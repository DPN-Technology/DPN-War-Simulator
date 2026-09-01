from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def probe(repo: Path, save: Path, expected_name: str, expected_xp: int) -> subprocess.CompletedProcess[str]:
    code = """
import sys
from pathlib import Path
import main
from warsim.persistence import load_profile
p = load_profile(Path(sys.argv[1]))
assert p is not None
assert p.name == sys.argv[2]
assert p.xp == int(sys.argv[3])
print('War Simulator runtime persistence probe OK')
"""
    return subprocess.run(
        [sys.executable, "-c", code, str(save), expected_name, str(expected_xp)],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=45,
        check=False,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )


def main() -> int:
    repo = Path.cwd().resolve()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    from warsim.config import SAVE_SCHEMA
    from warsim.models import CareerProfile
    from warsim.persistence import (
        SaveCorruptionError,
        backup_path,
        load_profile,
        recover_profile,
        save_profile,
    )

    with tempfile.TemporaryDirectory(prefix="dpn-war-phase3-") as td:
        root = Path(td)
        save = root / "career.json"

        # First-run must remain valid: absence means no career yet, not corruption.
        require(load_profile(save) is None, "Missing career save no longer behaves as first-run")

        marker_one = f"Phase3-{secrets.token_hex(8)}"
        marker_two = f"Phase3-{secrets.token_hex(8)}"
        save_profile(CareerProfile(name=marker_one, xp=310), save)
        save_profile(CareerProfile(name=marker_two, xp=620), save)

        current = load_profile(save)
        require(current is not None and current.name == marker_two and current.xp == 620, "Current career did not round-trip")
        recovery = backup_path(save)
        require(recovery.exists(), "Second verified save did not create recovery copy")
        recovery_payload = json.loads(recovery.read_text(encoding="utf-8"))
        require(recovery_payload.get("schema") == SAVE_SCHEMA, "Recovery copy schema is invalid")
        require(recovery_payload["profile"]["name"] == marker_one, "Recovery copy is not the prior verified career")

        restarted = probe(repo, save, marker_two, 620)
        require(restarted.returncode == 0, f"Headless game restart/import probe failed:\n{restarted.stdout}")

        # A damaged career must fail closed and must not be rewritten as a fresh save.
        corrupt = b"phase3-corrupt-war-save-" + secrets.token_bytes(96)
        save.write_bytes(corrupt)
        corrupt_hash = sha256(save)
        try:
            load_profile(save)
        except SaveCorruptionError:
            pass
        else:
            raise AssertionError("Corrupt career save was silently treated as a missing save")
        require(sha256(save) == corrupt_hash, "Corrupt career save was modified while loading")

        failed = probe(repo, save, marker_two, 620)
        require(failed.returncode != 0, "Game startup probe accepted corrupt career data")
        require(sha256(save) == corrupt_hash, "Failed game startup mutated corrupt career data")

        # A damaged recovery copy must fail without touching the damaged live save.
        good_recovery = recovery.read_bytes()
        recovery.write_bytes(b"phase3-invalid-recovery-" + secrets.token_bytes(64))
        try:
            recover_profile(save)
        except SaveCorruptionError:
            pass
        else:
            raise AssertionError("Invalid recovery copy was accepted")
        require(sha256(save) == corrupt_hash, "Rejected recovery attempt modified live career data")

        recovery.write_bytes(good_recovery)
        recovered = recover_profile(save)
        require(recovered.name == marker_one and recovered.xp == 310, "Verified recovery returned wrong career state")
        require(load_profile(save).name == marker_one, "Recovered career was not installed as live state")

        final_restart = probe(repo, save, marker_one, 310)
        require(final_restart.returncode == 0, f"Recovered career failed game restart/import probe:\n{final_restart.stdout}")

        # No temporary atomic-write debris should remain beside the career file.
        debris = [p.name for p in root.iterdir() if p.name.endswith(".tmp")]
        require(not debris, f"Persistence left temporary write debris: {debris}")

        print("DPN War Simulator Phase 3 runtime and recovery assurance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
