"""Pydantic request/response models for VideoGen Studio."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ── Projects ──────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    width: int = Field(default=1920, ge=1, le=7680)
    height: int = Field(default=1080, ge=1, le=4320)
    fps: int = Field(default=24, ge=1, le=120)
    duration_seconds: float = Field(default=10.0, ge=0.5, le=600.0)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    width: Optional[int] = Field(None, ge=1, le=7680)
    height: Optional[int] = Field(None, ge=1, le=4320)
    fps: Optional[int] = Field(None, ge=1, le=120)
    duration_seconds: Optional[float] = Field(None, ge=0.5, le=600.0)


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    width: int
    height: int
    fps: int
    duration_seconds: float
    thumbnail_path: Optional[str] = None
    render_status: str
    render_progress: float
    output_path: Optional[str] = None
    clip_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int


# ── Clips ─────────────────────────────────────────────────────────────

ClipType = Literal["video", "voiceover", "music", "subtitle", "image", "text"]


class ClipCreate(BaseModel):
    track: int = Field(default=0, ge=0, le=31)
    start_time_ms: int = Field(default=0, ge=0)
    end_time_ms: int = Field(gt=0)
    clip_type: ClipType
    source_path: Optional[str] = None
    source_text: Optional[str] = None
    model: Optional[str] = None
    seed: Optional[int] = None
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    fade_in_ms: int = Field(default=0, ge=0)
    fade_out_ms: int = Field(default=0, ge=0)
    effects_chain: Optional[list[dict[str, Any]]] = None


class ClipUpdate(BaseModel):
    track: Optional[int] = Field(None, ge=0, le=31)
    start_time_ms: Optional[int] = Field(None, ge=0)
    end_time_ms: Optional[int] = Field(None, gt=0)
    source_path: Optional[str] = None
    source_text: Optional[str] = None
    model: Optional[str] = None
    seed: Optional[int] = None
    volume: Optional[float] = Field(None, ge=0.0, le=2.0)
    speed: Optional[float] = Field(None, ge=0.25, le=4.0)
    fade_in_ms: Optional[int] = Field(None, ge=0)
    fade_out_ms: Optional[int] = Field(None, ge=0)
    effects_chain: Optional[list[dict[str, Any]]] = None


class ClipResponse(BaseModel):
    id: str
    project_id: str
    track: int
    start_time_ms: int
    end_time_ms: int
    clip_type: str
    source_path: Optional[str] = None
    source_text: Optional[str] = None
    model: Optional[str] = None
    seed: Optional[int] = None
    volume: float
    speed: float
    fade_in_ms: int
    fade_out_ms: int
    effects_chain: Optional[list[dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TimelineClipPosition(BaseModel):
    clip_id: str
    track: int
    start_time_ms: int


class TimelineBatchUpdate(BaseModel):
    clips: list[TimelineClipPosition]


# ── Generation ────────────────────────────────────────────────────────

class VideoGenerationRequest(BaseModel):
    project_id: str
    prompt: str = Field(min_length=1, max_length=5000)
    negative_prompt: Optional[str] = Field(None, max_length=5000)
    model: str = "cogvideo-2b"
    num_frames: int = Field(default=24, ge=8, le=256)
    guidance_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    num_inference_steps: int = Field(default=50, ge=1, le=200)
    seed: Optional[int] = None
    image_path: Optional[str] = None
    parent_clip_id: Optional[str] = None


class VideoGenerationResponse(BaseModel):
    task_id: str
    status: str


# ── Voiceover ─────────────────────────────────────────────────────────

class VoiceoverGenerateRequest(BaseModel):
    project_id: str
    profile_id: str
    text: str = Field(min_length=1, max_length=10000)
    language: str = "en"
    engine: Optional[str] = None
    model_size: Optional[str] = None


class VoiceoverGenerateResponse(BaseModel):
    clip_id: str
    task_id: str
    status: str


# ── Subtitles ─────────────────────────────────────────────────────────

class SubtitleGenerateRequest(BaseModel):
    clip_id: str
    language: Optional[str] = None
    stt_model: Optional[str] = None


class SubtitleItem(BaseModel):
    start_ms: int
    end_ms: int
    text: str


class SubtitleTrackUpdate(BaseModel):
    items: Optional[list[SubtitleItem]] = None
    style: Optional[dict[str, Any]] = None


class SubtitleTrackResponse(BaseModel):
    id: str
    project_id: str
    clip_id: Optional[str] = None
    language: str
    items: list[SubtitleItem]
    style: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Renders ───────────────────────────────────────────────────────────

class RenderRequest(BaseModel):
    format: str = Field(default="mp4", pattern=r"^(mp4|webm|mov)$")
    resolution: Optional[str] = Field(None, pattern=r"^\d+x\d+$")


class RenderResponse(BaseModel):
    id: str
    project_id: str
    status: str
    progress: float = 0.0


# ── Voice Profiles ────────────────────────────────────────────────────

class VoiceProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    voice_type: Literal["cloned", "preset", "designed"] = "cloned"
    preset_engine: Optional[str] = None
    preset_voice_id: Optional[str] = None
    design_prompt: Optional[str] = None
    default_engine: Optional[str] = None
    language: str = "en"


class VoiceProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    language: Optional[str] = None
    default_engine: Optional[str] = None


class VoiceProfileResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    voice_type: str
    preset_engine: Optional[str] = None
    preset_voice_id: Optional[str] = None
    design_prompt: Optional[str] = None
    default_engine: Optional[str] = None
    language: str
    sample_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Profile Samples ─────────────────────────────────────────────────────

class ProfileSampleUpdate(BaseModel):
    reference_text: str = Field(min_length=1)


class ProfileSampleResponse(BaseModel):
    id: str
    profile_id: str
    audio_path: str
    reference_text: str


# ── Audio Library ─────────────────────────────────────────────────────

class AudioLibraryEntryResponse(BaseModel):
    id: str
    name: str
    file_path: str
    category: str
    duration_seconds: Optional[float] = None
    source: str
    model: Optional[str] = None
    tags: Optional[list[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Templates ─────────────────────────────────────────────────────────

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    thumbnail_path: Optional[str] = None
    category: str
    is_builtin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Models ────────────────────────────────────────────────────────────

class ModelStatus(BaseModel):
    model_name: str
    display_name: str
    hf_repo_id: str
    pipeline_tag: str
    downloaded: bool
    downloading: bool
    size_mb: Optional[int] = None
    loaded: bool


class ModelStatusListResponse(BaseModel):
    models: list[ModelStatus]


# ── Health ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    app_name: str = "videogen-studio"
    version: str = "1.0.0"
    model_loaded: bool = False
    gpu_available: bool = False
    gpu_type: Optional[str] = None
    vram_used_mb: Optional[float] = None
    backend_type: Optional[str] = None
    backend_variant: Optional[str] = None
    gpu_compatibility_warning: Optional[str] = None


class DirectoryCheck(BaseModel):
    path: str
    exists: bool
    writable: bool
    error: Optional[str] = None


class FilesystemHealthResponse(BaseModel):
    healthy: bool
    disk_free_mb: Optional[float] = None
    disk_total_mb: Optional[float] = None
    directories: list[DirectoryCheck] = []


# ── Legacy VideoGen Models (restored for import compatibility) ─────────────

class GenerationRequest(BaseModel):
    profile_id: str
    text: str
    language: str = "en"
    seed: Optional[int] = None
    model_size: Optional[str] = None
    engine: Optional[str] = None
    instruct: Optional[str] = None
    personality: Optional[bool] = None
    max_chunk_chars: Optional[int] = None
    crossfade_ms: Optional[int] = None
    normalize: Optional[bool] = None
    effects_chain: Optional[list[dict]] = None


class GenerationResponse(BaseModel):
    id: str
    profile_id: str
    text: str
    language: str = "en"
    audio_path: Optional[str] = None
    duration: Optional[float] = None
    seed: Optional[int] = None
    instruct: Optional[str] = None
    engine: Optional[str] = None
    model_size: Optional[str] = None
    status: str = "completed"
    error: Optional[str] = None
    is_favorited: bool = False
    created_at: datetime
    versions: Optional[list["GenerationVersionResponse"]] = None
    active_version_id: Optional[str] = None


class GenerationVersionResponse(BaseModel):
    id: str
    generation_id: str
    label: str
    audio_path: str
    effects_chain: Optional[list[dict]] = None
    source_version_id: Optional[str] = None
    is_default: bool = False
    created_at: datetime


class HistoryQuery(BaseModel):
    profile_id: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0


class HistoryResponse(GenerationResponse):
    profile_name: str = ""


class HistoryListResponse(BaseModel):
    items: list[HistoryResponse]
    total: int = 0


class RefinementFlagsModel(BaseModel):
    smart_cleanup: bool = True
    self_correction: bool = True
    preserve_technical: bool = False


class CaptureResponse(BaseModel):
    id: str
    audio_path: str
    source: str = "file"
    language: Optional[str] = None
    duration_ms: Optional[int] = None
    transcript_raw: str = ""
    transcript_refined: Optional[str] = None
    stt_model: Optional[str] = None
    llm_model: Optional[str] = None
    refinement_flags: Optional[RefinementFlagsModel] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CaptureCreateResponse(CaptureResponse):
    auto_refine: bool = False
    allow_auto_paste: bool = True


class CaptureListResponse(BaseModel):
    items: list[CaptureResponse]
    total: int = 0


class StoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class StoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    item_count: int = 0


class StoryItemDetail(BaseModel):
    id: str
    story_id: str
    generation_id: str
    version_id: Optional[str] = None
    start_time_ms: int = 0
    track: int = 0
    trim_start_ms: int = 0
    trim_end_ms: int = 0
    created_at: datetime
    profile_id: str = ""
    profile_name: str = ""
    text: str = ""
    language: str = "en"
    audio_path: str = ""
    duration: float = 0.0
    seed: Optional[int] = None
    instruct: Optional[str] = None
    engine: Optional[str] = None
    volume: float = 1.0
    generation_created_at: Optional[datetime] = None
    versions: Optional[list[GenerationVersionResponse]] = None
    active_version_id: Optional[str] = None


class StoryDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: list[StoryItemDetail] = []


class EffectPresetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    effects_chain: list[dict] = []
    is_builtin: bool = False
    created_at: datetime
    updated_at: datetime


class EffectPresetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    effects_chain: list[dict] = []


class EffectPresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    effects_chain: Optional[list[dict]] = None


class EffectConfig(BaseModel):
    type: str
    enabled: bool = True
    params: dict[str, float] = {}


class AvailableEffect(BaseModel):
    type: str
    label: str
    description: str
    params: dict[str, "EffectParamDef"]


class EffectParamDef(BaseModel):
    default: float = 0.0
    min: float = 0.0
    max: float = 1.0
    step: float = 0.1
    description: str = ""


class AvailableEffectsResponse(BaseModel):
    effects: list[AvailableEffect] = []


class ApplyEffectsRequest(BaseModel):
    effects_chain: list[EffectConfig] = []
    source_version_id: Optional[str] = None
    label: Optional[str] = None
    set_as_default: bool = False


class MCPClientBindingResponse(BaseModel):
    client_id: str
    label: Optional[str] = None
    profile_id: Optional[str] = None
    default_engine: Optional[str] = None
    default_personality: bool = False
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MCPClientBindingUpsert(BaseModel):
    client_id: str
    label: Optional[str] = None
    profile_id: Optional[str] = None
    default_engine: Optional[str] = None
    default_personality: Optional[bool] = None


class AudioChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    device_ids: list[str] = []


class AudioChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    device_ids: Optional[list[str]] = None


class ChannelVoiceAssignment(BaseModel):
    profile_ids: list[str] = []


class ProfileChannelAssignment(BaseModel):
    channel_ids: list[str] = []


class AudioChannelResponse(BaseModel):
    id: str
    name: str
    is_default: bool = False
    device_ids: list[str] = []
    created_at: datetime


class CaptureSettingsResponse(BaseModel):
    stt_model: str = "turbo"
    language: str = "en"
    auto_refine: bool = False
    llm_model: str = "0.6B"
    smart_cleanup: bool = True
    self_correction: bool = True
    preserve_technical: bool = False
    allow_auto_paste: bool = True
    default_playback_voice_id: Optional[str] = None
    hotkey_enabled: bool = False
    chord_push_to_talk_keys: list[str] = []
    chord_toggle_to_talk_keys: list[str] = []


class GenerationSettingsResponse(BaseModel):
    max_chunk_chars: int = 1000
    crossfade_ms: int = 50
    normalize_audio: bool = True
    autoplay_on_generate: bool = True
    output_resolution: str = "1080p"
    output_fps: int = 30
    video_codec: str = "h264"
    max_render_duration_secs: int = 600


class ActiveTasksResponse(BaseModel):
    downloads: list[dict] = []
    generations: list[dict] = []


class StoryItemCreate(BaseModel):
    generation_id: str
    start_time_ms: int = 0
    track: int = 0


class StoryItemUpdateTime(BaseModel):
    generation_id: str
    start_time_ms: int


class StoryItemBatchUpdate(BaseModel):
    updates: list[StoryItemUpdateTime] = []


class StoryItemReorder(BaseModel):
    generation_ids: list[str] = []


class StoryItemMove(BaseModel):
    start_time_ms: int
    track: int


class StoryItemTrim(BaseModel):
    trim_start_ms: int = 0
    trim_end_ms: int = 0


class StoryItemSplit(BaseModel):
    split_time_ms: int


class StoryItemVolumeUpdate(BaseModel):
    volume: float


class StoryItemVersionUpdate(BaseModel):
    version_id: Optional[str] = None


# ── Additional models needed by legacy routes/services ─────────────────

class TranscriptionResponse(BaseModel):
    text: str
    duration: float = 0.0


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1)
    profile: str
    personality: Optional[bool] = None
    engine: Optional[str] = None
    model_size: Optional[str] = None


class LLMGenerateRequest(BaseModel):
    text: str = Field(min_length=1)
    model_size: Optional[str] = None
    system_prompt: Optional[str] = None


class LLMGenerateResponse(BaseModel):
    text: str
    model_size: str = ""


class ModelReadiness(BaseModel):
    ready: bool = False
    model_name: str = ""
    display_name: str = ""
    size: str = ""
    size_mb: Optional[float] = None


class ModelDownloadRequest(BaseModel):
    model_name: str


class ModelMigrateRequest(BaseModel):
    destination: str


class CaptureRefineRequest(BaseModel):
    flags: Optional[RefinementFlagsModel] = None
    model_size: Optional[str] = None


class CaptureRetranscribeRequest(BaseModel):
    model: Optional[str] = None
    language: Optional[str] = None


class CaptureReadinessResponse(BaseModel):
    stt: ModelReadiness
    llm: ModelReadiness


class CaptureSettingsUpdate(BaseModel):
    stt_model: Optional[str] = None
    language: Optional[str] = None
    auto_refine: Optional[bool] = None
    llm_model: Optional[str] = None
    smart_cleanup: Optional[bool] = None
    self_correction: Optional[bool] = None
    preserve_technical: Optional[bool] = None
    allow_auto_paste: Optional[bool] = None
    default_playback_voice_id: Optional[str] = None
    hotkey_enabled: Optional[bool] = None
    chord_push_to_talk_keys: Optional[list[str]] = None
    chord_toggle_to_talk_keys: Optional[list[str]] = None


class GenerationSettingsUpdate(BaseModel):
    max_chunk_chars: Optional[int] = None
    crossfade_ms: Optional[int] = None
    normalize_audio: Optional[bool] = None
    autoplay_on_generate: Optional[bool] = None
    output_resolution: Optional[str] = None
    output_fps: Optional[int] = None
    video_codec: Optional[str] = None
    max_render_duration_secs: Optional[int] = None


class PersonalityTextResponse(BaseModel):
    text: str
    model_size: str = ""


class ProfileEffectsUpdate(BaseModel):
    effects_chain: Optional[list[EffectConfig]] = None


class ActiveDownloadTask(BaseModel):
    model_name: str
    status: str = ""
    started_at: str = ""
    error: Optional[str] = None
    progress: Optional[float] = None
    current: Optional[int] = None
    total: Optional[int] = None
    filename: Optional[str] = None


class ActiveGenerationTask(BaseModel):
    task_id: str
    profile_id: str
    text_preview: str
    started_at: str = ""


class MCPClientBindingListResponse(BaseModel):
    items: list[MCPClientBindingResponse] = []
