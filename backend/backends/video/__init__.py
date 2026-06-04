"""Video backend protocol and factory."""

import threading
from collections.abc import Callable
from typing import Optional, Protocol

from .. import ModelConfig


class VideoBackend(Protocol):
    MODEL_CONFIGS: list[ModelConfig]

    async def load_model(self, model_size: str) -> None: ...
    async def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        num_frames: int = 24,
        fps: int = 8,
        guidance_scale: float = 7.0,
        num_inference_steps: int = 50,
        seed: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> tuple[str, float]: ...
    async def generate_from_image(
        self, image_path: str, prompt: str, num_frames: int = 24,
        seed: int | None = None,
    ) -> tuple[str, float]: ...
    def unload_model(self) -> None: ...
    def is_loaded(self) -> bool: ...


_video_backends: dict[str, "VideoBackend"] = {}
_video_backends_lock = threading.Lock()


def get_video_backend(engine: str) -> VideoBackend:
    """Get or create a video backend for the given engine."""
    if engine in _video_backends:
        return _video_backends[engine]

    with _video_backends_lock:
        if engine in _video_backends:
            return _video_backends[engine]

        if engine == "cogvideo" or engine == "cogvideo-2b":
            from .cogvideo_backend import CogVideoBackend
            backend = CogVideoBackend()
        elif engine == "wan-t2v" or engine == "wan-i2v":
            from .wan_backend import WanBackend
            backend = WanBackend()
        elif engine == "ltx":
            from .ltx_backend import LTXVideoBackend
            backend = LTXVideoBackend()
        elif engine == "hunyuan":
            from .hunyuan_backend import HunyuanVideoBackend
            backend = HunyuanVideoBackend()
        elif engine == "mochi":
            from .mochi_backend import MochiBackend
            backend = MochiBackend()
        elif engine == "svd":
            from .svd_backend import StableVideoDiffusionBackend
            backend = StableVideoDiffusionBackend()
        else:
            raise ValueError(f"Unknown video engine: {engine}")

        _video_backends[engine] = backend
        return backend


def reset_video_backends():
    """Reset video backend instances (useful for testing)."""
    _video_backends.clear()
