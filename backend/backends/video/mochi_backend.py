"""Mochi-1 generation backend using diffusers."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Callable, Optional

import imageio
import torch

from .. import ModelConfig
from ...utils.platform_detect import get_device, get_vram_gb

logger = logging.getLogger(__name__)


class MochiBackend:
    """Mochi-1 video generation backend."""

    MODEL_CONFIGS = [
        ModelConfig(
            model_name="mochi-1-preview",
            display_name="Mochi-1 Preview (T2V)",
            engine="mochi",
            hf_repo_id="genmo/mochi-1-preview",
            model_size="default",
            size_mb=19100,
            pipeline_tag="text-to-video",
        )
    ]

    def __init__(self):
        self._pipe = None
        self._device = get_device()
        self._dtype = torch.bfloat16 if self._device == "cuda" else torch.float32

    async def load_model(self, model_size: str = "default") -> None:
        import asyncio
        await asyncio.to_thread(self._load_model_sync)

    def _load_model_sync(self) -> None:
        from diffusers import MochiPipeline
        from backend.backends.base import is_model_cached, model_load_progress

        repo = "genmo/mochi-1-preview"
        logger.info("Loading Mochi-1 from %s", repo)
        is_cached = is_model_cached(repo)

        with model_load_progress("mochi-1-preview", is_cached):
            self._pipe = MochiPipeline.from_pretrained(
                repo,
                torch_dtype=self._dtype,
            )
            self._apply_memory_optimizations()
            logger.info("Mochi-1 model loaded")

    def _apply_memory_optimizations(self) -> None:
        vram_gb = get_vram_gb()
        if vram_gb is not None and vram_gb < 24:
            logger.info("Mochi enabling model CPU offload")
            self._pipe.enable_model_cpu_offload()
            self._pipe.vae.enable_tiling()
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
        if self._pipe is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self._device).manual_seed(seed)

        callback_on_step_end = None
        if progress_callback is not None:
            def make_callback(pc):
                def on_step(pipeline, step_index, timestep, callback_kwargs):
                    pc(step_index + 1, num_inference_steps)
                    return callback_kwargs
                return on_step
            callback_on_step_end = make_callback(progress_callback)

        output = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt or "",
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
            callback_on_step_end=callback_on_step_end,
        )

        frames = output.frames[0]
        duration = num_frames / fps

        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)

        writer = imageio.get_writer(
            temp_path, fps=fps, codec="libx264", quality=8, pixelformat="yuv420p"
        )
        for frame in frames:
            writer.append_data(frame)
        writer.close()

        return temp_path, duration

    async def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        num_frames: int = 24,
        seed: Optional[int] = None,
    ) -> tuple[str, float]:
        raise NotImplementedError("Image-to-Video generation is not supported for Mochi-1")

    def unload_model(self) -> None:
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            torch.cuda.empty_cache()
            logger.info("Mochi-1 model unloaded")

    def is_loaded(self) -> bool:
        return self._pipe is not None
