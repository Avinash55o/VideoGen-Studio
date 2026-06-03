"""
Platform detection for backend selection.
"""

import platform
from typing import Literal, Optional


def is_apple_silicon() -> bool:
    """
    Check if running on Apple Silicon (arm64 macOS).
    
    Returns:
        True if on Apple Silicon, False otherwise
    """
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def get_backend_type() -> Literal["mlx", "pytorch"]:
    """
    Detect the best backend for the current platform.

    Returns:
        "mlx" on Apple Silicon (if MLX is available and functional), "pytorch" otherwise
    """
    if is_apple_silicon():
        try:
            import mlx.core  # noqa: F401 — triggers native lib loading
            return "mlx"
        except (ImportError, OSError, RuntimeError):
            return "pytorch"
    return "pytorch"


def get_device() -> str:
    """Return the torch device string for video generation."""
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_vram_gb() -> Optional[float]:
    """Return available VRAM in GB, or None if not detectable."""
    import torch
    try:
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_mem / (1024**3)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            import psutil
            return psutil.virtual_memory().total / (1024**3) * 0.5
    except Exception:
        pass
    return None
