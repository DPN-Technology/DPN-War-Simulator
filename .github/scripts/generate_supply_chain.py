#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.cwd()
REPO=os.getenv("GITHUB_REPOSITORY", ROOT.name)
PROJECT=REPO.split("/")[-1]
VERSION=os.getenv("DPN_VERSION") or os.getenv("VERSION") or "UNSPECIFIED"
COMMIT=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()

def tracked():
    raw=subprocess.check_output(["git","ls-files","-z"])
    return [p.decode("utf-8","surrogateescape") for p in raw.split(b"\0") if p]

def file_sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def add_dep(store,eco,name,req,src):
    name=name.strip(); req=req.strip() or "unspecified"
    if name: store[(eco.lower(),name.lower(),req,src)]={"ecosystem":eco,"name":name,"requirement":req,"source":src}

def deps_from(files):
    out={}
    for rel in files:
        p=ROOT/rel
        if p.name.startswith("requirements") and p.suffix==".txt":
            for raw in p.read_text(encoding="utf-8",errors="replace").splitlines():
                line=raw.split("#",1)[0].strip()
                if not line or line.startswith(("-r","--","git+","http://","https://")): continue
                m=re.match(r"^([A-Za-z0-9_.-]+(?:\[[^\]]+\])?)\s*(.*)$",line)
                if m: add_dep(out,"PyPI",m.group(1),m.group(2),rel)
        elif p.name=="package.json":
            try: data=json.loads(p.read_text(encoding="utf-8"))
            except Exception: continue
            for section in ("dependencies","devDependencies","optionalDependencies","peerDependencies"):
                for name,req in (data.get(section) or {}).items(): add_dep(out,"npm",name,str(req),f"{rel}:{section}")
        elif p.suffix in {".gradle",".kts"} or p.name in {"build.gradle","build.gradle.kts"}:
            text=p.read_text(encoding="utf-8",errors="replace")
            pat=r"""(?:implementation|api|classpath|testImplementation|androidTestImplementation|debugImplementation|releaseImplementation)\s*(?:\(\s*)?["']([^"'\n]+:[^"'\n]+:[^"'\n]+)["']"""
            for coord in re.findall(pat,text):
                parts=coord.split(":")
                if len(parts)>=3: add_dep(out,"Gradle/Maven",":".join(parts[:-1]),parts[-1],rel)
        elif p.name.lower()=="dockerfile" or p.name.lower().startswith("dockerfile."):
            for line in p.read_text(encoding="utf-8",errors="replace").splitlines():
                m=re.match(r"^\s*FROM\s+([^\s]+)",line,re.I)
                if m and m.group(1).lower()!="scratch":
                    image=m.group(1); name,sep,tag=image.partition(":")
                    add_dep(out,"OCI",name,tag if sep else "latest/unspecified",rel)
        elif rel.lower().startswith(".github/workflows/") and p.suffix in {".yml",".yaml"}:
            for line in p.read_text(encoding="utf-8",errors="replace").splitlines():
                m=re.search(r"\buses:\s*([^\s#]+)",line)
                if m and not m.group(1).startswith("./"):
                    name,sep,ver=m.group(1).partition("@")
                    add_dep(out,"GitHub Actions",name,ver if sep else "unspecified",rel)
    return sorted(out.values(),key=lambda d:(d["ecosystem"].lower(),d["name"].lower(),d["source"]))

files=tracked()
manifest=[]
for rel in files:
    p=ROOT/rel
    if p.is_file(): manifest.append(f"{file_sha(p)}  {rel}")
Path("SOURCE_SHA256SUMS.txt").write_text("\n".join(manifest)+"\n",encoding="utf-8")

deps=deps_from(files)
lines=["ecosystem\tname\trequirement\tsource"]+[f'{d["ecosystem"]}\t{d["name"]}\t{d["requirement"]}\t{d["source"]}' for d in deps]
Path("DEPENDENCY_INVENTORY.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")

root="SPDXRef-RootPackage"
packages=[{"name":PROJECT,"SPDXID":root,"versionInfo":VERSION,"downloadLocation":f"https://github.com/{REPO}","filesAnalyzed":False,"licenseConcluded":"NOASSERTION","licenseDeclared":"NOASSERTION","copyrightText":"Copyright DPN Technology","supplier":"Organization: DPN Technology","packageComment":f"Source commit: {COMMIT}"}]
rels=[{"spdxElementId":"SPDXRef-DOCUMENT","relationshipType":"DESCRIBES","relatedSpdxElement":root}]
for d in deps:
    key=f'{d["ecosystem"]}:{d["name"]}:{d["requirement"]}:{d["source"]}'
    sid="SPDXRef-"+hashlib.sha1(key.encode()).hexdigest()[:16]
    packages.append({"name":d["name"],"SPDXID":sid,"downloadLocation":"NOASSERTION","filesAnalyzed":False,"licenseConcluded":"NOASSERTION","licenseDeclared":"NOASSERTION","copyrightText":"NOASSERTION","packageComment":f'Declared via {d["ecosystem"]}; requirement {d["requirement"]}; source {d["source"]}'})
    rels.append({"spdxElementId":root,"relationshipType":"DEPENDS_ON","relatedSpdxElement":sid})
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
ns=f"https://github.com/{REPO}/releases/tag/{VERSION}#spdx-{uuid.uuid5(uuid.NAMESPACE_URL,f'{REPO}:{VERSION}:{COMMIT}')}"
doc={"spdxVersion":"SPDX-2.3","dataLicense":"CC0-1.0","SPDXID":"SPDXRef-DOCUMENT","name":f"{PROJECT}-{VERSION}-SBOM","documentNamespace":ns,"creationInfo":{"created":now,"creators":["Organization: DPN Technology","Tool: DPN Supply Chain Generator 1.0"]},"packages":packages,"relationships":rels,"annotations":[{"annotationDate":now,"annotationType":"OTHER","annotator":"Organization: DPN Technology","comment":f"Tracked source files hashed: {len(manifest)}; declared dependencies inventoried: {len(deps)}; commit: {COMMIT}"}]}
Path("SBOM.spdx.json").write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(f"SBOM dependencies: {len(deps)}; tracked files: {len(manifest)}; commit: {COMMIT}")
