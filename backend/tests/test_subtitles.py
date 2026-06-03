"""Tests for subtitle generation endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.database.models import Clip, Project, SubtitleTrack


@pytest.fixture
def test_client(db_session):
    app = create_app()
    from backend.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_and_clip(db_session):
    project = Project(name="Test", width=1920, height=1080, fps=24, duration_seconds=10.0)
    db_session.add(project)
    db_session.commit()

    clip = Clip(
        project_id=project.id,
        track=1,
        start_time_ms=0,
        end_time_ms=5000,
        clip_type="voiceover",
        source_text="Hello world",
        source_path="data/test/audio.wav",
    )
    db_session.add(clip)
    db_session.commit()
    db_session.refresh(clip)
    return project, clip


class TestSubtitleEndpointErrorHandling:
    def test_generate_subtitles_clip_not_found(self, test_client):
        response = test_client.post(
            "/api/subtitles/generate",
            json={"clip_id": "nonexistent"},
        )
        assert response.status_code == 400

    def test_generate_subtitles_no_audio_source(self, test_client, db_session):
        project = Project(name="Test")
        db_session.add(project)
        db_session.commit()

        clip = Clip(
            project_id=project.id,
            track=1,
            start_time_ms=0,
            end_time_ms=1000,
            clip_type="voiceover",
            source_text="Hello",
        )
        db_session.add(clip)
        db_session.commit()
        db_session.refresh(clip)

        response = test_client.post(
            "/api/subtitles/generate",
            json={"clip_id": clip.id},
        )
        assert response.status_code == 400
        assert "no audio source" in response.json()["detail"].lower()


class TestSubtitleEndpointSuccess:
    @patch("backend.services.subtitle.get_whisper_model")
    def test_generate_subtitles_creates_track(self, mock_get_whisper, test_client, sample_project_and_clip, db_session):
        project, clip = sample_project_and_clip

        mock_whisper = MagicMock()
        mock_whisper.is_loaded.return_value = True

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.5
        mock_segment.text = "Hello world"

        mock_result = MagicMock()
        mock_result.segments = [mock_segment]
        mock_whisper.transcribe.return_value = mock_result

        mock_get_whisper.return_value = mock_whisper

        response = test_client.post(
            "/api/subtitles/generate",
            json={"clip_id": clip.id, "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["clip_id"] == clip.id
        assert len(data["items"]) == 1
        assert data["items"][0]["text"] == "Hello world"
        assert data["items"][0]["start_ms"] == 0
        assert data["items"][0]["end_ms"] == 2500

    @patch("backend.services.subtitle.get_whisper_model")
    def test_generate_subtitles_updates_existing_track(self, mock_get_whisper, test_client, sample_project_and_clip, db_session):
        project, clip = sample_project_and_clip

        existing = SubtitleTrack(
            project_id=project.id,
            clip_id=clip.id,
            language="en",
            items=[{"start_ms": 0, "end_ms": 1000, "text": "old"}],
        )
        db_session.add(existing)
        db_session.commit()

        mock_whisper = MagicMock()
        mock_whisper.is_loaded.return_value = True

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 3.0
        mock_segment.text = "Updated text"

        mock_result = MagicMock()
        mock_result.segments = [mock_segment]
        mock_whisper.transcribe.return_value = mock_result

        mock_get_whisper.return_value = mock_whisper

        response = test_client.post(
            "/api/subtitles/generate",
            json={"clip_id": clip.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["text"] == "Updated text"


class TestSubtitleUpdateEndpoint:
    def test_update_subtitle_track_not_found(self, test_client):
        response = test_client.put("/api/subtitles/nonexistent", json={"items": []})
        assert response.status_code == 404

    def test_update_subtitle_items(self, test_client, sample_project_and_clip, db_session):
        project, clip = sample_project_and_clip
        track = SubtitleTrack(
            project_id=project.id,
            clip_id=clip.id,
            language="en",
            items=[{"start_ms": 0, "end_ms": 1000, "text": "original"}],
        )
        db_session.add(track)
        db_session.commit()
        db_session.refresh(track)

        response = test_client.put(
            f"/api/subtitles/{track.id}",
            json={
                "items": [
                    {"start_ms": 0, "end_ms": 500, "text": "edited"},
                    {"start_ms": 500, "end_ms": 1000, "text": "more"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["text"] == "edited"

    def test_update_subtitle_style(self, test_client, sample_project_and_clip, db_session):
        project, clip = sample_project_and_clip
        track = SubtitleTrack(
            project_id=project.id,
            clip_id=clip.id,
            language="en",
            items=[{"start_ms": 0, "end_ms": 1000, "text": "test"}],
        )
        db_session.add(track)
        db_session.commit()
        db_session.refresh(track)

        response = test_client.put(
            f"/api/subtitles/{track.id}",
            json={"style": {"font": "Arial", "size": 24, "color": "white"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["style"]["font"] == "Arial"
        assert data["style"]["size"] == 24


class TestVoiceProfilesEndpoint:
    """Test slimmed voice profiles CRUD."""

    def test_list_profiles_empty(self, test_client):
        response = test_client.get("/api/voice-profiles")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_profile(self, test_client, db_session):
        response = test_client.post(
            "/api/voice-profiles",
            json={
                "name": "New Profile",
                "voice_type": "preset",
                "preset_engine": "qwen",
                "preset_voice_id": "default",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Profile"
        assert data["voice_type"] == "preset"
        assert "id" in data

    def test_create_profile_duplicate_name(self, test_client, db_session):
        test_client.post(
            "/api/voice-profiles",
            json={"name": "Dup", "voice_type": "preset", "preset_engine": "qwen", "preset_voice_id": "x"},
        )
        response = test_client.post(
            "/api/voice-profiles",
            json={"name": "Dup", "voice_type": "preset", "preset_engine": "qwen", "preset_voice_id": "x"},
        )
        assert response.status_code == 409

    def test_get_profile_not_found(self, test_client):
        response = test_client.get("/api/voice-profiles/nonexistent")
        assert response.status_code == 404

    def test_get_profile(self, test_client, db_session):
        from backend.database.models import VoiceProfile
        profile = VoiceProfile(name="Test", voice_type="preset", preset_engine="qwen", preset_voice_id="x")
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)

        response = test_client.get(f"/api/voice-profiles/{profile.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_update_profile(self, test_client, db_session):
        from backend.database.models import VoiceProfile
        profile = VoiceProfile(name="Original", voice_type="preset", preset_engine="qwen", preset_voice_id="x")
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)

        response = test_client.put(
            f"/api/voice-profiles/{profile.id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_delete_profile(self, test_client, db_session):
        from backend.database.models import VoiceProfile
        profile = VoiceProfile(name="ToDelete", voice_type="preset", preset_engine="qwen", preset_voice_id="x")
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)

        response = test_client.delete(f"/api/voice-profiles/{profile.id}")
        assert response.status_code == 204

    def test_delete_profile_not_found(self, test_client):
        response = test_client.delete("/api/voice-profiles/nonexistent")
        assert response.status_code == 404


class TestSubtitleService:
    def test_subtitle_track_to_response(self):
        from backend.services.subtitle import _subtitle_track_to_response
        from unittest.mock import MagicMock

        track = MagicMock()
        track.id = "test-id"
        track.project_id = "proj-id"
        track.clip_id = "clip-id"
        track.language = "en"
        track.items = [{"start_ms": 0, "end_ms": 1000, "text": "hello"}]
        track.style = None
        from datetime import datetime
        track.created_at = datetime.utcnow()
        track.updated_at = datetime.utcnow()

        resp = _subtitle_track_to_response(track)
        assert resp.id == "test-id"
        assert len(resp.items) == 1
        assert resp.items[0].text == "hello"
