from types import SimpleNamespace
from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT, LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y
from warsim.air_wing import advance_air_wing

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# Regression: D must only enter movement state and never pop Damage Control.
app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
app._key_up(SimpleNamespace(keysym='d')); assert 'd' not in app.keys

# Physical Air Group planning room.
plot=next(p for p in all_static_interactions() if p.action=='air_wing_console')
app.x,app.y,app.z=plot.x,plot.y,plot.floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='air_wing_console'
app._overlay_key('p'); assert len(app.air_wing.missions)==1
app.physics.moored=False; app.physics.speed_knots=18; app.shipboard.enterprise.wind_over_deck=18
app._overlay_key('l')
m=app.air_wing.missions[app.air_wing.selected_mission]; assert m.status=='AIRBORNE'
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>50
app._overlay_key('e')

# Advanced flight-deck exterior must render detailed geometry + aircraft.
app.x,app.y=SHIP_ORIGIN_X+35,SHIP_ORIGIN_Y+12
app.z=LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>80

# Mission returns and can recover through the same persistent state.
advance_air_wing(app.air_wing,m.planned_minutes*.75*60,app.physics.east_nm,app.physics.north_nm,app.physics.sea_state)
assert m.status=='RETURNING'
app.overlay='air_wing_console'; app._overlay_key('r'); assert m.status=='COMPLETE'
app._overlay_key('e')

# Engineering interior detail pass should substantially populate the scene.
app.x,app.y=SHIP_ORIGIN_X+33,SHIP_ORIGIN_Y+10
app.z=LAYERS['ENGINEERING'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>80

# Persistence includes the new air-wing state.
app._sync_physics_profile(); assert 'squadrons' in app.profile.air_wing_snapshot
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V15_PASS')
