"""Project business logic — shared helpers for the projects and clips routes."""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..database.models import Clip, Project, uuid7
from ..models import ClipResponse, ProjectResponse

logger = logging.getLogger(__name__)


def project_to_response(project: Project) -> ProjectResponse:
    """Convert a Project ORM object to a ProjectResponse schema."""
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        width=project.width,
        height=project.height,
        fps=project.fps,
        duration_seconds=project.duration_seconds,
        thumbnail_path=project.thumbnail_path,
        render_status=project.render_status,
        render_progress=project.render_progress,
        output_path=project.output_path,
        clip_count=len(project.clips) if project.clips else 0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def clip_to_response(clip: Clip) -> ClipResponse:
    """Convert a Clip ORM object to a ClipResponse schema."""
    return ClipResponse(
        id=clip.id,
        project_id=clip.project_id,
        track=clip.track,
        start_time_ms=clip.start_time_ms,
        end_time_ms=clip.end_time_ms,
        clip_type=clip.clip_type,
        source_path=clip.source_path,
        source_text=clip.source_text,
        model=clip.model,
        seed=clip.seed,
        volume=clip.volume,
        speed=clip.speed,
        fade_in_ms=clip.fade_in_ms,
        fade_out_ms=clip.fade_out_ms,
        effects_chain=clip.effects_chain,
        created_at=clip.created_at,
        updated_at=clip.updated_at,
    )


def ensure_project_exists(project_id: str, db: Session) -> None:
    """Raise 404 if the project doesn't exist or is soft-deleted."""
    exists = db.query(Project.id).filter(
        Project.id == project_id, Project.deleted_at.is_(None)
    ).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Project not found")


def get_active_project(project_id: str, db: Session) -> Project:
    """Fetch a non-deleted project or raise 404."""
    project = db.query(Project).filter(
        Project.id == project_id, Project.deleted_at.is_(None)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
