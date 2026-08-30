from types import SimpleNamespace

from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT, LAYERS

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
app.profile.rank_index=max(app.profile.rank_index,12)

# Permanent D regression applies inside the new strategic district too.
app.x,app.y,app.z=33,192,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
start=(app.x,app.y); app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
for _ in range(4): app._update(.04)
app._key_up(SimpleNamespace(keysym='d')); assert (app.x,app.y)!=start and app.overlay is None

# Physical front-line entry starts the persistent strategic campaign.
entry=next(p for p in all_static_interactions() if p.action=='strategic_front')
app.x,app.y,app.z=entry.x,entry.y,entry.floor_z+CAMERA_HEIGHT; app._interact(); assert app.strategic_war.active

# Physical theater HQ opens the strategic command board.
hq=next(p for p in all_static_interactions() if p.action=='strategic_command')
app.x,app.y,app.z=hq.x,hq.y,hq.floor_z+CAMERA_HEIGHT; app._interact(); assert app.overlay=='strategic_command'
# reconnaissance, operation acceptance and attack order
app._overlay_key('r'); assert app.strategic_war.recon_reports>=1
app._overlay_key('a'); assert app.strategic_war.selected_operation.status=='ACTIVE'
app._overlay_key('3'); assert app.strategic_war.selected_formation.order=='ATTACK'
# strategic artillery consumes battalion artillery shells
shells=next(iter(app.land_warfare.artillery.values())).shells
app._overlay_key('i'); assert next(iter(app.land_warfare.artillery.values())).shells<shells
app._overlay_key('e'); assert app.overlay is None

# Run the world long enough for operational AI to tick, then render front-line entities.
for _ in range(10): app._update(.25)
app.x,app.y,app.z=34,208,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>100
app.overlay='strategic_command'; app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>40

# Persist v2.2 state.
app._sync_physics_profile(); assert 'sectors' in app.profile.strategic_war_snapshot

app.destroyed=True; app.destroy(); print('GUI_SMOKE_V22_PASS')
