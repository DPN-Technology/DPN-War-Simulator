from warsim.seamless3d import SeamlessOpenWorld3DApp, SHIP_EQUIPMENT_WORLD
from warsim.openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, CAMERA_HEIGHT, all_static_interactions
from warsim.survivability import apply_impact

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# Physical Damage Control Central opens the structural survivability board.
layer,lx,ly=SHIP_EQUIPMENT_WORLD['DC_BOARD']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='survivability_dc'
app._overlay_key('t')
assert any(c.breach_area_m2>0 for c in app.survivability.compartments.values())
app._overlay_key('f'); app._overlay_key('p'); app._overlay_key('e'); assert app.overlay is None

# Physical boundary board operates the casualty model.
layer,lx,ly=SHIP_EQUIPMENT_WORLD['BOUNDARY_BOARD']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='survivability_boundaries'
app._overlay_key('b'); app._overlay_key('e')

# Medical receiving station treats casualties.
apply_impact(app.survivability,'DIVE_BOMB',85,zone='HANGAR_MID')
layer,lx,ly=SHIP_EQUIPMENT_WORLD['MEDICAL_STAGING']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='survivability_medical'
before=sum(c.wounded for c in app.survivability.compartments.values())
app._overlay_key('t')
after=sum(c.wounded for c in app.survivability.compartments.values())
assert after<before
app._overlay_key('e')

# Severe flooding affects vessel attitude in the live renderer.
app.survivability.compartments['STBD_VOID'].flooding=100
app.survivability.compartments['PORT_MACH'].flooding=75
for _ in range(8): app._update(.1)
app.x,app.y,app.z=SHIP_ORIGIN_X+30,SHIP_ORIGIN_Y+12,LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>35
assert abs(app.survivability.list_deg)>.2 or abs(app.survivability.trim_deg)>.2

# Abandon ship from DC and physically muster in the same seamless world.
app.overlay='survivability_dc'; app._overlay_key('a'); assert app.survivability.abandon_ship_ordered
app.overlay=None
muster=next(p for p in all_static_interactions() if p.action=='survival_muster')
app.x,app.y,app.z=muster.x,muster.y,muster.floor_z+CAMERA_HEIGHT
before=app.survivability.evacuation_progress_pct
app._interact(); assert app.survivability.evacuation_progress_pct>before

app.destroyed=True; app.destroy(); print('GUI_SMOKE_V11_PASS')
