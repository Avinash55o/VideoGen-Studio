"""Stable Video Diffusion (SVD) generation backend using diffusers."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Callable, Optional

import imageio
import torch
from PIL import Image

from .. import ModelConfig
from ...utils.platform_detect import get_device, get_vram_gb

logger = logging.getLogger(__name__)


class StableVideoDiffusionBackend:
    """Stable Video Diffusion (SVD) generation backend."""

    MODEL_CONFIGS = [
        ModelConfig(
            model_name="svd-xt",
            display_name="Stable Video Diffusion XT",
            engine="svd",
            hf_repo_id="stabilityai/stable-video-diffusion-img2vid-xt",
            model_size="default",
            size_mb=9000,
            pipeline_tag="image-to-video",
            supports_image_input=True,
        )
    ]

    def __init__(self):
        self._pipe = None
        self._device = get_device()
        self._dtype = torch.float16 if self._device == "cuda" else torch.float32

    async def load_model(self, model_size: str = "default") -> None:
        import asyncio
        await asyncio.to_thread(self._load_model_sync)

    def _load_model_sync(self) -> None:
        from diffusers import StableVideoDiffusionPipeline
        from backend.backends.base import is_model_cached, model_load_progress

        repo = "stabilityai/stable-video-diffusion-img2vid-xt"
        logger.info("Loading Stable Video Diffusion from %s", repo)
        is_cached = is_model_cached(repo)

        with model_load_progress("svd-xt", is_cached):
            self._pipe = StableVideoDiffusionPipeline.from_pretrained(
                repo,
                torch_dtype=self._dtype,
                variant="fp16" if self._dtype == torch.float16 else None,
            )
            self._apply_memory_optimizations()
            logger.info("Stable Video Diffusion model loaded")

    def _apply_memory_optimizations(self) -> None:
        vram_gb = get_vram_gb()
        if vram_gb is not None and vram_gb < 16:
            logger.info("SVD enabling model CPU offload")
            self._pipe.enable_model_cpu_offload()
        else:
            self._pipe.to(self._device)

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: int = 24,
        fps: int = 8,
        guidance_scale: float = 7.0,
        num_inference_steps: int = 50,
        seed: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> tuple[str, float]:
        raise NotImplementedError("Text-to-Video generation is not supported for Stable Video Diffusion")

    async def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        num_frames: int = 24,
        seed: Optional[int] = None,
    ) -> tuple[str, float]:
        if self._pipe is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        image = Image.open(image_path).convert("RGB")
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self._device).manual_seed(seed)

        output = self._pipe(
            image=image,
            num_frames=num_frames,
            generator=generator,
        )

        frames = output.frames[0]
        duration = num_frames / 8

        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)

        writer = imageio.get_writer(
            temp_path, fps=8, codec="libx264", quality=8, pixelformat="yuv420p"
        )
        for frame in frames:
            writer.append_data(frame)
        writer.close()

        return temp_path, duration

    def unload_model(self) -> None:
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            torch.cuda.empty_cache()
            logger.info("SVD model unloaded")

    def is_loaded(self) -> bool:
        return self._pipe is not None
