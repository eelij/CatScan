from __future__ import annotations

from pathlib import Path


def get_workspace_path(sb3_path: Path) -> Path:
    return sb3_path.parent / (sb3_path.name + ".catscan")


def get_backups_path(sb3_path: Path) -> Path:
    return get_workspace_path(sb3_path) / "backups"


def get_scripts_path(sb3_path: Path) -> Path:
    return get_workspace_path(sb3_path) / "scripts"


def get_exports_path(sb3_path: Path) -> Path:
    return get_workspace_path(sb3_path) / "exports"


def ensure_workspace(sb3_path: Path) -> None:
    ws = get_workspace_path(sb3_path)
    ws.mkdir(parents=True, exist_ok=True)
