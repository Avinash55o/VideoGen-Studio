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

    model_name = body.model
    image_path = body.image_path
    start_time_ms = 0
    track = 0

    if body.parent_clip_id:
        parent_clip = db.query(Clip).filter(
            Clip.id == body.parent_clip_id,
            Clip.project_id == body.project_id
        ).first()
        if not parent_clip:
            raise HTTPException(status_code=404, detail="Parent clip not found")
        if not parent_clip.source_path:
            raise HTTPException(status_code=400, detail="Parent clip has no video file generated yet")

        from ..config import resolve_storage_path, to_storage_path, get_projects_dir
        parent_video_path = resolve_storage_path(parent_clip.source_path)
        if not parent_video_path or not parent_video_path.exists():
            raise HTTPException(status_code=400, detail="Parent video file not found on disk")

        project_dir = get_projects_dir() / body.project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        extracted_frame_path = project_dir / f"frame_last_{parent_clip.id}.png"

        from ..utils.video_processing import extract_last_frame
        success = extract_last_frame(str(parent_video_path), str(extracted_frame_path))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to extract final frame from parent clip")

        image_path = to_storage_path(extracted_frame_path)
        start_time_ms = parent_clip.end_time_ms
        track = parent_clip.track

    if image_path:
        # Auto-upgrade text-to-video CogVideo request to image-to-video variant
        if model_name in ("cogvideo-2b", "cogvideo-2b-t2v", "cogvideo"):
            model_name = "cogvideo-5b-i2v"
        elif model_name not in ("cogvideo-5b-i2v", "ltx-video", "wan-i2v"):
            raise HTTPException(
                status_code=400,
                detail=f"Image-to-Video generation is not supported for model: {body.model}. Please use a CogVideo model for chained generation."
            )

    clip = Clip(
        project_id=body.project_id,
        track=track,
        start_time_ms=start_time_ms,
        end_time_ms=start_time_ms + int(body.num_frames / 8 * 1000),
        clip_type="video",
        source_text=body.prompt,
        model=model_name,
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
            model=model_name,
            prompt=body.prompt,
            negative_prompt=body.negative_prompt,
            num_frames=body.num_frames,
            guidance_scale=body.guidance_scale,
            num_inference_steps=body.num_inference_steps,
            seed=body.seed,
            image_path=image_path,
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
