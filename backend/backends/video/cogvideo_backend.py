"""CogVideoX backend using diffusers.

Supports:
- CogVideoX-5B-I2V (image-to-video)
- CogVideoX-2B (text-to-video)

Memory strategy:
  VRAM < 8GB   -> error with minimum requirement message
  VRAM 8-12GB  -> sequential_cpu_offload, vae_slicing, max 24 frames
  VRAM 12-24GB -> model_cpu_offload, max 48 frames
  VRAM > 24GB  -> full GPU, max 128 frames
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


class CogVideoBackend:
    """CogVideoX video generation backend."""

    MODEL_CONFIGS = [
        ModelConfig(
            model_name="cogvideo-5b-i2v",
            display_name="CogVideoX 5B I2V",
            engine="cogvideo",
            hf_repo_id="THUDM/CogVideoX-5B-I2V",
            model_size="5B",
            size_mb=10000,
            pipeline_tag="image-to-video",
            supports_image_input=True,
        ),
        ModelConfig(
            model_name="cogvideo-2b-t2v",
            display_name="CogVideoX 2B T2V",
            engine="cogvideo-2b",
            hf_repo_id="THUDM/CogVideoX-2B",
            model_size="2B",
            size_mb=5000,
            pipeline_tag="text-to-video",
        ),
    ]

    def __init__(self):
        self._pipe = None
        self._model_size: Optional[str] = None
        self._device = get_device()
        self._dtype = torch.float16 if self._device == "cuda" else torch.bfloat16

    def _hf_repo_for_size(self, model_size: str) -> str:
        # Normalize model size and fallbacks (like "default" or engine IDs)
        if model_size in ("default", "cogvideo", "cogvideo-2b", "cogvideo-2b-t2v"):
            model_size = "2B"
        elif model_size in ("cogvideo-5b", "cogvideo-5b-i2v"):
            model_size = "5B"

        for cfg in self.MODEL_CONFIGS:
            if cfg.model_size == model_size or cfg.model_name == model_size or cfg.engine == model_size:
                return cfg.hf_repo_id
        raise ValueError(f"Unknown model size: {model_size}")

    def _apply_memory_optimizations(self) -> None:
        vram_gb = get_vram_gb()
        is_5b = self._model_size == "5B"

        if vram_gb is not None and vram_gb < 8:
            raise RuntimeError(
                f"Insufficient VRAM ({vram_gb:.1f} GB). "
                f"CogVideoX requires at least 8 GB VRAM. Use the CPU backend instead."
            )

        if is_5b:
            if vram_gb is not None and vram_gb < 12:
                logger.info("VRAM <12GB for 5B model: enabling sequential CPU offload and VAE tiling")
                self._pipe.enable_sequential_cpu_offload()
                self._pipe.vae.enable_tiling()
            elif vram_gb is not None and vram_gb < 20:
                logger.info("VRAM <20GB for 5B model: enabling model CPU offload")
                self._pipe.enable_model_cpu_offload()
            else:
                logger.info("VRAM >=20GB for 5B model: full GPU mode")
                self._pipe.to(self._device)
        else:  # 2B model
            if vram_gb is not None and vram_gb < 8:
                logger.info("VRAM <8GB for 2B model: enabling sequential CPU offload")
                self._pipe.enable_sequential_cpu_offload()
            elif vram_gb is not None and vram_gb < 12:
                logger.info("VRAM <12GB for 2B model: enabling model CPU offload")
                self._pipe.enable_model_cpu_offload()
            else:
                logger.info("VRAM >=12GB for 2B model: full GPU mode (no CPU offload)")
                self._pipe.to(self._device)

    def max_frames_for_vram(self) -> int:
        vram_gb = get_vram_gb()
        if vram_gb is None:
            return 48
        if vram_gb < 12:
            return 24
        if vram_gb < 24:
            return 48
        return 128

    async def load_model(self, model_size: str) -> None:
        import asyncio
        await asyncio.to_thread(self._load_model_sync, model_size)

    def _load_model_sync(self, model_size: str) -> None:
        from backend.backends.base import is_model_cached, model_load_progress

        resolved_size = "2B"
        if model_size in ("cogvideo-5b", "cogvideo-5b-i2v", "5B"):
            resolved_size = "5B"

        repo = self._hf_repo_for_size(model_size)
        logger.info("Loading CogVideoX from %s", repo)

        model_name = "cogvideo-2b-t2v" if resolved_size == "2B" else "cogvideo-5b-i2v"
        is_cached = is_model_cached(repo)

        with model_load_progress(model_name, is_cached):
            if resolved_size == "5B":
                from diffusers import CogVideoXImageToVideoPipeline
                self._pipe = CogVideoXImageToVideoPipeline.from_pretrained(
                    repo,
                    torch_dtype=self._dtype,
                    variant="bf16" if self._dtype == torch.bfloat16 else "fp16",
                )
            else:
                from diffusers import CogVideoXPipeline
                self._pipe = CogVideoXPipeline.from_pretrained(
                    repo,
                    torch_dtype=self._dtype,
                    variant="bf16" if self._dtype == torch.bfloat16 else "fp16",
                )
            self._apply_memory_optimizations()
            self._model_size = resolved_size
            logger.info("CogVideoX model loaded (size=%s, device=%s)", resolved_size, self._device)

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
            "Generating video: prompt='%s' frames=%d steps=%d guidance=%.1f seed=%s",
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

        logger.info("Video generated: %s (%.1fs, %d frames)", temp_path, duration, num_frames)
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

        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        logger.info("I2V generation from image: %s", image_path)

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
            temp_path, fps=8, codec="libx264", quality=8, pixelformat="yuv420p",
        )
        for frame in frames:
            writer.append_data(frame)
        writer.close()

        return temp_path, duration

    def unload_model(self) -> None:
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            self._model_size = None
            torch.cuda.empty_cache()
            logger.info("CogVideoX model unloaded")

    def is_loaded(self) -> bool:
        return self._pipe is not None
