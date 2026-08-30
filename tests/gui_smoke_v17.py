from types import SimpleNamespace
from warsim.seamless3d import SeamlessOpenWorld3DApp, SHIP_HATCH_WORLD
from warsim.openworld import CAMERA_HEIGHT, LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y
from warsim.air_wing import plan_selected_mission

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# D remains pure strafe in the walking world.
app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys; app._key_up(SimpleNamespace(keysym='d'))

# Additional v1.7 compartment door is physical/animated.
key='HANGAR_FWD'; layer,lx,ly=SHIP_HATCH_WORLD[key]
app.x,app.y=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly; app.z=LAYERS[layer].floor_z+CAMERA_HEIGHT
app.shipboard.hatches[key]=True; app.physical_world.hatch_fraction[key]=1.0
app._interact(); assert app.shipboard.hatches[key] is False
app._update(.15); assert 0 < app.physical_world.hatch_fraction[key] < 1
app.shipboard.hatches[key]=True

# Create a flight-deck spotted individual aircraft and physically enter it.
ok,msg=plan_selected_mission(app.air_wing,app.physics.east_nm,app.physics.north_nm,app.physics.heading_deg); assert ok,msg
ac=next(a for a in app.air_wing.aircraft.values() if a.deck=='FLIGHT' and a.status=='SPOTTED')
pose=app._aircraft_world_pose(ac); assert pose
app.x,app.y,zz=pose; app.z=zz+CAMERA_HEIGHT
app._interact(); assert app.flight.active and app.flight.aircraft_key==ac.key

# Engine start, brakes off, throttle up, then actual carrier takeoff.
for keypress in ('i','b'):
    app._key_down(SimpleNamespace(keysym=keypress)); app._key_up(SimpleNamespace(keysym=keypress))
for _ in range(10):
    app._key_down(SimpleNamespace(keysym='w')); app._key_up(SimpleNamespace(keysym='w'))
for _ in range(160):
    app._update(.05)
    if not app.flight.on_deck: break
assert not app.flight.on_deck and app.flight.takeoffs>=1
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>45

# Recover with a valid training approach and exit back onto the seamless Flight Deck.
app.flight.east_nm=app.physics.east_nm+.02; app.flight.north_nm=app.physics.north_nm
app.flight.altitude_ft=75; app.flight.airspeed_knots=72; app.flight.heading_deg=app.physics.heading_deg
app.flight.gear_down=True; app.flight.flaps_down=True; app.shipboard.enterprise.wind_over_deck=18
app._key_down(SimpleNamespace(keysym='l')); app._key_up(SimpleNamespace(keysym='l')); assert app.flight.on_deck
app.flight.airspeed_knots=0
app._key_down(SimpleNamespace(keysym='e')); app._key_up(SimpleNamespace(keysym='e')); assert not app.flight.active

# Electrical casualty visual layer and articulated crew render without breaking the same world.
app.x,app.y=SHIP_ORIGIN_X+33,SHIP_ORIGIN_Y+10; app.z=LAYERS['ENGINEERING'].floor_z+CAMERA_HEIGHT
app.shipboard.equipment_runtime['LOAD_BOARD'].fault='SIMULATED BUS ARC'
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>90

app._sync_physics_profile(); assert 'flight_ops_snapshot' in app.profile.to_dict(); assert app.profile.carrier_takeoffs>=1
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V17_PASS')
