from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs"/"evidence"/"runtime"
OUT.mkdir(parents=True,exist_ok=True)
ARTIFACTS=[]

def settle(app,seconds=1.2):
    end=time.time()+seconds
    while time.time()<end:
        app.update_idletasks()
        app.update()
        time.sleep(0.05)

def capture(file_name,label):
    target=OUT/file_name
    subprocess.run(["import","-window","root",str(target)],check=True)
    ARTIFACTS.append({"file":file_name,"label":label,"viewport":os.environ.get("CAPTURE_VIEWPORT","1600x1000")})

from warsim.seamless3d import SeamlessOpenWorld3DApp

app=SeamlessOpenWorld3DApp()
app.geometry("1440x900+0+0")
settle(app,1.5)
capture("war-simulator-open-world.png","Seamless Open World")

for world,file_name,label in [
    ("HUB","war-simulator-training-hub.png","Naval Training & Career Center"),
    ("ENTERPRISE","war-simulator-enterprise.png","USS Enterprise CV-6"),
    ("BRIDGE","war-simulator-bridge.png","3D Bridge Practical")
]:
    app._enter_world(world)
    settle(app,1.2)
    capture(file_name,label)

manifest={
    "schemaVersion":1,
    "product":"DPN War Simulator",
    "repository":"DPN-War-Simulator",
    "generatedAt":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    "sourceCommit":os.environ.get("GITHUB_SHA","local"),
    "evidenceType":"actual-rendered-ui",
    "dataBoundary":"Captured from the real Tk seamless 3D simulation client in a fresh isolated HOME. Training/simulation state is local game state and must not be interpreted as real military operations or historical telemetry.",
    "artifacts":ARTIFACTS
}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
app.destroy()
print(f"Captured {len(ARTIFACTS)} War Simulator runtime view(s).")
