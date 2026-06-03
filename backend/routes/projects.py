"""Project CRUD endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..database.models import Project
from ..models import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectUpdate
from ..services.project import get_active_project, project_to_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort: str = Query("-updated_at", pattern=r"^-?(updated_at|created_at|name)$"),
    search: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
):
    """List all non-deleted projects with pagination and search."""
    query = db.query(Project).filter(Project.deleted_at.is_(None))

    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    total = query.count()

    direction = desc if sort.startswith("-") else asc
    sort_col = getattr(Project, sort.lstrip("-"))
    query = query.order_by(direction(sort_col))

    projects = query.offset(offset).limit(limit).all()
    return ProjectListResponse(
        items=[project_to_response(p) for p in projects],
        total=total,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new project."""
    project = Project(
        name=body.name,
        description=body.description,
        width=body.width,
        height=body.height,
        fps=body.fps,
        duration_seconds=body.duration_seconds,
    )
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A project with this name already exists")
    db.refresh(project)
    logger.info("Created project %s (%s)", project.id, project.name)
    return project_to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a single project by ID."""
    project = get_active_project(project_id, db)
    return project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """Update project metadata."""
    project = get_active_project(project_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A project with this name already exists")
    db.refresh(project)
    return project_to_response(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Soft-delete a project."""
    project = get_active_project(project_id, db)
    project.deleted_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("Soft-deleted project %s", project_id)
