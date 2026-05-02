from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_backend_env(base_dir: Path) -> None:
    """Load backend env files with local-first precedence.

    Local development uses `backend/.env.local`.
    Server deployments can use `backend/.env`.
    """

    env_local = base_dir / ".env.local"
    env_file = base_dir / ".env"

    if env_local.exists():
        load_dotenv(env_local, override=False)
        return

    if env_file.exists():
        load_dotenv(env_file, override=False)
