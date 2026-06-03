"""Video generation orchestration service."""

import logging
import shutil
from pathlib import Path

from ..database.models import Clip, Project
from ..backends.video import get_video_backend
from ..utils.progress import get_progress_manager

logger = logging.getLogger(__name__)


def get_video_model_configs():
    """Return model configs for all video backends."""
    configs = []
    from ..backends.video.cogvideo_backend import CogVideoBackend
    from ..backends.video.wan_backend import WanBackend
    configs.extend(CogVideoBackend.MODEL_CONFIGS)
    configs.extend(WanBackend.MODEL_CONFIGS)
    return configs


async def run_video_generation(
    task_id: str,
    project_id: str,
    clip_id: str,
    model: str,
    prompt: str,
    negative_prompt: str | None,
    num_frames: int,
    guidance_scale: float,
    num_inference_steps: int,
    seed: int | None,
    image_path: str | None,
    db_bind,
):
    """Background task: run video generation and update clip."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SASession

    progress = get_progress_manager()
    engine = create_engine(db_bind.url)

    try:
        backend = get_video_backend(model)

        if not backend.is_loaded():
            await backend.load_model("default")

        async def progress_callback(current: int, total: int):
            progress.update_progress(
                task_id, current, total, filename="Generating frames...",
                status="generating",
            )

        if image_path:
            video_path, duration = await backend.generate_from_image(
                image_path=image_path,
                prompt=prompt,
                num_frames=num_frames,
                seed=seed,
            )
        else:
            video_path, duration = await backend.generate(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_frames=num_frames,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                seed=seed,
                progress_callback=progress_callback,
            )

        clips_dir = Path("data") / "projects" / project_id / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)

        final_path = clips_dir / f"{clip_id}.mp4"
        shutil.move(video_path, str(final_path))

        with SASession(bind=engine) as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if clip:
                clip.source_path = f"data/projects/{project_id}/clips/{clip_id}.mp4"
                clip.end_time_ms = int(duration * 1000)
                clip.model = model
                clip.seed = seed
                db.commit()

        progress.mark_complete(task_id)

    except Exception as e:
        logger.exception("Video generation failed")
        progress.mark_error(task_id, str(e))
        with SASession(bind=engine) as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if clip:
                clip.end_time_ms = 2000
                db.commit()
