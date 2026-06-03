"""Voiceover generation — reuses VideoGen TTS backends."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..database.models import Clip, VoiceProfile
from ..services.task_queue import create_background_task
from ..services.voiceover import run_voiceover_generation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voiceover", tags=["voiceover"])


@router.post("/generate", status_code=202)
async def generate_voiceover(
    body: models.VoiceoverGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate voiceover audio from text and add to timeline."""
    profile = db.query(VoiceProfile).filter(VoiceProfile.id == body.profile_id).first()
    if not profile:
        raise HTTPException(404, "Voice profile not found")

    engine = body.engine or profile.default_engine or "qwen"

    clip = Clip(
        project_id=body.project_id,
        track=1,
        start_time_ms=0,
        end_time_ms=5000,
        clip_type="voiceover",
        source_text=body.text,
        model=engine,
    )
    db.add(clip)
    db.commit()
    db.refresh(clip)

    task_id = clip.id
    create_background_task(
        run_voiceover_generation(task_id, clip.id, profile, engine, body, db.bind)
    )

    return models.VoiceoverGenerateResponse(clip_id=clip.id, task_id=task_id, status="queued")
