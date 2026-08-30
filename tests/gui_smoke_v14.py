from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT
from warsim.campaign import create_campaign

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
app.profile.rank_index=12
app.campaign=create_campaign(app.physics.east_nm,app.physics.north_nm)

# Physical Bridge campaign planning plot.
plot=next(p for p in all_static_interactions() if p.action=='campaign_console')
app.x,app.y,app.z=plot.x,plot.y,plot.floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='campaign_console'
app._overlay_key('3'); assert app.campaign.time_scale==15
app._overlay_key('a'); assert app.campaign.active_mission is not None
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>30
app._overlay_key('e')

# Campaign remains active while player leaves the planning plot; no scene/world load occurred.
assert app.campaign.active_mission.status=='ACTIVE'

# Physical Hangar-deck logistics board and finite port service.
log=next(p for p in all_static_interactions() if p.action=='campaign_logistics')
app.x,app.y,app.z=log.x,log.y,log.floor_z+CAMERA_HEIGHT
app.physics.east_nm=0.0; app.physics.north_nm=0.0; app.physics.speed_knots=0.0
app.campaign.selected_base_index=0
before=app.campaign.bases['HOME'].fuel
app._interact(); assert app.overlay=='campaign_logistics'
app._overlay_key('s'); assert app.campaign.port_services==1
assert app.campaign.bases['HOME'].fuel < before
app._overlay_key('e')

# Make a convoy nearby so the exterior renderer includes persistent campaign traffic.
cv=app.campaign.convoys['CONVOY_A']; cv.east_nm=app.physics.east_nm+2.0; cv.north_nm=app.physics.north_nm+1.0
# move to flight deck for external view
app.x,app.y=64+20,8+10; from warsim.openworld import LAYERS
app.z=LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>35

# Persistence stores campaign network and active mission.
app._sync_physics_profile(); assert 'bases' in app.profile.campaign_snapshot
assert app.profile.campaign_snapshot['time_scale']==15
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V14_PASS')
