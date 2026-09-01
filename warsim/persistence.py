from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

from .models import CareerProfile
from .config import SAVE_SCHEMA


class SaveCorruptionError(RuntimeError):
    """Raised when a career save exists but cannot be trusted or decoded."""


def save_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        path = base / "WarSimulator"
    else:
        path = Path.home() / ".war_simulator"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def save_path() -> Path:
    return save_dir() / "career.json"


def backup_path(path: Path | None = None) -> Path:
    path = Path(path or save_path())
    return path.with_name(path.name + ".bak")


def _reject_unsafe_path(path: Path, label: str) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink():
        raise SaveCorruptionError(f"Refusing symlinked {label}: {path.name}")
    if not path.is_file():
        raise SaveCorruptionError(f"{label} is not a regular file: {path.name}")


def _fsync_dir(directory: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _reject_unsafe_path(path, "career save")
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp")
    fd = None
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb", closefd=True) as handle:
            fd = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
        _fsync_dir(path.parent)
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _decode_payload(raw: str, source: Path) -> dict:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise SaveCorruptionError(f"Career save is malformed JSON: {source.name}") from exc
    if not isinstance(payload, dict):
        raise SaveCorruptionError(f"Career save root must be an object: {source.name}")
    if payload.get("schema") != SAVE_SCHEMA:
        raise SaveCorruptionError(
            f"Career save schema is unsupported or missing: {payload.get('schema')!r}"
        )
    profile_data = payload.get("profile")
    if not isinstance(profile_data, dict):
        raise SaveCorruptionError("Career save profile payload is missing or invalid")
    if "name" in profile_data and not isinstance(profile_data["name"], str):
        raise SaveCorruptionError("Career save profile name has an invalid type")
    return payload


def _read_payload(path: Path) -> dict:
    _reject_unsafe_path(path, "career save")
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SaveCorruptionError(f"Career save could not be read: {path.name}") from exc
    if not raw.strip():
        raise SaveCorruptionError(f"Career save is empty: {path.name}")
    return _decode_payload(raw, path)


def _profile_from_payload(payload: dict) -> CareerProfile:
    try:
        return CareerProfile.from_dict(payload["profile"])
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise SaveCorruptionError("Career save profile data failed validation") from exc


def save_profile(profile: CareerProfile, path: Path | None = None) -> Path:
    path = Path(path or save_path())
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = {"schema": SAVE_SCHEMA, "profile": profile.to_dict()}
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")

    # Preserve the previous *verified* save before replacing it. A corrupt live
    # save is never copied over the known-good recovery copy.
    if path.exists() or path.is_symlink():
        previous = _read_payload(path)
        _profile_from_payload(previous)
        previous_bytes = path.read_bytes()
        _atomic_write(backup_path(path), previous_bytes)

    _atomic_write(path, encoded)
    # Read-after-write verification prevents acknowledging an incomplete save.
    verified = _read_payload(path)
    _profile_from_payload(verified)
    return path


def load_profile(path: Path | None = None) -> CareerProfile | None:
    path = Path(path or save_path())
    if not path.exists() and not path.is_symlink():
        return None
    return _profile_from_payload(_read_payload(path))


def recover_profile(path: Path | None = None) -> CareerProfile:
    """Restore the last verified career save and return the recovered profile."""
    path = Path(path or save_path())
    recovery = backup_path(path)
    if not recovery.exists() and not recovery.is_symlink():
        raise SaveCorruptionError("No verified career recovery copy is available")
    payload = _read_payload(recovery)
    profile = _profile_from_payload(payload)
    recovery_bytes = recovery.read_bytes()
    _atomic_write(path, recovery_bytes)
    # Verify the replacement using the exact same production loader path.
    restored = load_profile(path)
    if restored is None:
        raise SaveCorruptionError("Recovered career save unexpectedly disappeared")
    return profile
