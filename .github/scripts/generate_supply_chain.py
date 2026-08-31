#!/usr/bin/env python3
"""Generate DPN Technology release supply-chain records using only the standard library."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
REPO = os.getenv("GITHUB_REPOSITORY", ROOT.name)
PROJECT = REPO.split("/")[-1]
VERSION = os.getenv("DPN_VERSION") or os.getenv("VERSION") or "UNSPECIFIED"
COMMIT = os.getenv("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def tracked_files() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"])
    return [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_dep(items: dict, ecosystem: str, name: str, requirement: str, source: str) -> None:
    name = name.strip()
    requirement = requirement.strip()
    if not name:
        return
    key = (ecosystem.lower(), name.lower(), requirement, source)
    items[key] = {
        "ecosystem": ecosystem,
        "name": name,
        "requirement": requirement or "unspecified",
        "source": source,
    }


def parse_dependencies(files: list[str]) -> list[dict]:
    deps: dict[tuple, dict] = {}

    for rel in files:
        path = ROOT / rel
        lower = rel.lower()

        if path.name.startswith("requirements") and path.suffix == ".txt":
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for raw in lines:
                line = raw.split("#", 1)[0].strip()
                if not line or line.startswith(("-r", "--", "git+", "http://", "https://")):
                    continue
                m = re.match(r"^([A-Za-z0-9_.-]+(?:\[[^\]]+\])?)\s*(.*)$", line)
                if m:
                    add_dep(deps, "PyPI", m.group(1), m.group(2) or "unspecified", rel)

        elif path.name == "package.json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                for name, req in (data.get(section) or {}).items():
                    add_dep(deps, "npm", name, str(req), f"{rel}:{section}")

        elif path.suffix in {".gradle", ".kts"} or path.name in {"build.gradle", "build.gradle.kts"}:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            pattern = r"""(?:implementation|api|classpath|testImplementation|androidTestImplementation|debugImplementation|releaseImplementation)\s*(?:\(\s*)?["']([^"'\n]+:[^"'\n]+:[^"'\n]+)["']"""
            for coord in re.findall(pattern, text):
                parts = coord.split(":")
                if len(parts) >= 3:
                    add_dep(deps, "Gradle/Maven", ":".join(parts[:-1]), parts[-1], rel)

        elif path.name.lower() == "dockerfile" or path.name.lower().startswith("dockerfile."):
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line in lines:
                m = re.match(r"^\s*FROM\s+([^\s]+)", line, flags=re.I)
                if m:
                    image = m.group(1)
                    if image.lower() != "scratch":
                        name, sep, tag = image.partition(":")
                        add_dep(deps, "OCI", name, tag if sep else "latest/unspecified", rel)

        elif lower.startswith(".github/workflows/") and path.suffix in {".yml", ".yaml"}:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line in lines:
                m = re.search(r"\buses:\s*([^\s#]+)", line)
                if m:
                    ref = m.group(1)
                    if ref.startswith("./"):
                        continue
                    name, sep, ver = ref.partition("@")
                    add_dep(deps, "GitHub Actions", name, ver if sep else "unspecified", rel)

    return sorted(deps.values(), key=lambda d: (d["ecosystem"].lower(), d["name"].lower(), d["source"]))


def spdx_id(key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"SPDXRef-{digest}"


files = tracked_files()
manifest_lines = []
for rel in files:
    path = ROOT / rel
    if path.is_file():
        manifest_lines.append(f"{sha256_file(path)}  {rel}")
Path("SOURCE_SHA256SUMS.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

deps = parse_dependencies(files)
inventory = ["ecosystem\tname\trequirement\tsource"]
inventory.extend(f'{d["ecosystem"]}\t{d["name"]}\t{d["requirement"]}\t{d["source"]}' for d in deps)
Path("DEPENDENCY_INVENTORY.txt").write_text("\n".join(inventory) + "\n", encoding="utf-8")

root_id = "SPDXRef-RootPackage"
namespace_seed = f"{REPO}:{VERSION}:{COMMIT}"
namespace = f"https://github.com/{REPO}/releases/tag/{VERSION}#spdx-{uuid.uuid5(uuid.NAMESPACE_URL, namespace_seed)}"
packages = [{
    "name": PROJECT,
    "SPDXID": root_id,
    "versionInfo": VERSION,
    "downloadLocation": f"https://github.com/{REPO}",
    "filesAnalyzed": False,
    "licenseConcluded": "NOASSERTION",
    "licenseDeclared": "NOASSERTION",
    "copyrightText": "Copyright DPN Technology",
    "supplier": "Organization: DPN Technology",
    "packageComment": f"Source commit: {COMMIT}",
}]
relationships = [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": root_id}]

for dep in deps:
    key = f'{dep["ecosystem"]}:{dep["name"]}:{dep["requirement"]}:{dep["source"]}'
    dep_id = spdx_id(key)
    packages.append({
        "name": dep["name"],
        "SPDXID": dep_id,
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
        "packageComment": f'Declared via {dep["ecosystem"]}; requirement {dep["requirement"]}; source {dep["source"]}',
    })
    relationships.append({"spdxElementId": root_id, "relationshipType": "DEPENDS_ON", "relatedSpdxElement": dep_id})

spdx = {
    "spdxVersion": "SPDX-2.3",
    "dataLicense": "CC0-1.0",
    "SPDXID": "SPDXRef-DOCUMENT",
    "name": f"{PROJECT}-{VERSION}-SBOM",
    "documentNamespace": namespace,
    "creationInfo": {
        "created": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "creators": ["Organization: DPN Technology", "Tool: DPN Supply Chain Generator 1.0"],
    },
    "packages": packages,
    "relationships": relationships,
    "annotations": [{
        "annotationDate": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "annotationType": "OTHER",
        "annotator": "Organization: DPN Technology",
        "comment": f"Tracked source files hashed: {len(manifest_lines)}; declared dependencies inventoried: {len(deps)}; commit: {COMMIT}",
    }],
}
Path("SBOM.spdx.json").write_text(json.dumps(spdx, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"Generated SBOM.spdx.json with {len(deps)} declared dependencies.")
print(f"Generated SOURCE_SHA256SUMS.txt with {len(manifest_lines)} tracked files.")
print("Generated DEPENDENCY_INVENTORY.txt.")
