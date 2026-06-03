"""Tests for video generation endpoints and backends."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.database.models import Clip, Project
from backend.database.session import SessionLocal


@pytest.fixture
def test_client(db_session):
    """Create a test client with the real app, patching db session."""
    app = create_app()
    app.dependency_overrides.clear()

    from backend.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_project(db_session):
    project = Project(name="Test Project", width=1920, height=1080, fps=24, duration_seconds=10.0)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestGenerationEndpointErrorHandling:
    """Test generation endpoint with proper error cases."""

    def test_generate_video_project_not_found(self, test_client):
        response = test_client.post(
            "/api/generate/video",
            json={"project_id": "nonexistent", "prompt": "test", "model": "cogvideo-2b"},
        )
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    def test_generate_video_missing_prompt(self, test_client, sample_project):
        response = test_client.post(
            "/api/generate/video",
            json={"project_id": sample_project.id, "model": "cogvideo-2b"},
        )
        assert response.status_code == 422

    def test_generate_video_empty_prompt(self, test_client, sample_project):
        response = test_client.post(
            "/api/generate/video",
            json={"project_id": sample_project.id, "prompt": "", "model": "cogvideo-2b"},
        )
        assert response.status_code == 422

    def test_generate_video_invalid_model(self, test_client, sample_project):
        response = test_client.post(
            "/api/generate/video",
            json={
                "project_id": sample_project.id,
                "prompt": "test video",
                "model": "nonexistent-model",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data


class TestGenerationEndpointSuccess:
    """Test successful generation request flow with mocked backend."""

    @patch("backend.routes.generation.run_video_generation", new_callable=AsyncMock)
    def test_generate_video_creates_clip(self, mock_run, test_client, sample_project, db_session):
        response = test_client.post(
            "/api/generate/video",
            json={
                "project_id": sample_project.id,
                "prompt": "a cat walking in a park",
                "model": "cogvideo-2b",
                "num_frames": 24,
                "guidance_scale": 7.0,
                "num_inference_steps": 50,
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"

        clip = db_session.query(Clip).filter(Clip.id == data["task_id"]).first()
        assert clip is not None
        assert clip.project_id == sample_project.id
        assert clip.track == 0
        assert clip.clip_type == "video"
        assert clip.source_text == "a cat walking in a park"
        assert clip.model == "cogvideo-2b"

    @patch("backend.routes.generation.run_video_generation", new_callable=AsyncMock)
    def test_generate_video_with_seed(self, mock_run, test_client, sample_project, db_session):
        response = test_client.post(
            "/api/generate/video",
            json={
                "project_id": sample_project.id,
                "prompt": "cat walking",
                "model": "cogvideo-2b",
                "seed": 42,
            },
        )
        assert response.status_code == 202
        data = response.json()
        clip = db_session.query(Clip).filter(Clip.id == data["task_id"]).first()
        assert clip.seed == 42

    @patch("backend.routes.generation.run_video_generation", new_callable=AsyncMock)
    def test_generate_video_with_negative_prompt(self, mock_run, test_client, sample_project, db_session):
        response = test_client.post(
            "/api/generate/video",
            json={
                "project_id": sample_project.id,
                "prompt": "cat walking",
                "negative_prompt": "blurry, low quality",
                "model": "wan-t2v",
                "num_frames": 16,
            },
        )
        assert response.status_code == 202
        data = response.json()
        clip = db_session.query(Clip).filter(Clip.id == data["task_id"]).first()
        assert clip.model == "wan-t2v"

    @patch("backend.routes.generation.run_video_generation", new_callable=AsyncMock)
    def test_generate_video_with_custom_params(self, mock_run, test_client, sample_project, db_session):
        response = test_client.post(
            "/api/generate/video",
            json={
                "project_id": sample_project.id,
                "prompt": "cat walking",
                "model": "cogvideo-2b",
                "num_frames": 48,
                "guidance_scale": 12.0,
                "num_inference_steps": 100,
            },
        )
        assert response.status_code == 202
        data = response.json()
        clip = db_session.query(Clip).filter(Clip.id == data["task_id"]).first()
        assert clip is not None

    @patch("backend.routes.generation.run_video_generation", new_callable=AsyncMock)
    def test_generate_video_creates_clip_on_deleted_project(self, mock_run, test_client, db_session):
        project = Project(name="Deleted", deleted_at="2025-01-01T00:00:00")
        db_session.add(project)
        db_session.commit()

        response = test_client.post(
            "/api/generate/video",
            json={"project_id": project.id, "prompt": "test", "model": "cogvideo-2b"},
        )
        assert response.status_code == 404


class TestGenerationProgressEndpoint:
    """Test SSE progress endpoint."""

    def test_progress_unknown_task(self, test_client):
        response = test_client.get("/api/generate/progress/nonexistent-task")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_progress_stream_format(self, test_client):
        response = test_client.get("/api/generate/progress/test-task-123")
        assert response.headers["cache-control"] == "no-cache"
        assert "text/event-stream" in response.headers["content-type"]


class TestVideoBackendFactory:
    """Test video backend factory."""

    def test_get_cogvideo_backend(self):
        from backend.backends.video import get_video_backend
        backend = get_video_backend("cogvideo-2b")
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        assert isinstance(backend, CogVideoBackend)

    def test_get_cogvideo_short_name(self):
        from backend.backends.video import get_video_backend
        backend = get_video_backend("cogvideo")
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        assert isinstance(backend, CogVideoBackend)

    def test_get_wan_backend(self):
        from backend.backends.video import get_video_backend
        backend = get_video_backend("wan-t2v")
        from backend.backends.video.wan_backend import WanBackend
        assert isinstance(backend, WanBackend)

    def test_unknown_engine_raises(self):
        from backend.backends.video import get_video_backend
        with pytest.raises(ValueError, match="Unknown video engine"):
            get_video_backend("nonexistent")

    def test_backend_singleton(self):
        from backend.backends.video import get_video_backend, reset_video_backends
        reset_video_backends()
        a = get_video_backend("cogvideo-2b")
        b = get_video_backend("cogvideo-2b")
        assert a is b

    def test_reset_backends(self):
        from backend.backends.video import get_video_backend, reset_video_backends
        reset_video_backends()
        a = get_video_backend("cogvideo-2b")
        reset_video_backends()
        b = get_video_backend("cogvideo-2b")
        assert a is not b


class TestCogVideoBackend:
    """Test CogVideo backend unit."""

    def test_init(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        backend = CogVideoBackend()
        assert not backend.is_loaded()
        assert backend._model_size is None

    def test_model_configs_present(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        assert len(CogVideoBackend.MODEL_CONFIGS) == 2

    def test_model_configs_have_required_fields(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        for cfg in CogVideoBackend.MODEL_CONFIGS:
            assert cfg.model_name
            assert cfg.hf_repo_id
            assert cfg.pipeline_tag

    def test_hf_repo_for_size(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        backend = CogVideoBackend()
        assert "THUDM/CogVideoX-2B" in backend._hf_repo_for_size("2B")
        assert "THUDM/CogVideoX-5B-I2V" in backend._hf_repo_for_size("5B")

    def test_hf_repo_for_unknown_size(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        backend = CogVideoBackend()
        with pytest.raises(ValueError):
            backend._hf_repo_for_size("99B")

    def test_max_frames_for_vram_no_detect(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        backend = CogVideoBackend()
        frames = backend.max_frames_for_vram()
        assert isinstance(frames, int)
        assert frames > 0

    def test_unload_when_not_loaded(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        backend = CogVideoBackend()
        backend.unload_model()
        assert not backend.is_loaded()

    def test_generate_without_load_raises(self):
        from backend.backends.video.cogvideo_backend import CogVideoBackend
        backend = CogVideoBackend()
        with pytest.raises(RuntimeError, match="Model not loaded"):
            import asyncio
            asyncio.run(backend.generate(prompt="test"))


class TestWanBackend:
    """Test Wan2.1 backend unit."""

    def test_init(self):
        from backend.backends.video.wan_backend import WanBackend
        backend = WanBackend()
        assert not backend.is_loaded()
        assert backend._model_size is None

    def test_model_configs_present(self):
        from backend.backends.video.wan_backend import WanBackend
        assert len(WanBackend.MODEL_CONFIGS) == 1

    def test_generate_from_image_not_implemented(self):
        from backend.backends.video.wan_backend import WanBackend
        backend = WanBackend()
        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(backend.generate_from_image("test.jpg", "prompt"))

    def test_unload_when_not_loaded(self):
        from backend.backends.video.wan_backend import WanBackend
        backend = WanBackend()
        backend.unload_model()
        assert not backend.is_loaded()

    def test_generate_without_load_raises(self):
        from backend.backends.video.wan_backend import WanBackend
        backend = WanBackend()
        with pytest.raises(RuntimeError, match="Model not loaded"):
            import asyncio
            asyncio.run(backend.generate(prompt="test"))


class TestVideoService:
    """Test video service utilities."""

    def test_get_video_model_configs_returns_list(self):
        from backend.services.video import get_video_model_configs
        configs = get_video_model_configs()
        assert len(configs) >= 3
        names = [c.model_name for c in configs]
        assert "cogvideo-2b-t2v" in names
        assert "cogvideo-5b-i2v" in names
        assert "wan-t2v-1.3b" in names

    def test_video_configs_have_unique_names(self):
        from backend.services.video import get_video_model_configs
        configs = get_video_model_configs()
        names = [c.model_name for c in configs]
        assert len(names) == len(set(names))
