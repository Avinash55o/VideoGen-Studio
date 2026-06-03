"""Clip CRUD and timeline batch operations."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..database.models import Clip
from ..models import ClipCreate, ClipResponse, ClipUpdate, TimelineBatchUpdate
from ..services.project import clip_to_response, ensure_project_exists

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects/{project_id}/clips", tags=["clips"])


@router.get("", response_model=list[ClipResponse])
async def list_clips(project_id: str, db: Session = Depends(get_db)):
    """List all clips for a project, sorted by track then start_time_ms."""
    ensure_project_exists(project_id, db)
    clips = (
        db.query(Clip)
        .filter(Clip.project_id == project_id)
        .order_by(Clip.track, Clip.start_time_ms)
        .all()
    )
    return [clip_to_response(c) for c in clips]


@router.post("", response_model=ClipResponse, status_code=201)
async def create_clip(
    project_id: str,
    body: ClipCreate,
    db: Session = Depends(get_db),
):
    """Add a clip to the project timeline."""
    ensure_project_exists(project_id, db)
    clip = Clip(project_id=project_id, **body.model_dump())
    db.add(clip)
    db.commit()
    db.refresh(clip)
    logger.info("Created clip %s on project %s track %d", clip.id, project_id, clip.track)
    return clip_to_response(clip)


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(
    project_id: str,
    clip_id: str,
    db: Session = Depends(get_db),
):
    """Get a single clip by ID."""
    ensure_project_exists(project_id, db)
    clip = db.query(Clip).filter(Clip.id == clip_id, Clip.project_id == project_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip_to_response(clip)


@router.put("/{clip_id}", response_model=ClipResponse)
async def update_clip(
    project_id: str,
    clip_id: str,
    body: ClipUpdate,
    db: Session = Depends(get_db),
):
    """Update a clip's properties."""
    clip = db.query(Clip).filter(Clip.id == clip_id, Clip.project_id == project_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(clip, key, value)

    db.commit()
    db.refresh(clip)
    return clip_to_response(clip)


@router.delete("/{clip_id}", status_code=204)
async def delete_clip(
    project_id: str,
    clip_id: str,
    db: Session = Depends(get_db),
):
    """Remove a clip from the timeline."""
    clip = db.query(Clip).filter(Clip.id == clip_id, Clip.project_id == project_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    db.delete(clip)
    db.commit()
    logger.info("Deleted clip %s from project %s", clip_id, project_id)


@router.put("/timeline/batch", status_code=204)
async def batch_update_timeline(
    project_id: str,
    body: TimelineBatchUpdate,
    db: Session = Depends(get_db),
):
    """Atomically update positions of multiple clips. Used by timeline drag-and-drop."""
    ensure_project_exists(project_id, db)

    clip_ids = {c.clip_id for c in body.clips}
    existing = (
        db.query(Clip)
        .filter(Clip.project_id == project_id, Clip.id.in_(clip_ids))
        .all()
    )
    existing_map = {c.id: c for c in existing}

    if len(existing_map) != len(clip_ids):
        missing = clip_ids - set(existing_map.keys())
        raise HTTPException(status_code=404, detail=f"Clips not found: {missing}")

    for pos in body.clips:
        clip = existing_map[pos.clip_id]
        clip.track = pos.track
        clip.start_time_ms = pos.start_time_ms
        logger.debug("Moved clip %s to track %d @ %dms", clip.id, pos.track, pos.start_time_ms)

    db.commit()


@router.get("/{clip_id}/audio")
async def get_clip_audio(project_id: str, clip_id: str, db: Session = Depends(get_db)):
    """Serve the audio/video file associated with a clip."""
    from pathlib import Path
    from fastapi.responses import FileResponse, Response
    import mimetypes

    ensure_project_exists(project_id, db)
    clip = db.query(Clip).filter(Clip.id == clip_id, Clip.project_id == project_id).first()
    if not clip or not clip.source_path:
        raise HTTPException(status_code=404, detail="Clip audio not found")

    audio_path = Path(clip.source_path)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    media_type, _ = mimetypes.guess_type(audio_path.name)
    return FileResponse(
        audio_path,
        media_type=media_type or "audio/wav",
        filename=audio_path.name,
    )
