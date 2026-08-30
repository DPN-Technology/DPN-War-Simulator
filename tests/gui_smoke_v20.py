from types import SimpleNamespace

from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT, LAYERS

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# Permanent D-key regression on foot before combat.
start=(app.x,app.y); app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
for _ in range(4): app._update(.04)
app._key_up(SimpleNamespace(keysym='d')); assert (app.x,app.y)!=start

# Physically issue infantry equipment and start the combined-arms exercise at the range entry.
armory=next(p for p in all_static_interactions() if p.action=='infantry_armory')
app.x,app.y,app.z=armory.x,armory.y,armory.floor_z+CAMERA_HEIGHT; app._interact()
entry=next(p for p in all_static_interactions() if p.action=='infantry_range')
app.x,app.y,app.z=entry.x,entry.y,entry.floor_z+CAMERA_HEIGHT; app._interact()
assert app.ground_combat.engagement_active and app.ground_combat.player.active and app.overlay is None

# D remains strafe-right in live infantry mode and does not open any screen.
start=(app.x,app.y); app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None
for _ in range(5): app._update(.04)
app._key_up(SimpleNamespace(keysym='d')); assert (app.x,app.y)!=start

# Put the first training contact in a visible firing lane and exercise infantry controls.
contact=app.ground_combat.selected_contact; contact.x,contact.y=app.x+8,app.y; contact.cover_pct=0; contact.confidence=100; contact.identified=True
app.yaw=0.0
app._key_down(SimpleNamespace(keysym='c')); app._key_up(SimpleNamespace(keysym='c'))
app._key_down(SimpleNamespace(keysym='space')); app._key_up(SimpleNamespace(keysym='space'))
assert app.ground_combat.player.shots_fired>=1
app._key_down(SimpleNamespace(keysym='j')); app._key_up(SimpleNamespace(keysym='j'))
assert app.ground_combat.selected_order!='FOLLOW'

# Finite combined-arms support.
app.ground_ops.air_support_points=30
app.ground_combat.support_cooldown=0; app._key_down(SimpleNamespace(keysym='5')); app._key_up(SimpleNamespace(keysym='5'))
assert app.ground_combat.supports_called>=1 and app.ground_ops.air_support_points<30
app.ground_combat.support_cooldown=0; app._key_down(SimpleNamespace(keysym='6')); app._key_up(SimpleNamespace(keysym='6'))
assert app.ground_combat.supports_called>=2

# Render the expanded village, friendly fireteam, contact, weapon HUD and objective beacon.
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>90
# Open the new fireteam status overlay and prove it renders, then return to live first-person mode.
app._key_down(SimpleNamespace(keysym='g')); app._key_up(SimpleNamespace(keysym='g')); assert app.overlay=='ground_combat_console'
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>30
app._overlay_key('e'); assert app.overlay is None

# Combined-arms state is part of the career snapshot.
app._sync_physics_profile(); assert 'squad' in app.profile.ground_combat_snapshot

app.destroyed=True; app.destroy(); print('GUI_SMOKE_V20_PASS')
