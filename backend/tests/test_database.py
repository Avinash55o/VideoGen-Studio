"""Tests for the VideoGen database schema and ORM models."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.models import (
    Project,
    Clip,
    SubtitleTrack,
    Render,
    VoiceProfile,
    VoiceSample,
    AudioLibraryEntry,
    Template,
    uuid7,
)
from backend.database.session import SessionLocal


class TestUUID7:
    def test_generates_unique_values(self):
        ids = {uuid7() for _ in range(1000)}
        assert len(ids) == 1000

    def test_returns_string(self):
        assert isinstance(uuid7(), str)
        assert len(uuid7()) == 36  # standard UUID format


class TestProject:
    def test_create_project(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        saved = db_session.query(Project).first()
        assert saved.name == "Test Project"
        assert saved.width == 1920
        assert saved.height == 1080
        assert saved.fps == 24
        assert saved.duration_seconds == 10.0
        assert saved.render_status == "draft"
        assert saved.render_progress == 0.0
        assert saved.deleted_at is None

    def test_default_values(self, db_session):
        project = Project(name="Minimal")
        db_session.add(project)
        db_session.commit()

        saved = db_session.query(Project).first()
        assert saved.width == 1920
        assert saved.height == 1080
        assert saved.fps == 24
        assert saved.duration_seconds == 10.0
        assert saved.render_status == "draft"

    def test_soft_delete(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        project.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        saved = db_session.query(Project).first()
        assert saved.deleted_at is not None

    def test_project_requires_name(self, db_session):
        project = Project()
        db_session.add(project)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_timestamps_set_on_create(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        assert project.created_at is not None
        assert project.updated_at is not None
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)


class TestClip:
    def test_create_clip(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        clip = Clip(
            project_id=project.id,
            track=0,
            start_time_ms=0,
            end_time_ms=5000,
            clip_type="video",
            source_path="/path/to/video.mp4",
        )
        db_session.add(clip)
        db_session.commit()

        saved = db_session.query(Clip).first()
        assert saved.project_id == project.id
        assert saved.track == 0
        assert saved.start_time_ms == 0
        assert saved.end_time_ms == 5000
        assert saved.clip_type == "video"
        assert saved.volume == 1.0
        assert saved.speed == 1.0

    def test_clip_belongs_to_project(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        clip = Clip(project_id=project.id, end_time_ms=3000, clip_type="music")
        db_session.add(clip)
        db_session.commit()

        assert clip in project.clips
        assert clip.project == project

    def test_cascade_delete(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        clip = Clip(project_id=project.id, end_time_ms=3000, clip_type="video")
        db_session.add(clip)
        db_session.commit()

        db_session.delete(project)
        db_session.commit()

        assert db_session.query(Clip).count() == 0

    def test_clip_with_effects_chain(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        effects = [{"type": "blur", "radius": 5}, {"type": "color_grade", "lut": "warm"}]
        clip = Clip(
            project_id=project.id,
            end_time_ms=3000,
            clip_type="video",
            effects_chain=effects,
        )
        db_session.add(clip)
        db_session.commit()

        saved = db_session.query(Clip).first()
        assert saved.effects_chain == effects

    def test_fade_in_out(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        clip = Clip(
            project_id=project.id,
            end_time_ms=3000,
            clip_type="video",
            fade_in_ms=200,
            fade_out_ms=500,
        )
        db_session.add(clip)
        db_session.commit()

        saved = db_session.query(Clip).first()
        assert saved.fade_in_ms == 200
        assert saved.fade_out_ms == 500


class TestSubtitleTrack:
    def test_create_subtitle_track(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        items = [
            {"start_ms": 0, "end_ms": 2000, "text": "Hello"},
            {"start_ms": 2000, "end_ms": 5000, "text": "World"},
        ]
        track = SubtitleTrack(project_id=project.id, language="en", items=items)
        db_session.add(track)
        db_session.commit()

        saved = db_session.query(SubtitleTrack).first()
        assert saved.language == "en"
        assert len(saved.items) == 2
        assert saved.items[0]["text"] == "Hello"
        assert saved.project_id == project.id


class TestRender:
    def test_create_render(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        render = Render(
            project_id=project.id,
            file_path="/path/to/output.mp4",
            format="mp4",
            status="rendering",
        )
        db_session.add(render)
        db_session.commit()

        saved = db_session.query(Render).first()
        assert saved.project_id == project.id
        assert saved.format == "mp4"
        assert saved.status == "rendering"

    def test_render_belongs_to_project(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        render = Render(project_id=project.id, file_path="/out.mp4")
        db_session.add(render)
        db_session.commit()

        assert render in project.renders

    def test_cascade_delete(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        render = Render(project_id=project.id, file_path="/out.mp4")
        db_session.add(render)
        db_session.commit()

        db_session.delete(project)
        db_session.commit()

        assert db_session.query(Render).count() == 0


class TestVoiceProfile:
    def test_create_voice_profile(self, db_session):
        profile = VoiceProfile(
            name="Test Voice",
            description="A test voice",
            voice_type="cloned",
            language="en",
        )
        db_session.add(profile)
        db_session.commit()

        saved = db_session.query(VoiceProfile).first()
        assert saved.name == "Test Voice"
        assert saved.voice_type == "cloned"
        assert len(saved.samples) == 0

    def test_unique_name(self, db_session):
        VoiceProfile(name="Duplicate", voice_type="cloned")
        db_session.add(VoiceProfile(name="Unique", voice_type="cloned"))
        db_session.commit()

        with pytest.raises(Exception):
            db_session.add(VoiceProfile(name="Unique", voice_type="preset"))
            db_session.commit()

    def test_with_samples(self, db_session):
        profile = VoiceProfile(name="Sampled Voice", voice_type="cloned")
        db_session.add(profile)
        db_session.commit()

        sample = VoiceSample(
            profile_id=profile.id,
            audio_path="/path/to/sample.wav",
            reference_text="Hello world",
        )
        db_session.add(sample)
        db_session.commit()

        saved = db_session.query(VoiceProfile).first()
        assert len(saved.samples) == 1
        assert saved.samples[0].reference_text == "Hello world"

    def test_cascade_delete_samples(self, db_session):
        profile = VoiceProfile(name="To Delete", voice_type="cloned")
        db_session.add(profile)
        db_session.commit()

        sample = VoiceSample(profile_id=profile.id, audio_path="/s.wav", reference_text="t")
        db_session.add(sample)
        db_session.commit()

        db_session.delete(profile)
        db_session.commit()

        assert db_session.query(VoiceSample).count() == 0


class TestAudioLibrary:
    def test_create_entry(self, db_session):
        entry = AudioLibraryEntry(
            name="Background Music",
            file_path="/path/to/music.wav",
            category="music",
            tags=["ambient", "royalty-free"],
        )
        db_session.add(entry)
        db_session.commit()

        saved = db_session.query(AudioLibraryEntry).first()
        assert saved.name == "Background Music"
        assert saved.category == "music"
        assert saved.tags == ["ambient", "royalty-free"]

    def test_category_index(self, db_session):
        for cat in ["music", "sfx", "music", "ambient"]:
            db_session.add(AudioLibraryEntry(
                name=f"Entry {cat}", file_path=f"/{cat}.wav", category=cat,
            ))
        db_session.commit()

        assert db_session.query(AudioLibraryEntry).filter(
            AudioLibraryEntry.category == "music"
        ).count() == 2


class TestTemplate:
    def test_create_template(self, db_session):
        template = Template(
            name="Cinematic Intro",
            description="A dramatic opening sequence",
            project_data={"clips": [], "timeline": {}},
            category="intros",
            is_builtin=True,
        )
        db_session.add(template)
        db_session.commit()

        saved = db_session.query(Template).first()
        assert saved.name == "Cinematic Intro"
        assert saved.is_builtin is True
        assert saved.project_data == {"clips": [], "timeline": {}}

    def test_builtin_default(self, db_session):
        template = Template(
            name="Custom",
            project_data={"clips": []},
        )
        db_session.add(template)
        db_session.commit()

        assert template.is_builtin is False


class TestRelationships:
    def test_project_clips_relationship(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        clips = [
            Clip(project_id=project.id, end_time_ms=2000, clip_type="video"),
            Clip(project_id=project.id, end_time_ms=3000, clip_type="music"),
            Clip(project_id=project.id, end_time_ms=4000, clip_type="voiceover"),
        ]
        for c in clips:
            db_session.add(c)
        db_session.commit()

        saved = db_session.query(Project).first()
        assert len(saved.clips) == 3

    def test_project_multiple_children(self, db_session, sample_project_data):
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()

        clip = Clip(project_id=project.id, end_time_ms=2000, clip_type="video")
        db_session.add(clip)
        track = SubtitleTrack(project_id=project.id, items=[])
        db_session.add(track)
        render = Render(project_id=project.id, file_path="/out.mp4")
        db_session.add(render)
        db_session.commit()

        saved = db_session.query(Project).first()
        assert len(saved.clips) == 1
        assert len(saved.subtitle_tracks) == 1
        assert len(saved.renders) == 1
