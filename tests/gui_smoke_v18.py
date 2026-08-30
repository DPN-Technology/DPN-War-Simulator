from types import SimpleNamespace

from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import CAMERA_HEIGHT, LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y
from warsim.air_wing import plan_selected_mission
from warsim.flight_combat import selected_contact, apply_aircraft_damage

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# Walking D remains right-strafe only.
app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys; app._key_up(SimpleNamespace(keysym='d'))

# Plan fighter CAP and physically enter an individually tracked aircraft.
app.air_wing.selected_squadron='VF6'; app.air_wing.selected_mission_type='CAP'
ok,msg=plan_selected_mission(app.air_wing,app.physics.east_nm,app.physics.north_nm,app.physics.heading_deg); assert ok,msg
ac=next(a for a in app.air_wing.aircraft.values() if a.deck=='FLIGHT' and a.status=='SPOTTED' and a.squadron=='VF6')
pose=app._aircraft_world_pose(ac); assert pose
app.x,app.y,zz=pose; app.z=zz+CAMERA_HEIGHT
app._interact(); assert app.flight.active and app.flight.aircraft_key==ac.key

# Launch from the moving carrier.
for keypress in ('i','b'):
    app._key_down(SimpleNamespace(keysym=keypress)); app._key_up(SimpleNamespace(keysym=keypress))
for _ in range(10):
    app._key_down(SimpleNamespace(keysym='w')); app._key_up(SimpleNamespace(keysym='w'))
for _ in range(170):
    app._update(.05)
    if not app.flight.on_deck: break
assert not app.flight.on_deck and app.flight_combat.active_sortie

# Put selected training fighter directly ahead, render it, and fire guns.
t=next(c for c in app.flight_combat.contacts.values() if c.kind=='AIR'); app.flight_combat.selected_contact=t.key
t.east_nm=app.flight.east_nm+.20; t.north_nm=app.flight.north_nm; t.altitude_ft=app.flight.altitude_ft; t.health=10; app.flight.heading_deg=90
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>55
app._key_down(SimpleNamespace(keysym='space')); app._key_up(SimpleNamespace(keysym='space'))
assert app.flight_combat.aerial_victories>=1 and not t.active

# Radio/nav controls and visible aircraft damage state.
app._key_down(SimpleNamespace(keysym='q')); app._key_up(SimpleNamespace(keysym='q'))
app._key_down(SimpleNamespace(keysym='m')); app._key_up(SimpleNamespace(keysym='m'))
apply_aircraft_damage(app.flight_combat,app.flight,18,'GUI smoke training hit')
app._render(); app.update_idletasks(); assert app.flight.airframe_health<100

# Bail out, then fast-forward rescue clock and verify return to Sickbay/open world.
app.flight.altitude_ft=1800
app._key_down(SimpleNamespace(keysym='x')); app._key_up(SimpleNamespace(keysym='x'))
assert not app.flight.active and app.overlay=='pilot_survival' and app.flight_combat.rescue_pending
app.flight_combat.rescue_seconds=24.9
app._update(.2)
assert app.flight_combat.pilot_safe and app.overlay is None
assert abs(app.z-(LAYERS['LOWER'].floor_z+CAMERA_HEIGHT))<.01

app._sync_physics_profile(); d=app.profile.to_dict(); assert 'flight_combat_snapshot' in d; assert app.profile.aerial_victories>=1; assert app.profile.pilot_rescues>=1
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V18_PASS')
