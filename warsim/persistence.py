from __future__ import annotations
import json
import os
from pathlib import Path
from .models import CareerProfile
from .config import SAVE_SCHEMA


def save_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        path = base / "WarSimulator"
    else:
        path = Path.home() / ".war_simulator"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_path() -> Path:
    return save_dir() / "career.json"


def save_profile(profile: CareerProfile, path: Path | None = None) -> Path:
    path = path or save_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": SAVE_SCHEMA, "profile": profile.to_dict()}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def load_profile(path: Path | None = None) -> CareerProfile | None:
    path = path or save_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return CareerProfile.from_dict(payload.get("profile", {}))
    except Exception:
        return None
