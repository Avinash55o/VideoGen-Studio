"""FFmpeg binary detection and common subprocess helpers."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_FFMPEG_PATH: Optional[str] = None
_FFPROBE_PATH: Optional[str] = None


def _find_binary(name: str) -> Optional[str]:
    which = shutil.which(name)
    if which:
        return which
    common_dirs = [
        "/usr/local/bin",
        "/usr/bin",
        "/opt/homebrew/bin",
        "/usr/local/opt/ffmpeg/bin",
        "C:\\ffmpeg\\bin",
        str(Path.home() / "ffmpeg" / "bin"),
    ]
    for d in common_dirs:
        candidate = Path(d) / (name + (".exe" if __import__("sys").platform == "win32" else ""))
        if candidate.exists():
            return str(candidate)
    return None


def get_ffmpeg_path() -> Optional[str]:
    global _FFMPEG_PATH
    if _FFMPEG_PATH is None:
        _FFMPEG_PATH = _find_binary("ffmpeg")
        if _FFMPEG_PATH:
            logger.info("Found ffmpeg at %s", _FFMPEG_PATH)
        else:
            logger.warning("ffmpeg not found on system — render pipeline unavailable")
    return _FFMPEG_PATH


def get_ffprobe_path() -> Optional[str]:
    global _FFPROBE_PATH
    if _FFPROBE_PATH is None:
        _FFPROBE_PATH = _find_binary("ffprobe")
        if _FFPROBE_PATH:
            logger.info("Found ffprobe at %s", _FFPROBE_PATH)
        else:
            logger.warning("ffprobe not found on system")
    return _FFPROBE_PATH


def is_ffmpeg_available() -> bool:
    return get_ffmpeg_path() is not None


def probe_duration(path: Path) -> Optional[float]:
    ffprobe = get_ffprobe_path()
    if not ffprobe:
        return None
    try:
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip()) if result.stdout.strip() else None
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return None


def run_ffmpeg(args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("ffmpeg not available")
    cmd = [ffmpeg, "-y", *args]
    logger.debug("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
