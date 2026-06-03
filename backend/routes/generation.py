"""Video generation endpoints."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..database.models import Clip, Project
from ..services.task_queue import create_background_task
from ..services.video import run_video_generation
from ..utils.progress import get_progress_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate", tags=["generation"])


@router.post("/video", response_model=models.VideoGenerationResponse, status_code=202)
async def generate_video(
    body: models.VideoGenerationRequest,
    db: Session = Depends(get_db),
):
    """Start a video generation task. Returns immediately with a task_id."""
    project = db.query(Project).filter(
        Project.id == body.project_id, Project.deleted_at.is_(None)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    clip = Clip(
        project_id=body.project_id,
        track=0,
        start_time_ms=0,
        end_time_ms=int(body.num_frames / 8 * 1000),
        clip_type="video",
        source_text=body.prompt,
        model=body.model,
        seed=body.seed,
    )
    db.add(clip)
    db.commit()
    db.refresh(clip)

    task_id = clip.id
    create_background_task(
        run_video_generation(
            task_id=task_id,
            project_id=body.project_id,
            clip_id=clip.id,
            model=body.model,
            prompt=body.prompt,
            negative_prompt=body.negative_prompt,
            num_frames=body.num_frames,
            guidance_scale=body.guidance_scale,
            num_inference_steps=body.num_inference_steps,
            seed=body.seed,
            image_path=body.image_path,
            db_bind=db.bind,
        )
    )

    return models.VideoGenerationResponse(
        task_id=task_id,
        status="queued",
    )


@router.get("/progress/{task_id}")
async def get_generation_progress(task_id: str):
    """SSE stream for generation progress."""
    progress_manager = get_progress_manager()

    async def event_generator():
        async for event in progress_manager.subscribe(task_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
