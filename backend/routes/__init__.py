"""Route registration for VideoGen Studio API.

Phase 1 enables only routes that work with the new schema.
Legacy route files remain on disk but are commented out;
they will be rewritten in later phases.
"""

from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    """Include all domain routers on the application."""
    from .projects import router as projects_router
    from .clips import router as clips_router
    from .health import router as health_router
    from .profiles import router as profiles_router
    from .channels import router as channels_router
    from .transcription import router as transcription_router
    from .llm import router as llm_router
    from .models import router as models_router
    from .settings import router as settings_router
    from .tasks import router as tasks_router
    from .cuda import router as cuda_router
    from .events import router as events_router
    from .generation import router as generation_router
    from .voiceover import router as voiceover_router
    from .subtitles import router as subtitles_router
    from .voice_profiles import router as voice_profiles_router
    from .render import router as render_router

    app.include_router(projects_router)
    app.include_router(clips_router)
    app.include_router(health_router)
    app.include_router(profiles_router)
    app.include_router(channels_router)
    app.include_router(transcription_router)
    app.include_router(llm_router)
    app.include_router(models_router)
    app.include_router(settings_router)
    app.include_router(tasks_router)
    app.include_router(cuda_router)
    app.include_router(events_router)
    app.include_router(generation_router)
    app.include_router(voiceover_router)
    app.include_router(subtitles_router)
    app.include_router(voice_profiles_router)
    app.include_router(render_router)

    # ── Disabled until rewritten for new schema ──────────────
    # from .generations import router as generations_router
    # from .history import router as history_router
    # from .captures import router as captures_router
    # from .stories import router as stories_router
    # from .effects import router as effects_router
    # from .audio import router as audio_router
    # from .speak import router as speak_router
    # from .mcp_bindings import router as mcp_bindings_router
