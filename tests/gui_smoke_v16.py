from types import SimpleNamespace
from warsim.seamless3d import SeamlessOpenWorld3DApp, SHIP_HATCH_WORLD
from warsim.openworld import CAMERA_HEIGHT, LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, CONNECTORS
from warsim.survivability import apply_impact

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# D remains movement-only in the upgraded physical world.
app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
app._key_up(SimpleNamespace(keysym='d'))

# Animated hatch: logical state changes immediately, visible door eases over time.
key='ISLAND_PORT'; layer,lx,ly=SHIP_HATCH_WORLD[key]
app.x,app.y=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly; app.z=LAYERS[layer].floor_z+CAMERA_HEIGHT
app.shipboard.hatches[key]=True; app.physical_world.hatch_fraction[key]=1.0
app._interact(); assert app.shipboard.hatches[key] is False
app._update(.15); frac=app.physical_world.hatch_fraction[key]; assert 0.0 < frac < 1.0

# Storm/rain rendering on the flight deck.
app.physical_world.weather_mode='STORM'; app.physics.sea_state=7
for _ in range(8): app._update(.3)
app.x,app.y=SHIP_ORIGIN_X+30,SHIP_ORIGIN_Y+14; app.z=LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); storm_items=len(app.canvas.find_all()); assert storm_items>110

# Local structural casualty must become visually represented as fire/smoke/flooding geometry.
apply_impact(app.survivability,'TORPEDO',82,zone='STBD_MACH',side='STARBOARD')
app.x,app.y=SHIP_ORIGIN_X+41,SHIP_ORIGIN_Y+18; app.z=LAYERS['ENGINEERING'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); damage_items=len(app.canvas.find_all()); assert damage_items>100

# Radar animation advances, and seamless ladder travel visibly occupies an intermediate Z.
start_angle=app.physical_world.radar_angle_deg; app._update(.4); assert app.physical_world.radar_angle_deg!=start_angle
conn=CONNECTORS['ENG_HANGAR_FWD']; app.x,app.y=conn.x,conn.y; app.z=conn.from_z+CAMERA_HEIGHT
app._start_vertical_travel(conn,conn.to_z); start_z=app.z
app.vertical_travel['start']-=app.vertical_travel['duration']*.5
app._update(.01); assert min(start_z,conn.to_z+CAMERA_HEIGHT)<app.z<max(start_z,conn.to_z+CAMERA_HEIGHT)

# Persistence includes v1.6 environment state.
app._sync_physics_profile(); assert app.profile.physical_world_snapshot['weather_mode']=='STORM'
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V16_PASS')
