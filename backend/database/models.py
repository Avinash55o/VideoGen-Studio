"""SQLAlchemy ORM models for VideoGen Studio."""

import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def uuid7() -> str:
    """Time-ordered UUID v7 for B-tree-friendly primary keys."""
    try:
        return str(_uuid.uuid7())
    except AttributeError:
        # Fallback for Python <3.14: build a UUID4-like string
        return str(_uuid.uuid4())


class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=uuid7)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    width = Column(Integer, nullable=False, default=1920)
    height = Column(Integer, nullable=False, default=1080)
    fps = Column(Integer, nullable=False, default=24)
    duration_seconds = Column(Float, nullable=False, default=10.0)
    thumbnail_path = Column(String, nullable=True)
    render_status = Column(String, default="draft")
    render_progress = Column(Float, default=0.0)
    output_path = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    clips = relationship("Clip", back_populates="project", cascade="all, delete-orphan",
                         passive_deletes=True)
    subtitle_tracks = relationship("SubtitleTrack", back_populates="project",
                                   cascade="all, delete-orphan", passive_deletes=True)
    renders = relationship("Render", back_populates="project", cascade="all, delete-orphan",
                           passive_deletes=True)


class Clip(TimestampMixin, Base):
    __tablename__ = "clips"

    id = Column(String, primary_key=True, default=uuid7)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    track = Column(Integer, nullable=False, default=0)
    start_time_ms = Column(Integer, nullable=False, default=0)
    end_time_ms = Column(Integer, nullable=False)
    clip_type = Column(String, nullable=False)
    source_path = Column(String, nullable=True)
    source_text = Column(Text, nullable=True)
    model = Column(String, nullable=True)
    seed = Column(Integer, nullable=True)
    volume = Column(Float, nullable=False, default=1.0)
    speed = Column(Float, nullable=False, default=1.0)
    fade_in_ms = Column(Integer, nullable=False, default=0)
    fade_out_ms = Column(Integer, nullable=False, default=0)
    effects_chain = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="clips")


class SubtitleTrack(TimestampMixin, Base):
    __tablename__ = "subtitle_tracks"

    id = Column(String, primary_key=True, default=uuid7)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    clip_id = Column(String, ForeignKey("clips.id", ondelete="SET NULL"), nullable=True)
    language = Column(String, default="en")
    items = Column(JSON, nullable=False, default=list)
    style = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="subtitle_tracks")


class Render(TimestampMixin, Base):
    __tablename__ = "renders"

    id = Column(String, primary_key=True, default=uuid7)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String, nullable=False)
    format = Column(String, default="mp4")
    resolution = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    status = Column(String, default="rendering")

    project = relationship("Project", back_populates="renders")


class VoiceProfile(TimestampMixin, Base):
    __tablename__ = "voice_profiles"

    id = Column(String, primary_key=True, default=uuid7)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    voice_type = Column(String, default="cloned")
    preset_engine = Column(String, nullable=True)
    preset_voice_id = Column(String, nullable=True)
    design_prompt = Column(Text, nullable=True)
    default_engine = Column(String, nullable=True)
    language = Column(String, default="en")

    samples = relationship("VoiceSample", back_populates="profile",
                           cascade="all, delete-orphan", passive_deletes=True)


class VoiceSample(Base):
    __tablename__ = "voice_samples"

    id = Column(String, primary_key=True, default=uuid7)
    profile_id = Column(String, ForeignKey("voice_profiles.id", ondelete="CASCADE"), nullable=False)
    audio_path = Column(String, nullable=False)
    reference_text = Column(Text, nullable=False)

    profile = relationship("VoiceProfile", back_populates="samples")


class AudioLibraryEntry(TimestampMixin, Base):
    __tablename__ = "audio_library"

    id = Column(String, primary_key=True, default=uuid7)
    name = Column(String(200), nullable=False)
    file_path = Column(String, nullable=False)
    category = Column(String, default="music")
    duration_seconds = Column(Float, nullable=True)
    source = Column(String, default="imported")
    model = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)

    __table_args__ = (Index("ix_audio_library_category", "category"),)


class Template(TimestampMixin, Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True, default=uuid7)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    project_data = Column(JSON, nullable=False)
    category = Column(String, default="general")
    is_builtin = Column(Boolean, default=False)


class Generation(TimestampMixin, Base):
    __tablename__ = "generations"

    id = Column(String, primary_key=True, default=uuid7)
    profile_id = Column(String, ForeignKey("voice_profiles.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    language = Column(String, default="en")
    audio_path = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    seed = Column(Integer, nullable=True)
    instruct = Column(Text, nullable=True)
    engine = Column(String, nullable=True)
    model_size = Column(String, nullable=True)
    status = Column(String, default="generating")
    error = Column(Text, nullable=True)
    is_favorited = Column(Boolean, default=False)
    max_chunk_chars = Column(Integer, nullable=True)
    crossfade_ms = Column(Integer, nullable=True)
    normalize = Column(Boolean, default=True)
    effects_chain = Column(JSON, nullable=True)

    profile = relationship("VoiceProfile", backref="generations")
    versions = relationship("GenerationVersion", back_populates="generation",
                            cascade="all, delete-orphan", passive_deletes=True)


class GenerationVersion(TimestampMixin, Base):
    __tablename__ = "generation_versions"

    id = Column(String, primary_key=True, default=uuid7)
    generation_id = Column(String, ForeignKey("generations.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String, default="original")
    audio_path = Column(String, nullable=False)
    effects_chain = Column(JSON, nullable=True)
    source_version_id = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)

    generation = relationship("Generation", back_populates="versions")


class ProfileSample(Base):
    __tablename__ = "profile_samples"

    id = Column(String, primary_key=True, default=uuid7)
    profile_id = Column(String, ForeignKey("voice_profiles.id", ondelete="CASCADE"), nullable=False)
    audio_path = Column(String, nullable=False)
    reference_text = Column(Text, nullable=False)


class MCPClientBinding(TimestampMixin, Base):
    __tablename__ = "mcp_client_bindings"

    client_id = Column(String, primary_key=True)
    label = Column(String, nullable=True)
    profile_id = Column(String, ForeignKey("voice_profiles.id"), nullable=True)
    default_engine = Column(String, nullable=True)
    default_personality = Column(Boolean, default=False)
    last_seen_at = Column(DateTime, nullable=True)


class Capture(TimestampMixin, Base):
    __tablename__ = "captures"

    id = Column(String, primary_key=True, default=uuid7)
    audio_path = Column(String, nullable=False)
    source = Column(String, nullable=False, default="file")
    language = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    transcript_raw = Column(Text, nullable=False, default="")
    transcript_refined = Column(Text, nullable=True)
    stt_model = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    refinement_flags = Column(JSON, nullable=True)


class CaptureSettings(Base):
    __tablename__ = "capture_settings"

    id = Column(String, primary_key=True, default=uuid7)
    stt_model = Column(String, default="turbo")
    language = Column(String, default="en")
    auto_refine = Column(Boolean, default=False)
    llm_model = Column(String, default="0.6B")
    smart_cleanup = Column(Boolean, default=True)
    self_correction = Column(Boolean, default=True)
    preserve_technical = Column(Boolean, default=False)
    allow_auto_paste = Column(Boolean, default=True)
    default_playback_voice_id = Column(String, nullable=True)
    hotkey_enabled = Column(Boolean, default=False)
    chord_push_to_talk_keys = Column(JSON, default=list)
    chord_toggle_to_talk_keys = Column(JSON, default=list)


class GenerationSettings(Base):
    __tablename__ = "generation_settings"

    id = Column(String, primary_key=True, default=uuid7)
    max_chunk_chars = Column(Integer, default=1000)
    crossfade_ms = Column(Integer, default=50)
    normalize_audio = Column(Boolean, default=True)
    autoplay_on_generate = Column(Boolean, default=True)
    output_resolution = Column(String(16), default="1080p")
    output_fps = Column(Integer, default=30)
    video_codec = Column(String(16), default="h264")
    max_render_duration_secs = Column(Integer, default=600)


class EffectPreset(TimestampMixin, Base):
    __tablename__ = "effect_presets"

    id = Column(String, primary_key=True, default=uuid7)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    effects_chain = Column(JSON, nullable=False)
    is_builtin = Column(Boolean, default=False)


class Story(TimestampMixin, Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True, default=uuid7)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    item_count = Column(Integer, default=0)

    items = relationship("StoryItem", back_populates="story",
                         cascade="all, delete-orphan", passive_deletes=True)


class StoryItem(TimestampMixin, Base):
    __tablename__ = "story_items"

    id = Column(String, primary_key=True, default=uuid7)
    story_id = Column(String, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    generation_id = Column(String, ForeignKey("generations.id"), nullable=False)
    version_id = Column(String, nullable=True)
    start_time_ms = Column(Integer, default=0)
    track = Column(Integer, default=0)
    trim_start_ms = Column(Integer, default=0)
    trim_end_ms = Column(Integer, default=0)
    volume = Column(Float, default=1.0)

    story = relationship("Story", back_populates="items")
    generation = relationship("Generation")


class AudioChannel(TimestampMixin, Base):
    __tablename__ = "audio_channels"

    id = Column(String, primary_key=True, default=uuid7)
    name = Column(String(200), nullable=False)
    is_default = Column(Boolean, default=False)
    device_ids = Column(JSON, default=list)


class ChannelDeviceMapping(Base):
    __tablename__ = "channel_device_mappings"

    id = Column(String, primary_key=True, default=uuid7)
    channel_id = Column(String, ForeignKey("audio_channels.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(String, nullable=False)


class ProfileChannelMapping(Base):
    __tablename__ = "profile_channel_mappings"

    id = Column(String, primary_key=True, default=uuid7)
    profile_id = Column(String, ForeignKey("voice_profiles.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(String, ForeignKey("audio_channels.id", ondelete="CASCADE"), nullable=False)
