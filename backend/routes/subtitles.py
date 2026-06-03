"""Subtitle generation and editing — reuses Whisper STT."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..database.models import SubtitleTrack
from ..services.subtitle import _subtitle_track_to_response, generate_subtitle_track

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subtitles", tags=["subtitles"])


@router.post("/generate", response_model=models.SubtitleTrackResponse)
async def generate_subtitles(
    body: models.SubtitleGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate subtitle track from voiceover clip audio using Whisper."""
    try:
        return await generate_subtitle_track(
            clip_id=body.clip_id,
            language=body.language,
            stt_model=body.stt_model,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{track_id}", response_model=models.SubtitleTrackResponse)
async def update_subtitle_track(
    track_id: str,
    body: models.SubtitleTrackUpdate,
    db: Session = Depends(get_db),
):
    """Update subtitle items (manual editing) or style."""
    track = db.query(SubtitleTrack).filter(SubtitleTrack.id == track_id).first()
    if not track:
        raise HTTPException(404, "Subtitle track not found")

    if body.items is not None:
        track.items = [item.model_dump() for item in body.items]
    if body.style is not None:
        track.style = body.style

    db.commit()
    db.refresh(track)
    return _subtitle_track_to_response(track)
