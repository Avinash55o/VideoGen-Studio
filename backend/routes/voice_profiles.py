"""Slimmed voice profile CRUD for video narration.

Drops from the original VideoGen profiles route:
- personality field (not needed for video narration)
- effects_chain (applied at clip level)
- avatar_path (not needed)
- compose endpoint (personality rewrite)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import VoiceProfile as DBVoiceProfile, get_db
from ..database.models import VoiceSample

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-profiles", tags=["voice_profiles"])


def _profile_to_response(profile: DBVoiceProfile) -> models.VoiceProfileResponse:
    sample_count = len(profile.samples) if hasattr(profile, "samples") and profile.samples else 0
    return models.VoiceProfileResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        voice_type=profile.voice_type,
        preset_engine=profile.preset_engine,
        preset_voice_id=profile.preset_voice_id,
        design_prompt=profile.design_prompt,
        default_engine=profile.default_engine,
        language=profile.language,
        sample_count=sample_count,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("", response_model=list[models.VoiceProfileResponse])
async def list_voice_profiles(db: Session = Depends(get_db)):
    profiles = db.query(DBVoiceProfile).order_by(DBVoiceProfile.name).all()
    return [_profile_to_response(p) for p in profiles]


@router.get("/{profile_id}", response_model=models.VoiceProfileResponse)
async def get_voice_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(DBVoiceProfile).filter(DBVoiceProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Voice profile not found")
    return _profile_to_response(profile)


@router.post("", response_model=models.VoiceProfileResponse, status_code=201)
async def create_voice_profile(body: models.VoiceProfileCreate, db: Session = Depends(get_db)):
    existing = db.query(DBVoiceProfile).filter(DBVoiceProfile.name == body.name).first()
    if existing:
        raise HTTPException(409, "Profile with this name already exists")

    profile = DBVoiceProfile(
        name=body.name,
        description=body.description,
        voice_type=body.voice_type,
        preset_engine=body.preset_engine,
        preset_voice_id=body.preset_voice_id,
        design_prompt=body.design_prompt,
        default_engine=body.default_engine,
        language=body.language,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


@router.put("/{profile_id}", response_model=models.VoiceProfileResponse)
async def update_voice_profile(
    profile_id: str,
    body: models.VoiceProfileUpdate,
    db: Session = Depends(get_db),
):
    profile = db.query(DBVoiceProfile).filter(DBVoiceProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Voice profile not found")

    if body.name is not None:
        profile.name = body.name
    if body.description is not None:
        profile.description = body.description
    if body.language is not None:
        profile.language = body.language
    if body.default_engine is not None:
        profile.default_engine = body.default_engine

    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_voice_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(DBVoiceProfile).filter(DBVoiceProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Voice profile not found")
    db.delete(profile)
    db.commit()
