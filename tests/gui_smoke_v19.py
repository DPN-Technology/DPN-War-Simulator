from types import SimpleNamespace

from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT, LAYERS

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# Permanent regression: D is movement/steering input, never a surprise panel in normal world play.
app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys; app._key_up(SimpleNamespace(keysym='d'))

# Walk to the new expeditionary operations district and open the physical ground board.
ops=next(p for p in all_static_interactions() if p.action=='ground_console')
app.x,app.y,app.z=ops.x,ops.y,ops.floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='ground_console'
app.profile.rank_index=12  # training smoke has command authority
app._overlay_key('tab') # landing mission
app._overlay_key('a'); assert app.ground_ops.active_mission is not None
app._overlay_key('j')
app._overlay_key('l')
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>65
app._overlay_key('e')

# Physical motor-pool vehicle: enter, start, release brake, accelerate and steer right with D.
motor=next(p for p in all_static_interactions() if p.action=='ground_motor')
app.x,app.y,app.z=motor.x,motor.y,motor.floor_z+CAMERA_HEIGHT
app._interact(); assert app.ground_ops.drive.active
app._key_down(SimpleNamespace(keysym='i')); app._key_up(SimpleNamespace(keysym='i'))
app._key_down(SimpleNamespace(keysym='b')); app._key_up(SimpleNamespace(keysym='b'))
for _ in range(5):
    app._key_down(SimpleNamespace(keysym='w')); app._key_up(SimpleNamespace(keysym='w'))
start=(app.x,app.y); app._key_down(SimpleNamespace(keysym='d'))
for _ in range(24): app._update(.05)
app._key_up(SimpleNamespace(keysym='d'))
assert app.overlay is None and app.ground_ops.drive.distance_m>0 and (app.x,app.y)!=start
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>70

# Stop and exit back into the same continuous first-person shore world.
app.ground_ops.drive.speed_mps=0; app.ground_ops.drive.throttle=0; app.ground_ops.drive.brake=True
app._key_down(SimpleNamespace(keysym='e')); app._key_up(SimpleNamespace(keysym='e'))
assert not app.ground_ops.drive.active and abs(app.z-(LAYERS['BASE'].floor_z+CAMERA_HEIGHT))<.01

# Ground state is part of career persistence.
app._sync_physics_profile(); assert 'units' in app.profile.ground_ops_snapshot; assert app.profile.ground_vehicle_distance_m>0
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V19_PASS')
