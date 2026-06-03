"""Tests for project and clip CRUD endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base
from backend.routes import register_routers


@pytest.fixture(autouse=True)
def _test_db():
    """Replace the global database session with a fresh in-memory SQLite DB."""
    import backend.database.session as sess_mod

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    sess_mod.engine = engine
    sess_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from backend.database import get_db

    app = FastAPI()
    register_routers(app)

    def override_get_db():
        db = sess_mod.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)


@pytest.fixture
def client(_test_db):
    return _test_db


@pytest.fixture
def sample_project():
    return {
        "name": "Test Project",
        "description": "A project for testing",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "duration_seconds": 15.0,
    }


class TestProjectCRUD:
    def test_create_project(self, client, sample_project):
        resp = client.post("/api/projects", json=sample_project)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Project"
        assert data["width"] == 1920
        assert data["height"] == 1080
        assert data["fps"] == 30
        assert data["duration_seconds"] == 15.0
        assert data["render_status"] == "draft"
        assert data["clip_count"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_project_minimal(self, client):
        resp = client.post("/api/projects", json={"name": "Minimal"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Minimal"
        assert data["width"] == 1920
        assert data["height"] == 1080
        assert data["fps"] == 24
        assert data["duration_seconds"] == 10.0

    def test_create_project_validation(self, client):
        resp = client.post("/api/projects", json={"name": ""})
        assert resp.status_code == 422
        resp = client.post("/api/projects", json={"name": "x", "fps": 0})
        assert resp.status_code == 422
        resp = client.post("/api/projects", json={"name": "x", "width": 0})
        assert resp.status_code == 422

    def test_list_projects(self, client, sample_project):
        client.post("/api/projects", json={"name": "Project A"})
        client.post("/api/projects", json={"name": "Project B"})
        client.post("/api/projects", json=sample_project)

        resp = client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_projects_pagination(self, client):
        for i in range(5):
            client.post("/api/projects", json={"name": f"Project {i}"})

        resp = client.get("/api/projects?offset=0&limit=2")
        assert resp.status_code == 200
        assert resp.json()["total"] == 5
        assert len(resp.json()["items"]) == 2

        resp = client.get("/api/projects?offset=2&limit=2")
        assert len(resp.json()["items"]) == 2

    def test_list_projects_search(self, client):
        client.post("/api/projects", json={"name": "My Video"})
        client.post("/api/projects", json={"name": "Another Clip"})
        client.post("/api/projects", json={"name": "Video Edit"})

        resp = client.get("/api/projects?search=Video")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_projects_sort(self, client):
        client.post("/api/projects", json={"name": "B"})
        client.post("/api/projects", json={"name": "A"})
        client.post("/api/projects", json={"name": "C"})

        resp = client.get("/api/projects?sort=name")
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()["items"]]
        assert names == ["A", "B", "C"]

        resp = client.get("/api/projects?sort=-name")
        names = [item["name"] for item in resp.json()["items"]]
        assert names == ["C", "B", "A"]

    def test_get_project(self, client, sample_project):
        create_resp = client.post("/api/projects", json=sample_project)
        project_id = create_resp.json()["id"]

        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Project"

    def test_get_project_not_found(self, client):
        resp = client.get("/api/projects/nonexistent-id")
        assert resp.status_code == 404

    def test_update_project(self, client, sample_project):
        create_resp = client.post("/api/projects", json=sample_project)
        project_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/projects/{project_id}",
            json={"name": "Updated Name", "description": "Updated desc"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["description"] == "Updated desc"
        assert resp.json()["width"] == 1920

    def test_update_project_partial(self, client, sample_project):
        create_resp = client.post("/api/projects", json=sample_project)
        project_id = create_resp.json()["id"]

        resp = client.put(f"/api/projects/{project_id}", json={"fps": 60})
        assert resp.status_code == 200
        assert resp.json()["fps"] == 60
        assert resp.json()["name"] == "Test Project"

    def test_delete_project(self, client, sample_project):
        create_resp = client.post("/api/projects", json=sample_project)
        project_id = create_resp.json()["id"]

        resp = client.delete(f"/api/projects/{project_id}")
        assert resp.status_code == 204

        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 404

    def test_deleted_project_not_in_list(self, client, sample_project):
        create_resp = client.post("/api/projects", json=sample_project)
        project_id = create_resp.json()["id"]
        client.delete(f"/api/projects/{project_id}")

        resp = client.get("/api/projects")
        assert resp.json()["total"] == 0


class TestClipCRUD:
    def _create_project(self, client):
        resp = client.post("/api/projects", json={"name": "Clip Test Project"})
        return resp.json()["id"]

    def test_create_clip(self, client):
        project_id = self._create_project(client)

        resp = client.post(
            f"/api/projects/{project_id}/clips",
            json={
                "track": 0,
                "start_time_ms": 0,
                "end_time_ms": 5000,
                "clip_type": "video",
                "source_text": "a cat playing",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["clip_type"] == "video"
        assert data["track"] == 0
        assert data["start_time_ms"] == 0
        assert data["end_time_ms"] == 5000
        assert data["project_id"] == project_id
        assert "id" in data

    def test_create_clip_missing_project(self, client):
        resp = client.post(
            "/api/projects/nonexistent/clips",
            json={"end_time_ms": 3000, "clip_type": "video"},
        )
        assert resp.status_code == 404

    def test_create_clip_with_effects(self, client):
        project_id = self._create_project(client)

        resp = client.post(
            f"/api/projects/{project_id}/clips",
            json={
                "end_time_ms": 3000,
                "clip_type": "video",
                "effects_chain": [{"type": "blur", "radius": 5}],
                "fade_in_ms": 200,
                "fade_out_ms": 500,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["effects_chain"] == [{"type": "blur", "radius": 5}]
        assert data["fade_in_ms"] == 200
        assert data["fade_out_ms"] == 500

    def test_list_clips(self, client):
        project_id = self._create_project(client)

        client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 2000, "clip_type": "video", "track": 0},
        )
        client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "music", "track": 1},
        )

        resp = client.get(f"/api/projects/{project_id}/clips")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_clips_ordered(self, client):
        project_id = self._create_project(client)

        client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 5000, "clip_type": "video", "track": 0, "start_time_ms": 3000},
        )
        client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 5000, "clip_type": "video", "track": 0, "start_time_ms": 0},
        )

        resp = client.get(f"/api/projects/{project_id}/clips")
        items = resp.json()
        assert items[0]["start_time_ms"] == 0
        assert items[1]["start_time_ms"] == 3000

    def test_get_clip(self, client):
        project_id = self._create_project(client)

        create_resp = client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "video"},
        )
        clip_id = create_resp.json()["id"]

        resp = client.get(f"/api/projects/{project_id}/clips/{clip_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == clip_id

    def test_get_clip_not_found(self, client):
        project_id = self._create_project(client)
        resp = client.get(f"/api/projects/{project_id}/clips/nonexistent")
        assert resp.status_code == 404

    def test_update_clip(self, client):
        project_id = self._create_project(client)

        create_resp = client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "video"},
        )
        clip_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/projects/{project_id}/clips/{clip_id}",
            json={"volume": 0.5, "speed": 2.0},
        )
        assert resp.status_code == 200
        assert resp.json()["volume"] == 0.5
        assert resp.json()["speed"] == 2.0

    def test_delete_clip(self, client):
        project_id = self._create_project(client)

        create_resp = client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "video"},
        )
        clip_id = create_resp.json()["id"]

        resp = client.delete(f"/api/projects/{project_id}/clips/{clip_id}")
        assert resp.status_code == 204

        resp = client.get(f"/api/projects/{project_id}/clips/{clip_id}")
        assert resp.status_code == 404


class TestTimelineBatch:
    def _create_project_with_clips(self, client):
        project_resp = client.post("/api/projects", json={"name": "Batch Test"})
        project_id = project_resp.json()["id"]

        clip1 = client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "video", "track": 0, "start_time_ms": 0},
        ).json()
        clip2 = client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "music", "track": 1, "start_time_ms": 0},
        ).json()

        return project_id, clip1, clip2

    def test_batch_update_positions(self, client):
        project_id, clip1, clip2 = self._create_project_with_clips(client)

        resp = client.put(
            f"/api/projects/{project_id}/clips/timeline/batch",
            json={
                "clips": [
                    {"clip_id": clip1["id"], "track": 2, "start_time_ms": 5000},
                    {"clip_id": clip2["id"], "track": 0, "start_time_ms": 1000},
                ]
            },
        )
        assert resp.status_code == 204

        clips = client.get(f"/api/projects/{project_id}/clips").json()
        clip1_updated = next(c for c in clips if c["id"] == clip1["id"])
        clip2_updated = next(c for c in clips if c["id"] == clip2["id"])

        assert clip1_updated["track"] == 2
        assert clip1_updated["start_time_ms"] == 5000
        assert clip2_updated["track"] == 0
        assert clip2_updated["start_time_ms"] == 1000

    def test_batch_missing_clip(self, client):
        project_id, clip1, _ = self._create_project_with_clips(client)

        resp = client.put(
            f"/api/projects/{project_id}/clips/timeline/batch",
            json={
                "clips": [
                    {"clip_id": clip1["id"], "track": 1, "start_time_ms": 0},
                    {"clip_id": "nonexistent", "track": 1, "start_time_ms": 0},
                ]
            },
        )
        assert resp.status_code == 404

    def test_batch_nonexistent_project(self, client):
        resp = client.put(
            "/api/projects/nonexistent/clips/timeline/batch",
            json={"clips": []},
        )
        assert resp.status_code == 404


class TestCascadeDelete:
    def test_delete_project_cascades_to_clips(self, client):
        project_resp = client.post("/api/projects", json={"name": "Cascade Test"})
        project_id = project_resp.json()["id"]

        client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "video"},
        )
        client.post(
            f"/api/projects/{project_id}/clips",
            json={"end_time_ms": 3000, "clip_type": "music"},
        )

        client.delete(f"/api/projects/{project_id}")

        clips_resp = client.get(f"/api/projects/{project_id}/clips")
        assert clips_resp.status_code == 404
