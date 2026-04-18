from .video_audio_muxer_node import VideoAudioMuxerNode

NODE_CLASS_MAPPINGS = {
    "VideoAudioMuxer": VideoAudioMuxerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoAudioMuxer": "Video Audio Muxer Node",
}

__all__ = [
    "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"
]
