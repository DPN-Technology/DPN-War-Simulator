#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.cwd(); REPO=os.getenv("GITHUB_REPOSITORY",ROOT.name); TAG=os.getenv("DPN_VERSION") or os.getenv("RELEASE_TAG") or "UNSPECIFIED"; RUN_ID=os.getenv("GITHUB_RUN_ID","local"); RUN_ATTEMPT=os.getenv("GITHUB_RUN_ATTEMPT","1"); WORKFLOW=os.getenv("GITHUB_WORKFLOW","Supply Chain"); ACTOR=os.getenv("GITHUB_ACTOR","local"); SERVER=os.getenv("GITHUB_SERVER_URL","https://github.com"); COMMIT=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(); ASSETS=["SBOM.spdx.json","SBOM.cyclonedx.json","SOURCE_SHA256SUMS.txt","DEPENDENCY_INVENTORY.txt","SBOM_MANIFEST.txt"]
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
 return h.hexdigest()
materials=[]
for name in ASSETS:
 p=ROOT/name
 if not p.is_file(): raise SystemExit(f"missing required release record: {name}")
 materials.append({"name":name,"sha256":sha256(p),"size":p.stat().st_size})
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"); prov={"schema":"https://dpntechnology.com/schemas/release-provenance/v1","subject":{"repository":REPO,"tag":TAG,"commit":COMMIT},"builder":{"platform":"GitHub Actions","workflow":WORKFLOW,"run_id":RUN_ID,"run_attempt":RUN_ATTEMPT,"actor":ACTOR,"run_url":f"{SERVER}/{REPO}/actions/runs/{RUN_ID}" if RUN_ID!="local" else "local"},"buildType":"dpn.release-integrity.v1","invocation":{"event":os.getenv("GITHUB_EVENT_NAME","local"),"ref":os.getenv("GITHUB_REF","local")},"metadata":{"generated_utc":now,"reproducible_source_commit":COMMIT},"materials":materials}
Path("RELEASE_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8"); names=ASSETS+["RELEASE_PROVENANCE.json"]; Path("RELEASE_SHA256SUMS.txt").write_text("\n".join(f"{sha256(ROOT/name)}  {name}" for name in names)+"\n",encoding="utf-8"); print(f"Release provenance created for {REPO}@{TAG} commit {COMMIT}; assets: {len(names)}")
