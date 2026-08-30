from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
app.profile.rank_index=12  # ship-command-watch authority

# Move physically to Task Force Tactical Plot.
plot=next(p for p in all_static_interactions() if p.action=='fleet_console')
app.x,app.y,app.z=plot.x,plot.y,plot.floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='fleet_console'
app._overlay_key('3'); assert app.task_force.formation=='DISPERSED'
app._overlay_key('t'); assert app.task_force.training_problem_active
app._overlay_key('r'); assert app.task_force.radio_silence
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>30

# Let fleet AI and sensors run.
app.overlay=None
for _ in range(8): app._update(1.0)
assert any(c.detected for c in app.task_force.contacts.values())

# Reopen physical Signal Bridge and issue an escort engagement once a contact is tracked.
sig=next(p for p in all_static_interactions() if p.action=='fleet_signal')
app.x,app.y,app.z=sig.x,sig.y,sig.floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='fleet_signal'
# select a detected contact
vals=[c for c in app.task_force.contacts.values() if c.health_pct>0]
for i,c in enumerate(vals):
    if c.detected:
        app.task_force.selected_contact_index=i; break
before=app.task_force.selected_contact.health_pct
app._overlay_key('a')
assert app.task_force.selected_contact.health_pct < before
app._overlay_key('e')

# Fleet logistics board can start replenishment; position selected ship close and keep speed safe.
log=next(p for p in all_static_interactions() if p.action=='fleet_logistics')
app.x,app.y,app.z=log.x,log.y,log.floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='fleet_logistics'
app.physics.speed_knots=10
v=app.task_force.selected_friendly
v.east_nm=app.physics.east_nm+0.1; v.north_nm=app.physics.north_nm; v.fuel_pct=45
app._overlay_key('p'); assert app.task_force.logistics.transfer_in_progress
app.overlay=None
for _ in range(30): app._update(1.0)
assert not app.task_force.logistics.transfer_in_progress
assert v.fuel_pct>45

# Exterior render includes task-force entities and save snapshot contains them.
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>35
app._sync_physics_profile(); assert 'friendly' in app.profile.task_force_snapshot
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V13_PASS')
