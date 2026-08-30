from pathlib import Path
from types import SimpleNamespace
import json
from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import LAYERS,CAMERA_HEIGHT,SHIP_ORIGIN_X,SHIP_ORIGIN_Y
from warsim.config import VERSION
root=Path(__file__).resolve().parents[1]
assert VERSION=='2.7.0'
m=json.loads((root/'assets3d'/'Enterprise_CV6_1942_Midway_manifest.json').read_text())
assert m['geometry']['editable_objects']>=1400 and m['geometry']['triangles']>=40000
assert len(m['exterior_modules'])==4 and len(m['interior_modules'])==4
app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
app.x=SHIP_ORIGIN_X+166; app.y=SHIP_ORIGIN_Y+15; app.z=LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT; app.yaw=.15; app.pitch=-.03
app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys; app._key_up(SimpleNamespace(keysym='d'))
faces=[]; app._collect_detail_geometry(faces,1280,720); assert len(faces)>80
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>130
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V27_PASS')
