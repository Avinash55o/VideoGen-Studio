"""Whisper STT subtitle generation for timeline clips."""

import logging
from pathlib import Path

from .. import models
from ..database.models import Clip, SubtitleTrack

logger = logging.getLogger(__name__)


def _subtitle_track_to_response(track: SubtitleTrack) -> models.SubtitleTrackResponse:
    return models.SubtitleTrackResponse(
        id=track.id,
        project_id=track.project_id,
        clip_id=track.clip_id,
        language=track.language,
        items=[models.SubtitleItem(**item) for item in (track.items or [])],
        style=track.style,
        created_at=track.created_at,
        updated_at=track.updated_at,
    )


async def generate_subtitle_track(clip_id: str, language: str | None, stt_model: str | None, db):
    """Generate subtitle track from voiceover clip audio using Whisper."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise ValueError("Clip not found")
    if not clip.source_path:
        raise ValueError("Clip has no audio source — generate voiceover first")

    audio_path = Path(clip.source_path)
    if not audio_path.exists():
        raise ValueError("Audio file not found on disk")

    from ..services.transcribe import get_whisper_model
    whisper = get_whisper_model()
    if not whisper.is_loaded():
        await whisper.load_model(stt_model or "turbo")

    result = whisper.transcribe(str(audio_path), language=language, word_timestamps=True)

    items = []
    for segment in result.segments:
        items.append(models.SubtitleItem(
            start_ms=int(segment.start * 1000),
            end_ms=int(segment.end * 1000),
            text=segment.text.strip(),
        ))

    track = db.query(SubtitleTrack).filter(
        SubtitleTrack.project_id == clip.project_id,
        SubtitleTrack.clip_id == clip.id,
    ).first()

    if track:
        track.items = [item.model_dump() for item in items]
    else:
        track = SubtitleTrack(
            project_id=clip.project_id,
            clip_id=clip.id,
            language=language or "en",
            items=[item.model_dump() for item in items],
        )
        db.add(track)

    db.commit()
    db.refresh(track)
    return _subtitle_track_to_response(track)
