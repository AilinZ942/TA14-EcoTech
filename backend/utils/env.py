from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_backend_env(base_dir: Path) -> None:
    """Load the repository root `.env` file if it exists."""

    root_env_file = base_dir / ".env"
    if root_env_file.exists():
        load_dotenv(root_env_file, override=False)
