from warsim.seamless3d import SeamlessOpenWorld3DApp, SHIP_EQUIPMENT_WORLD
from warsim.openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, CAMERA_HEIGHT
from warsim.survivability import apply_impact

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None

# Give the smoke-test profile junior-officer authority so command orders can be exercised.
app.profile.rank_index=9  # Ensign -> department-watch authority in v1.2 training model

# Physical Bridge command desk opens the command console.
layer,lx,ly=SHIP_EQUIPMENT_WORLD['COMMAND_DESK']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='command_console'
app._overlay_key('g'); assert app.command.general_quarters
assert len(app.command.orders)>=8

# Cycle department and submit/issue an additional command.
app._overlay_key('tab'); app._overlay_key('0')
assert app.command.orders_issued>=9
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>20
app._overlay_key('e'); assert app.overlay is None

# A structural casualty triggers autonomous DC/medical response when time advances.
apply_impact(app.survivability,'DIVE_BOMB',90,zone='HANGAR_MID')
app.running_time=True; app.shipboard.running=True
for _ in range(4): app._update(1.05)
assert any(o.department=='DAMAGE_CONTROL' for o in app.command.orders.values())
assert any(c.duty=='BATTLE STATION' for c in app.life.crew.values())

# Render the live world with command state active.
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>35

app._sync_physics_profile(); assert 'departments' in app.profile.command_snapshot
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V12_PASS')
