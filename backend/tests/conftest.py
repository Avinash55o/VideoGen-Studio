"""Shared test fixtures for VideoGen Studio backend tests."""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base


TEST_DB_FD, TEST_DB_PATH = tempfile.mkstemp(suffix=".db")


@pytest.fixture(autouse=True)
def _test_db() -> Path:
    """Create a fresh in-memory SQLite database for each test.

    All tables are created before the test and dropped after.
    """
    
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from backend.database import init_db as _real_init
    _original_engine = None
    _original_session = None

    import backend.database.session as sess_mod
    _original_engine = sess_mod.engine
    _original_session = sess_mod.SessionLocal

    sess_mod.engine = engine
    sess_mod.SessionLocal = TestSession

    yield

    sess_mod.engine = _original_engine
    sess_mod.SessionLocal = _original_session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Yield a SQLAlchemy session within a transaction that rolls back."""
    from backend.database.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _test_data_dir(monkeypatch) -> Path:
    """Redirect config paths to a temp directory."""
    tmp = Path(tempfile.mkdtemp(prefix="videogen-test-"))
    monkeypatch.setattr("backend.config._data_dir", tmp)
    (tmp / "projects").mkdir(parents=True, exist_ok=True)
    (tmp / "renders").mkdir(parents=True, exist_ok=True)
    (tmp / "voice-profiles").mkdir(parents=True, exist_ok=True)
    return tmp


@pytest.fixture
def sample_project_data():
    return {
        "name": "Test Project",
        "description": "A project for testing",
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "duration_seconds": 10.0,
    }
