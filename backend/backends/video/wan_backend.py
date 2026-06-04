"""Wan2.1 video generation backend using diffusers.

Supports:
- Wan2.1-T2V-1.3B (text-to-video)
- Wan2.1-I2V-14B (image-to-video, optional future)

Memory strategy:
  VRAM < 4GB   -> error with minimum requirement message
  VRAM 4-8GB   -> sequential_cpu_offload, max 24 frames
  VRAM 8-16GB  -> model_cpu_offload, max 48 frames
  VRAM > 16GB  -> full GPU, max 128 frames
"""

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


class WanBackend:
    """Wan2.1 video generation backend."""

    MODEL_CONFIGS = [
        ModelConfig(
            model_name="wan-t2v-1.3b",
            display_name="Wan2.1 T2V 1.3B",
            engine="wan-t2v",
            hf_repo_id="Wan-AI/Wan2.1-T2V-1.3B",
            model_size="1.3B",
            size_mb=3000,
            pipeline_tag="text-to-video",
        ),
        ModelConfig(
            model_name="wan-i2v-14b",
            display_name="Wan2.1 I2V 14B (480P)",
            engine="wan-i2v",
            hf_repo_id="Wan-AI/Wan2.1-I2V-14B-480P",
            model_size="14B",
            size_mb=28000,
            pipeline_tag="image-to-video",
            supports_image_input=True,
            languages=["en", "zh"],
        ),
    ]

    def __init__(self):
        self._pipe = None
        self._model_size: Optional[str] = None
        self._device = get_device()
        self._dtype = torch.bfloat16

    async def load_model(self, model_size: str) -> None:
        import asyncio
        await asyncio.to_thread(self._load_model_sync, model_size)

    def _load_model_sync(self, model_size: str) -> None:
        from backend.backends.base import is_model_cached, model_load_progress

        resolved_size = "1.3B"
        if model_size in ("wan-i2v", "wan-i2v-14b", "14B"):
            resolved_size = "14B"

        repo = "Wan-AI/Wan2.1-I2V-14B-480P" if resolved_size == "14B" else "Wan-AI/Wan2.1-T2V-1.3B"
        logger.info("Loading Wan2.1 from %s", repo)

        model_name = "wan-i2v-14b" if resolved_size == "14B" else "wan-t2v-1.3b"
        is_cached = is_model_cached(repo)

        with model_load_progress(model_name, is_cached):
            if resolved_size == "14B":
                from diffusers import WanImageToVideoPipeline
                self._pipe = WanImageToVideoPipeline.from_pretrained(
                    repo,
                    torch_dtype=self._dtype,
                )
            else:
                from diffusers import WanPipeline
                self._pipe = WanPipeline.from_pretrained(
                    repo,
                    torch_dtype=self._dtype,
                )
            self._model_size = resolved_size
            self._apply_memory_optimizations()
            logger.info("Wan2.1 model loaded (size=%s, device=%s)", resolved_size, self._device)

    def _apply_memory_optimizations(self) -> None:
        vram_gb = get_vram_gb()
        is_14b = self._model_size == "14B"

        min_required = 16 if is_14b else 4
        if vram_gb is not None and vram_gb < min_required:
            raise RuntimeError(
                f"Insufficient VRAM ({vram_gb:.1f} GB). "
                f"{'Wan2.1 14B' if is_14b else 'Wan2.1 1.3B'} requires at least {min_required} GB VRAM."
            )

        if is_14b:
            if vram_gb is not None and vram_gb < 24:
                logger.info("VRAM <24GB for 14B model: enabling sequential CPU offload")
                self._pipe.enable_sequential_cpu_offload()
            else:
                logger.info("VRAM >=24GB for 14B model: enabling model CPU offload")
                self._pipe.enable_model_cpu_offload()
        else:
            if vram_gb is not None and vram_gb < 8:
                logger.info("VRAM <8GB: enabling sequential CPU offload")
                self._pipe.enable_sequential_cpu_offload()
            elif vram_gb is not None and vram_gb < 16:
                logger.info("VRAM <16GB: enabling model CPU offload")
                self._pipe.enable_model_cpu_offload()
            else:
                logger.info("VRAM >=16GB: full GPU mode")
                self._pipe.to(self._device)

    def max_frames_for_vram(self) -> int:
        vram_gb = get_vram_gb()
        if vram_gb is None:
            return 48
        if vram_gb < 8:
            return 24
        if vram_gb < 16:
            return 48
        return 128

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

        max_frames = self.max_frames_for_vram()
        if num_frames > max_frames:
            logger.warning("Clamping num_frames from %d to %d (VRAM limit)", num_frames, max_frames)
            num_frames = max_frames

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

        logger.info(
            "Generating Wan2.1 video: prompt='%s' frames=%d steps=%d guidance=%.1f seed=%s",
            prompt[:80], num_frames, num_inference_steps, guidance_scale,
            seed if seed is not None else "random",
        )

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
            temp_path,
            fps=fps,
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
        )
        for frame in frames:
            writer.append_data(frame)
        writer.close()

        logger.info("Wan2.1 video generated: %s (%.1fs, %d frames)", temp_path, duration, num_frames)
        return temp_path, duration

    async def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        num_frames: int = 24,
        seed: Optional[int] = None,
    ) -> tuple[str, float]:
        if self._pipe is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        if self._model_size != "14B":
            raise RuntimeError("Image-to-Video generation is only supported with the 14B model size")

        from PIL import Image
        image = Image.open(image_path).convert("RGB")
        logger.info("Wan2.1 I2V generation from image: %s", image_path)

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self._device).manual_seed(seed)

        output = self._pipe(
            prompt=prompt,
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

        logger.info("Wan2.1 I2V video generated: %s (%.1fs, %d frames)", temp_path, duration, num_frames)
        return temp_path, duration

    def unload_model(self) -> None:
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            self._model_size = None
            torch.cuda.empty_cache()
            logger.info("Wan2.1 model unloaded")

    def is_loaded(self) -> bool:
        return self._pipe is not None
