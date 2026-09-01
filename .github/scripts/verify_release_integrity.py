#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path.cwd(); EXPECTED_REPO=os.getenv("GITHUB_REPOSITORY"); EXPECTED_TAG=os.getenv("DPN_VERSION") or os.getenv("RELEASE_TAG"); EXPECTED_COMMIT=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
TOKEN_PATTERNS=(re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),re.compile(r"\bAKIA[0-9A-Z]{16}\b")); PRIVATE_KEY_MARKERS=("-----BEGIN "+"PRIVATE KEY-----","-----BEGIN RSA "+"PRIVATE KEY-----","-----BEGIN EC "+"PRIVATE KEY-----","-----BEGIN OPENSSH "+"PRIVATE KEY-----"); RECORDS=("SBOM.spdx.json","SBOM.cyclonedx.json","SOURCE_SHA256SUMS.txt","DEPENDENCY_INVENTORY.txt","SBOM_MANIFEST.txt","RELEASE_PROVENANCE.json","RELEASE_SHA256SUMS.txt")
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
 return h.hexdigest()
errors=[]
for name in RECORDS:
 if not (ROOT/name).is_file(): errors.append(f"missing release record: {name}")
if errors: print("\n".join(errors),file=sys.stderr); raise SystemExit(1)
manifest={}
for lineno,raw in enumerate((ROOT/"RELEASE_SHA256SUMS.txt").read_text(encoding="utf-8").splitlines(),1):
 if not raw.strip(): continue
 parts=raw.split("  ",1)
 if len(parts)!=2 or not re.fullmatch(r"[0-9a-f]{64}",parts[0]): errors.append(f"invalid release checksum manifest line {lineno}"); continue
 manifest[parts[1]]=parts[0]
for name in RECORDS[:-1]:
 if manifest.get(name)!=sha256(ROOT/name): errors.append(f"checksum coverage or digest mismatch for {name}")
try: provenance=json.loads((ROOT/"RELEASE_PROVENANCE.json").read_text(encoding="utf-8"))
except Exception as exc: errors.append(f"invalid RELEASE_PROVENANCE.json: {exc}"); provenance={}
subject=provenance.get("subject") if isinstance(provenance,dict) else None
if not isinstance(subject,dict): errors.append("provenance subject is missing")
else:
 if EXPECTED_REPO and subject.get("repository")!=EXPECTED_REPO: errors.append("provenance repository does not match GITHUB_REPOSITORY")
 if EXPECTED_TAG and subject.get("tag")!=EXPECTED_TAG: errors.append("provenance tag does not match release tag")
 if subject.get("commit")!=EXPECTED_COMMIT: errors.append("provenance commit does not match checked-out release commit")
material_map={item.get("name"):item.get("sha256") for item in provenance.get("materials",[]) if isinstance(item,dict)}
for name in RECORDS[:5]:
 if material_map.get(name)!=sha256(ROOT/name): errors.append(f"provenance material digest mismatch for {name}")
for name in RECORDS:
 text=(ROOT/name).read_text(encoding="utf-8",errors="replace")
 if any(marker in text for marker in PRIVATE_KEY_MARKERS): errors.append(f"private-key material detected in generated release record {name}")
 if any(pattern.search(text) for pattern in TOKEN_PATTERNS): errors.append(f"credential-like token detected in generated release record {name}")
if errors:
 for error in errors: print(f"ERROR: {error}",file=sys.stderr)
 raise SystemExit(1)
print(f"Release integrity PASS: {len(RECORDS)} records verified for commit {EXPECTED_COMMIT}")
