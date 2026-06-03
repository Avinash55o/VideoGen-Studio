"""Render pipeline endpoints — compose project clips into final video."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..database.models import Project
from ..services.project import get_active_project
from ..services.render import RenderError, render_project
from ..services.task_queue import create_background_task
from ..utils.ffmpeg import is_ffmpeg_available

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/render", tags=["render"])


@router.post("", response_model=models.RenderResponse, status_code=202)
async def start_render(
    project_id: str,
    body: models.RenderRequest = models.RenderRequest(),
    db: Session = Depends(get_db),
):
    """Start a background render of the project."""
    if not is_ffmpeg_available():
        raise HTTPException(status_code=400, detail="ffmpeg is not installed — render pipeline unavailable")

    project = get_active_project(project_id, db)
    if not project:
        raise HTTPException(404, "Project not found")

    db_bind = db.bind
    create_background_task(
        _run_render_task(project_id, db_bind, body.format, body.resolution)
    )

    return models.RenderResponse(
        id=project_id,
        project_id=project_id,
        status="queued",
        progress=0.0,
    )


async def _run_render_task(project_id: str, db_bind, fmt: str, resolution: str | None):
    """Background task wrapper for rendering."""
    try:
        await render_project(project_id, db_bind, format=fmt, resolution=resolution)
    except RenderError as e:
        logger.error("Render failed for project %s: %s", project_id, e)


@router.get("/status", response_model=models.RenderResponse)
async def get_render_status(project_id: str, db: Session = Depends(get_db)):
    """Poll render progress."""
    project = get_active_project(project_id, db)
    if not project:
        raise HTTPException(404, "Project not found")

    return models.RenderResponse(
        id=project_id,
        project_id=project_id,
        status=project.render_status,
        progress=project.render_progress,
    )


@router.get("/download")
async def download_render(project_id: str, db: Session = Depends(get_db)):
    """Download the latest completed render for this project."""
    project = get_active_project(project_id, db)
    if not project:
        raise HTTPException(404, "Project not found")

    if project.render_status != "complete" or not project.output_path:
        raise HTTPException(400, detail="Render not yet complete")

    output = Path(project.output_path)
    if not output.exists():
        raise HTTPException(404, detail="Render file not found on disk")

    return FileResponse(
        output,
        media_type="video/mp4",
        filename=f"{project.name}.mp4",
    )
