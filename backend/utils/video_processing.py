"""Video processing helpers."""

import logging
from pathlib import Path
from backend.utils.ffmpeg import run_ffmpeg, probe_duration

logger = logging.getLogger(__name__)


def extract_last_frame(video_path: str, output_path: str) -> bool:
    """Seek to the end of the video and extract the final frame as an image.

    Uses FFmpeg for fast seek and frame extraction.
    """
    try:
        path = Path(video_path)
        if not path.exists():
            logger.error("Video file does not exist: %s", video_path)
            return False

        duration = probe_duration(path)
        if duration is None or duration <= 0:
            logger.warning("Could not determine duration for %s, seeking to 0", video_path)
            seek_time = 0.0
        else:
            # Seek 0.05 seconds before the end to guarantee a valid frame is captured.
            seek_time = max(0.0, duration - 0.05)

        # Build ffmpeg args (run_ffmpeg automatically adds 'ffmpeg' and '-y')
        args = [
            "-ss", f"{seek_time:.3f}",
            "-i", str(path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]

        res = run_ffmpeg(args)
        if res.returncode != 0:
            logger.error("FFmpeg frame extraction failed: %s", res.stderr)
            return False

        logger.info("Extracted last frame of %s to %s (seek time: %.3f)", video_path, output_path, seek_time)
        return True
    except Exception:
        logger.exception("Failed to extract final frame from %s", video_path)
        return False
