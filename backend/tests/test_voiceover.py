"""Tests for voiceover generation endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.database.models import Clip, Project, VoiceProfile


@pytest.fixture
def test_client(db_session):
    app = create_app()
    from backend.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_profile(db_session):
    profile = VoiceProfile(
        name="Test Voice",
        voice_type="preset",
        preset_engine="qwen",
        preset_voice_id="default",
        default_engine="qwen",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def sample_project(db_session):
    project = Project(name="Test Project", width=1920, height=1080, fps=24, duration_seconds=10.0)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestVoiceoverEndpointErrorHandling:
    def test_generate_voiceover_missing_project_id(self, test_client, sample_profile):
        response = test_client.post(
            "/api/voiceover/generate",
            json={
                "profile_id": sample_profile.id,
                "text": "Hello world",
            },
        )
        assert response.status_code == 422

    def test_generate_voiceover_profile_not_found(self, test_client, sample_project):
        response = test_client.post(
            "/api/voiceover/generate",
            json={
                "project_id": sample_project.id,
                "profile_id": "nonexistent",
                "text": "Hello world",
            },
        )
        assert response.status_code == 404
        assert "Voice profile not found" in response.json()["detail"]

    def test_generate_voiceover_empty_text(self, test_client, sample_project, sample_profile):
        response = test_client.post(
            "/api/voiceover/generate",
            json={
                "project_id": sample_project.id,
                "profile_id": sample_profile.id,
                "text": "",
            },
        )
        assert response.status_code == 422


class TestVoiceoverEndpointSuccess:
    @patch("backend.routes.voiceover.run_voiceover_generation", new_callable=AsyncMock)
    def test_generate_voiceover_creates_clip(self, mock_run, test_client, sample_project, sample_profile, db_session):
        response = test_client.post(
            "/api/voiceover/generate",
            json={
                "project_id": sample_project.id,
                "profile_id": sample_profile.id,
                "text": "Welcome to my video about space",
                "language": "en",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert "clip_id" in data
        assert "task_id" in data

        clip = db_session.query(Clip).filter(Clip.id == data["clip_id"]).first()
        assert clip is not None
        assert clip.project_id == sample_project.id
        assert clip.track == 1
        assert clip.clip_type == "voiceover"
        assert clip.source_text == "Welcome to my video about space"
        assert clip.model == "qwen"

    @patch("backend.routes.voiceover.run_voiceover_generation", new_callable=AsyncMock)
    def test_generate_voiceover_with_custom_engine(self, mock_run, test_client, sample_project, sample_profile, db_session):
        response = test_client.post(
            "/api/voiceover/generate",
            json={
                "project_id": sample_project.id,
                "profile_id": sample_profile.id,
                "text": "Hello",
                "engine": "kokoro",
            },
        )
        assert response.status_code == 202
        data = response.json()
        clip = db_session.query(Clip).filter(Clip.id == data["clip_id"]).first()
        assert clip.model == "kokoro"

    @patch("backend.routes.voiceover.run_voiceover_generation", new_callable=AsyncMock)
    def test_generate_voiceover_uses_profile_default_engine(self, mock_run, test_client, sample_project, db_session):
        profile = VoiceProfile(
            name="Custom Engine Profile",
            voice_type="preset",
            preset_engine="luxtts",
            preset_voice_id="default",
            default_engine="luxtts",
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)

        response = test_client.post(
            "/api/voiceover/generate",
            json={
                "project_id": sample_project.id,
                "profile_id": profile.id,
                "text": "Hello",
            },
        )
        assert response.status_code == 202
        data = response.json()
        clip = db_session.query(Clip).filter(Clip.id == data["clip_id"]).first()
        assert clip.model == "luxtts"


class TestVoiceoverService:
    def test_voiceover_service_module_imports(self):
        from backend.services.voiceover import run_voiceover_generation
        assert callable(run_voiceover_generation)
