"""TTS voiceover orchestration for timeline clips."""

import asyncio
import logging
from pathlib import Path

from ..database.models import Clip

logger = logging.getLogger(__name__)


async def _write_audio(wav_path: str, audio_array, sample_rate: int):
    import soundfile as sf
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, sf.write, wav_path, audio_array, sample_rate)


async def run_voiceover_generation(task_id: str, clip_id: str, profile, engine: str, body, db_bind):
    """Background: generate TTS audio, update clip duration."""
    from ..backends import get_tts_backend_for_engine
    from ..services.profiles import create_voice_prompt_for_profile
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SASession

    try:
        backend = get_tts_backend_for_engine(engine)
        if not backend.is_loaded():
            await backend.load_model()

        engine_ = create_engine(db_bind.url)
        with SASession(bind=engine_) as db:
            voice_prompt = await create_voice_prompt_for_profile(profile.id, db, engine=engine)

        audio_array, sample_rate = await backend.generate(
            text=body.text,
            voice_prompt=voice_prompt,
            language=body.language,
        )

        with SASession(bind=engine_) as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                return

            clips_dir = Path("data") / "projects" / clip.project_id / "clips"
            clips_dir.mkdir(parents=True, exist_ok=True)
            wav_path = str(clips_dir / f"{clip_id}.wav")

            await _write_audio(wav_path, audio_array, sample_rate)

            duration = len(audio_array) / sample_rate
            clip.source_path = f"data/projects/{clip.project_id}/clips/{clip_id}.wav"
            clip.end_time_ms = int(duration * 1000)
            db.commit()

    except Exception:
        logger.exception("Voiceover generation failed")
        engine_ = create_engine(db_bind.url)
        with SASession(bind=engine_) as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if clip:
                clip.end_time_ms = 2000
                db.commit()
