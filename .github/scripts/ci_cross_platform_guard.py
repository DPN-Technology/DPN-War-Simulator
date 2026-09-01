from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SENSITIVE = re.compile(
    r"(^|/)\.env$|(^|/)(vault|master)[^/]*\.key$|(^|/)FIRST_RUN_LOGIN\.txt$|"
    r"(^|/)data/.*\.(sqlite|sqlite3|db|enc)$|(^|/)backups/",
    re.IGNORECASE,
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def reject_sensitive_state() -> None:
    offenders = [path for path in tracked_files() if SENSITIVE.search(path)]
    if offenders:
        print("Sensitive/runtime files must not be tracked:", file=sys.stderr)
        for path in offenders:
            print(path, file=sys.stderr)
        raise SystemExit(1)


def verify_entrypoints() -> None:
    required = [ROOT / "main.py", ROOT / "WarSimulator.pyw", ROOT / "warsim"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required simulation entrypoints: " + ", ".join(missing))


def main() -> None:
    reject_sensitive_state()
    verify_entrypoints()
    print("War Simulator portable Phase 4 guard passed")


if __name__ == "__main__":
    main()
