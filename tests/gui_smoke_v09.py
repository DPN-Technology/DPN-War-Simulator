from warsim.seamless3d import SeamlessOpenWorld3DApp, SHIP_EQUIPMENT_WORLD
from warsim.openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, CAMERA_HEIGHT, all_static_interactions
from warsim.ship_physics import set_engine_order, set_rudder, advance_ship_physics

app=SeamlessOpenWorld3DApp()
app.geometry('1280x720')
app.update_idletasks(); app.update(); app.overlay=None

# Cast off at physical sea-detail station.
mooring=next(p for p in all_static_interactions() if p.key=='SHIP_MOORING')
app.x,app.y,app.z=mooring.x,mooring.y,mooring.floor_z+CAMERA_HEIGHT
app._interact()
assert not app.physics.moored
assert app._gangway_transition_blocked(65.0,63.0,29.0)

# Physical helm opens live ship control and changes rudder.
layer,lx,ly=SHIP_EQUIPMENT_WORLD['HELM']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='helm_physics'
app._overlay_key('right'); assert app.physics.rudder_deg>0
app._overlay_key('e'); assert app.overlay is None

# Engine telegraph drives continuous physics.
layer,lx,ly=SHIP_EQUIPMENT_WORLD['ENGINE_TELEGRAPH']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='engine_physics'
app._overlay_key('4'); assert app.physics.engine_order==1.0
app._overlay_key('e')
for _ in range(1800): advance_ship_physics(app.physics,.05)
assert app.physics.speed_knots>4
start_h=app.physics.heading_deg
set_rudder(app.physics,30)
for _ in range(800): advance_ship_physics(app.physics,.05)
assert abs(((app.physics.heading_deg-start_h+180)%360)-180)>1

# Underway exterior renders and navigation board is usable.
app.x,app.y,app.z=SHIP_ORIGIN_X+20,SHIP_ORIGIN_Y+10,LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>30
app.overlay='navigation'; app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>35

app.destroyed=True; app.destroy()
print('GUI_SMOKE_V09_PASS')
