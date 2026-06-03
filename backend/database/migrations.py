"""Schema migrations for VideoGen Studio.

Idempotent column/table-level migrations run on every startup.
Fresh installs get tables via SQLAlchemy metadata.create_all();
this handles schema evolution for existing databases.
"""

import logging

from sqlalchemy import inspect, text

from .models import Base

logger = logging.getLogger(__name__)


def run_migrations(engine) -> None:
    """Run all schema migrations. Safe to call on every startup."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "projects" not in tables:
        logger.info("Fresh database — will create all VideoGen tables")
        return

    _migrate_projects(engine, inspector, tables)
    _migrate_clips(engine, inspector, tables)
    _migrate_renders(engine, inspector, tables)


def _get_columns(inspector, table: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table)}


def _add_column(engine, table: str, column_sql: str, label: str) -> None:
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))
        conn.commit()
    logger.info("Added %s column to %s", label, table)


def _migrate_projects(engine, inspector, tables: set[str]) -> None:
    if "projects" not in tables:
        return
    columns = _get_columns(inspector, "projects")
    if "render_status" not in columns:
        _add_column(engine, "projects", "render_status VARCHAR DEFAULT 'draft'", "render_status")
    if "render_progress" not in columns:
        _add_column(engine, "projects", "render_progress FLOAT DEFAULT 0.0", "render_progress")
    if "deleted_at" not in columns:
        _add_column(engine, "projects", "deleted_at DATETIME", "deleted_at (soft-delete)")


def _migrate_clips(engine, inspector, tables: set[str]) -> None:
    if "clips" not in tables:
        return
    columns = _get_columns(inspector, "clips")
    for col_name, col_def, label in [
        ("effects_chain", "effects_chain JSON", "effects_chain"),
        ("fade_in_ms", "fade_in_ms INTEGER DEFAULT 0", "fade_in_ms"),
        ("fade_out_ms", "fade_out_ms INTEGER DEFAULT 0", "fade_out_ms"),
    ]:
        if col_name not in columns:
            _add_column(engine, "clips", col_def, label)


def _migrate_renders(engine, inspector, tables: set[str]) -> None:
    if "renders" not in tables:
        return
    columns = _get_columns(inspector, "renders")
    if "file_size_bytes" not in columns:
        _add_column(engine, "renders", "file_size_bytes INTEGER", "file_size_bytes")
    if "resolution" not in columns:
        _add_column(engine, "renders", "resolution VARCHAR", "resolution")
