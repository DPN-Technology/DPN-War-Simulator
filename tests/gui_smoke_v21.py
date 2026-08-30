from types import SimpleNamespace

from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT, LAYERS

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
app.profile.rank_index=max(app.profile.rank_index,12)

# Permanent D regression still applies on foot in the expanded battlefield world.
app.x,app.y,app.z=33,139,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
start=(app.x,app.y); app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
for _ in range(4): app._update(.04)
app._key_up(SimpleNamespace(keysym='d')); assert (app.x,app.y)!=start

# Start battalion field operation at its physical maneuver-area entry.
entry=next(p for p in all_static_interactions() if p.action=='land_battlefield')
app.x,app.y,app.z=entry.x,entry.y,entry.floor_z+CAMERA_HEIGHT; app._interact()
assert app.land_warfare.active

# Open tactical board, select/command a unit and request finite artillery.
app._key_down(SimpleNamespace(keysym='f8')); app._key_up(SimpleNamespace(keysym='f8')); assert app.overlay=='land_command'
app._overlay_key('2'); assert app.land_warfare.selected_unit.order=='ADVANCE'
shells=next(iter(app.land_warfare.artillery.values())).shells
app._overlay_key('a'); assert next(iter(app.land_warfare.artillery.values())).shells<shells
app._overlay_key('e'); assert app.overlay is None

# Enter a battlefield vehicle at the physical armored staging point.
armor=next(p for p in all_static_interactions() if p.action=='land_armor')
app.x,app.y,app.z=armor.x,armor.y,armor.floor_z+CAMERA_HEIGHT; app._interact()
assert app.land_warfare.player_vehicle_key
v=app.land_warfare.vehicles[app.land_warfare.player_vehicle_key]
app._key_down(SimpleNamespace(keysym='i')); app._key_up(SimpleNamespace(keysym='i')); assert v.engine_running
app._key_down(SimpleNamespace(keysym='w')); app._key_up(SimpleNamespace(keysym='w')); v.brake=False
# D must steer right only: no overlay opens.
h0=v.heading_deg; app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None
for _ in range(15): app._update(.05)
app._key_up(SimpleNamespace(keysym='d')); assert v.distance_m>0 and v.heading_deg!=h0 and app.overlay is None

# Battlefield weapon consumes ammunition and acts on selected contact.
before=(v.main_ammo,v.mg_ammo,app.land_warfare.selected_contact.strength)
app._key_down(SimpleNamespace(keysym='space')); app._key_up(SimpleNamespace(keysym='space'))
after=(v.main_ammo,v.mg_ammo,app.land_warfare.selected_contact.strength)
assert after!=before

# Render the expanded battlefield entities / sectors and the command overlay.
app.x,app.y,app.z=34,148,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>100
app.overlay='land_command'; app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>35

# Persist v2.1 state.
app._sync_physics_profile(); assert 'sectors' in app.profile.land_warfare_snapshot

app.destroyed=True; app.destroy(); print('GUI_SMOKE_V21_PASS')
