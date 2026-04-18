from typing_extensions import override

import torch

from comfy_api.latest import ComfyExtension, io
from comfy_api.latest._input_impl.video_types import VideoFromComponents


class VideoAudioMuxerNode(io.ComfyNode):
    """
    動画ファイル（映像のみ）と音声ファイルを結合（Mux）して、
    音声付きの動画ファイルを生成するノード。
    vcodec='copy' を使い、映像の再エンコードを行わないため高速です。
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        """
            Return a schema which contains all information about the node.
            Some types: "Model", "Vae", "Clip", "Conditioning", "Latent", "Image", "Int", "String", "Float", "Combo".
            For outputs the "io.Model.Output" should be used, for inputs the "io.Model.Input" can be used.
            The type can be a "Combo" - this will be a list for selection.
        """
        return io.Schema(
            node_id="VideoAudioMuxer",
            display_name="Video Audio Muxer Node",
            category="image/video",
            inputs=[
                io.Video.Input("video"),
                io.Audio.Input("audio")
            ],
            outputs=[
                io.Video.Output(),
            ],
        )

    @classmethod
    def check_lazy_status(cls, video, audio):
        """
            Return a list of input names that need to be evaluated.

            This function will be called if there are any lazy inputs which have not yet been
            evaluated. As long as you return at least one field which has not yet been evaluated
            (and more exist), this function will be called again once the value of the requested
            field is available.

            Any evaluated inputs will be passed as arguments to this function. Any unevaluated
            inputs will have the value None.
        """
        return []

    @classmethod
    def execute(cls, video, audio) -> io.NodeOutput:
        video_components = video.get_components()
        waveform = audio["waveform"]  # [B, C, T]
        sample_rate = audio["sample_rate"]

        # --- 動画と音声の長さを秒単位で計算 ---
        num_frames = video_components.images.shape[0]
        video_duration = float(num_frames / video_components.frame_rate)

        target_samples = int(video_duration * sample_rate)

        # --- 長さ調整 ---
        current_samples = waveform.shape[-1]

        if current_samples > target_samples:
            # 音声が長い → 後半をカット
            waveform = waveform[..., :target_samples]
        elif current_samples < target_samples:
            # 音声が短い → 無音で埋める
            pad_size = target_samples - current_samples
            pad = torch.zeros((*waveform.shape[:-1], pad_size), dtype=waveform.dtype, device=waveform.device)
            waveform = torch.cat([waveform, pad], dim=-1)

        video_components.audio = {
            "waveform": waveform,
            "sample_rate": sample_rate
        }
        result_video = VideoFromComponents(video_components)

        return io.NodeOutput(result_video)

# Set the web directory, any .js file in that directory will be loaded by the frontend as a frontend extension
# WEB_DIRECTORY = "./somejs"


# Add custom API routes, using router
from aiohttp import web
from server import PromptServer

@PromptServer.instance.routes.get("/VideoAudioMuxerNode")
async def get_video_audio_muxer_node(request):
    return web.json_response("VideoAudioMuxerNode")


class VideoAudioMuxerNodeExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            VideoAudioMuxerNode,
        ]


async def comfy_entrypoint() -> VideoAudioMuxerNodeExtension:  # ComfyUI calls this to load your extension and its nodes.
    return VideoAudioMuxerNodeExtension()
