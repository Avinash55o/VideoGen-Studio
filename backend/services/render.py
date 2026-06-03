"""Render pipeline — composes project clips into a final video using FFmpeg."""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .. import config
from ..database.models import Clip, Project, Render, uuid7
from ..utils.ffmpeg import get_ffmpeg_path, get_ffprobe_path, is_ffmpeg_available, run_ffmpeg

logger = logging.getLogger(__name__)


class RenderError(Exception):
    pass


def _seconds(ms: int) -> float:
    return ms / 1000.0


def _format_ffmpeg_time(ms: int) -> str:
    total_sec = ms / 1000.0
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _make_trim_filter(duration_s: float) -> str:
    return f"atrim=duration={duration_s:.3f},asetpts=N/SR/TB"


def _fade_filter(fade_in_ms: int, fade_out_ms: int, duration_s: float) -> str:
    filters = []
    if fade_in_ms > 0:
        filters.append(f"afade=t=in:d={_seconds(fade_in_ms):.3f}")
    if fade_out_ms > 0:
        filters.append(f"afade=t=out:st={duration_s - _seconds(fade_out_ms):.3f}:d={_seconds(fade_out_ms):.3f}")
    return ",".join(filters) if filters else "anull"


def _volume_filter(volume: float) -> str:
    if abs(volume - 1.0) < 0.01:
        return "anull"
    return f"volume={volume:.2f}"


async def render_project(project_id: str, db_bind, format: str = "mp4",
                         resolution: Optional[str] = None) -> str:
    """Run the full render pipeline for a project. Returns the render ID."""
    import asyncio
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SASession

    if not is_ffmpeg_available():
        raise RenderError("ffmpeg is not installed — render pipeline unavailable")

    engine = create_engine(db_bind.url)

    with SASession(bind=engine) as db:
        project = db.query(Project).filter(
            Project.id == project_id, Project.deleted_at.is_(None)
        ).first()
        if not project:
            raise RenderError("Project not found")

        clips = (
            db.query(Clip)
            .filter(Clip.project_id == project_id)
            .order_by(Clip.track, Clip.start_time_ms)
            .all()
        )

        if not clips:
            raise RenderError("No clips in project — nothing to render")

        project.render_status = "rendering"
        project.render_progress = 0.0
        db.commit()

    render_id = uuid7()
    renders_dir = config.get_renders_dir()
    output_filename = f"{render_id}.{format}"
    output_path = str(renders_dir / output_filename)

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, _do_render, project, clips, output_path, format, resolution, render_id
        )

        with SASession(bind=engine) as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.render_status = "complete"
                project.render_progress = 1.0
                project.output_path = output_path

                file_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
                render_record = Render(
                    id=render_id,
                    project_id=project_id,
                    file_path=output_path,
                    format=format,
                    resolution=resolution or f"{project.width}x{project.height}",
                    duration_seconds=project.duration_seconds,
                    file_size_bytes=file_size,
                    status="complete",
                )
                db.add(render_record)
                db.commit()

        return render_id

    except Exception as exc:
        logger.exception("Render failed for project %s", project_id)
        with SASession(bind=engine) as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.render_status = "failed"
                project.render_progress = 0.0
                db.commit()
        raise RenderError(str(exc)) from exc


def _do_render(project, clips, output_path: str, fmt: str,
               resolution: Optional[str], render_id: str):
    """Synchronous FFmpeg compose pipeline."""
    project_dir = config.get_projects_dir() / project.id
    project_dir.mkdir(parents=True, exist_ok=True)

    width, height = project.width, project.height
    if resolution and "x" in resolution:
        parts = resolution.split("x")
        width, height = int(parts[0]), int(parts[1])

    fps = project.fps
    duration_s = project.duration_seconds
    total_ms = int(duration_s * 1000)

    video_clips = [c for c in clips if c.clip_type == "video" and c.source_path]
    audio_clips = [c for c in clips if c.clip_type in ("voiceover", "music") and c.source_path]

    _update_progress(project.id, 0.1)

    with tempfile.TemporaryDirectory(prefix=f"render_{render_id}_") as tmpdir:
        tmp = Path(tmpdir)

        # ── Step 1: extract trimmed audio segments ─────────────────
        audio_segments = []
        for i, clip in enumerate(audio_clips):
            seg = _extract_audio_segment(clip, tmp, i)
            if seg:
                audio_segments.append(seg)

        _update_progress(project.id, 0.3)

        # ── Step 2: build FFmpeg filter_complex for audio ──────────
        filter_chain: list[str] = []
        audio_inputs: list[Path] = []
        amix_inputs: list[str] = []

        for idx, seg in enumerate(audio_segments):
            label = f"a{idx}"
            audio_inputs.append(seg.path)
            delay_ms = seg.start_ms
            trim_dur = _seconds(seg.duration_ms)
            vol_filter = _volume_filter(seg.volume)

            fade = _fade_filter(seg.fade_in_ms, seg.fade_out_ms, trim_dur) if seg.fade_in_ms > 0 or seg.fade_out_ms > 0 else "anull"

            if delay_ms > 0:
                delay_sec = _seconds(delay_ms)
                filt = (
                    f"[{idx}:a]{vol_filter},{fade},adelay={delay_sec:.3f}|{delay_sec:.3f}[{label}]"
                )
            else:
                filt = f"[{idx}:a]{vol_filter},{fade}[{label}]"
            filter_chain.append(filt)
            amix_inputs.append(f"[{label}]")

        # ── Step 3: video track ────────────────────────────────────
        if video_clips:
            vid_concat = _make_video_concat(video_clips, duration_s, tmp, fps, width, height)
            video_input = vid_concat.path
            video_label = vid_concat.label
            video_filter_parts = [f"[{video_label}]"]

            for seg_idx, vid_seg in enumerate(vid_concat.segments):
                v_label = f"v{seg_idx}"
                video_filter_parts.append(f"[{seg_idx}:v]")
                # trim video + set PTS
                trim_dur_v = _seconds(vid_seg.duration_ms)
                trim_filter = f"trim=duration={trim_dur_v:.3f},setpts=PTS-STARTPTS"
                # scale if resolution differs
                scale = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
                # fade in/out
                fade_v = ""
                if vid_seg.fade_in_ms > 0:
                    fade_v += f"fade=t=in:d={_seconds(vid_seg.fade_in_ms):.3f}"
                if vid_seg.fade_out_ms > 0:
                    fi = _seconds(vid_seg.fade_in_ms)
                    fo = _seconds(vid_seg.fade_out_ms)
                    fo_start = trim_dur_v - fo
                    if fade_v:
                        fade_v += f",fade=t=out:st={fo_start:.3f}:d={fo:.3f}"
                    else:
                        fade_v = f"fade=t=out:st={fo_start:.3f}:d={fo:.3f}"
                if not fade_v:
                    fade_v = "null"

                video_filter_parts.append(f"{trim_filter},{scale},{fade_v}[{v_label}]")
        else:
            video_filter_parts = ["color=c=black:s={}x{}:d={:.3f}:r={}[vid]".format(width, height, duration_s, fps)]
            video_label = "vid"
            video_filter_parts = [f"[{video_label}]"]

        # ── Step 4: combine filters ────────────────────────────────
        if audio_inputs:
            amix_str = f"{''.join(amix_inputs)}amix=inputs={len(amix_inputs)}:normalize=0[aout]"
            filter_complex = ";".join(filter_chain + [amix_str])
        else:
            filter_complex = "anullsrc=r=44100:cl=stereo[aout]"

        # Combine video and audio
        if video_clips:
            final_video_label = f"[v{video_clips[0].clip_type}]"  # placeholder
            filter_complex = ";".join(video_filter_parts) + ";" + filter_complex

        filter_complex = ";".join(video_filter_parts + filter_chain + [amix_str]) if audio_inputs else ";".join(video_filter_parts)

        _update_progress(project.id, 0.5)

        # ── Step 5: build input args ───────────────────────────────
        input_args = []
        for seg in audio_segments:
            input_args += ["-i", str(seg.path)]
        for seg in (vid_concat.segments if video_clips else []):
            input_args += ["-i", str(seg.path)]

        codec_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "22"]
        if fmt == "webm":
            codec_args = ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0"]
        elif fmt == "mov":
            codec_args = ["-c:v", "prores_ks", "-profile:v", "3"]

        # Determine final video label
        final_video_label = video_filter_parts[-1].split("[")[1].split("]")[0] if "[" in video_filter_parts[-1] else "vid"

        ffmpeg_args = input_args + [
            "-filter_complex", filter_complex,
            "-map", f"[{final_video_label}]",
            "-map", "[aout]",
            *codec_args,
            "-c:a", "aac" if fmt != "webm" else "libopus",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            output_path,
        ]

        try:
            run_ffmpeg(ffmpeg_args, timeout=3600)
        except subprocess.TimeoutExpired:
            raise RenderError("Render timed out after 60 minutes")
        except RuntimeError as e:
            raise RenderError(str(e))

        _update_progress(project.id, 1.0)


def _update_progress(project_id: str, progress: float):
    """Update project render progress in DB."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session as SASession
        from ..config import get_db_path

        db_path = get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")
        with SASession(bind=engine) as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.render_progress = progress
                db.commit()
    except Exception:
        logger.exception("Failed to update render progress")


def _extract_audio_segment(clip, tmpdir: Path, idx: int):
    """Extract a trimmed, volume-adjusted audio segment using FFmpeg."""
    source = Path(clip.source_path)
    if not source.exists():
        logger.warning("Clip %s source not found: %s", clip.id, clip.source_path)
        return None

    duration_ms = clip.end_time_ms - clip.start_time_ms
    if duration_ms <= 0:
        return None

    seg_path = tmpdir / f"audio_{idx}.wav"

    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return None

    cmd = [
        ffmpeg, "-y",
        "-ss", _format_ffmpeg_time(clip.start_time_ms),
        "-i", str(source),
        "-t", _seconds(duration_ms),
        "-af", _volume_filter(clip.volume),
        "-ar", "44100",
        "-ac", "2",
        str(seg_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
    except subprocess.CalledProcessError:
        logger.exception("Failed to extract audio segment for clip %s", clip.id)
        return None

    return _AudioSegment(
        path=seg_path,
        start_ms=clip.start_time_ms,
        duration_ms=duration_ms,
        volume=clip.volume,
        fade_in_ms=clip.fade_in_ms,
        fade_out_ms=clip.fade_out_ms,
    )


class _AudioSegment:
    def __init__(self, path: Path, start_ms: int, duration_ms: int,
                 volume: float, fade_in_ms: int, fade_out_ms: int):
        self.path = path
        self.start_ms = start_ms
        self.duration_ms = duration_ms
        self.volume = volume
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms


class _VideoConcatResult:
    def __init__(self):
        self.segments: list[_VideoSegment] = []
        self.path = None
        self.label = "vid"


class _VideoSegment:
    def __init__(self, path: Path, duration_ms: int, fade_in_ms: int, fade_out_ms: int):
        self.path = path
        self.duration_ms = duration_ms
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms


def _make_video_concat(video_clips, total_duration_s: float,
                       tmpdir: Path, fps: int, width: int, height: int) -> _VideoConcatResult:
    """Extract video segments and create concat demuxer."""
    result = _VideoConcatResult()

    for i, clip in enumerate(video_clips):
        source = Path(clip.source_path)
        if not source.exists():
            continue

        duration_ms = clip.end_time_ms - clip.start_time_ms
        if duration_ms <= 0:
            continue

        seg_path = tmpdir / f"video_{i}.mp4"

        ffmpeg = get_ffmpeg_path()
        if not ffmpeg:
            continue

        # Trim + scale + pad to project resolution
        scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        trim_dur = _seconds(duration_ms)

        cmd = [
            ffmpeg, "-y",
            "-ss", _format_ffmpeg_time(clip.start_time_ms),
            "-i", str(source),
            "-t", f"{trim_dur:.3f}",
            "-vf", f"trim=duration={trim_dur:.3f},setpts=PTS-STARTPTS,{scale_filter}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-an",
            str(seg_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
        except subprocess.CalledProcessError:
            logger.exception("Failed to extract video segment for clip %s", clip.id)
            continue

        result.segments.append(_VideoSegment(
            path=seg_path,
            duration_ms=duration_ms,
            fade_in_ms=clip.fade_in_ms,
            fade_out_ms=clip.fade_out_ms,
        ))

    if not result.segments:
        return result

    # ── Build concat demuxer file ─────────────────────────────────
    concat_path = tmpdir / "concat.txt"
    with open(concat_path, "w") as f:
        for i, seg in enumerate(result.segments):
            # Check if it has video
            seg_path = Path(seg.path) if isinstance(seg.path, str) else seg.path
            rel = seg_path.relative_to(tmpdir)
            f.write(f"file '{rel}'\n")

    result.path = concat_path
    result.label = "vid_concat"

    # ── Produce concatenated video ─────────────────────────────────
    concat_output = tmpdir / "merged_video.mp4"
    ffmpeg = get_ffmpeg_path()
    if ffmpeg:
        cmd = [
            ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-an",
            str(concat_output),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
        except subprocess.CalledProcessError:
            logger.exception("Failed to concat video segments")
            return result

        result.path = concat_output
        result.label = "0"

        # Replace raw segments with single concat output
        result.segments = [_VideoSegment(
            path=concat_output,
            duration_ms=sum(s.duration_ms for s in result.segments),
            fade_in_ms=0,
            fade_out_ms=0,
        )]

    return result
