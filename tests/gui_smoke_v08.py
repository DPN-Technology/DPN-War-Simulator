from warsim.seamless3d import SeamlessOpenWorld3DApp, SHIP_EQUIPMENT_WORLD
from warsim.openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, CAMERA_HEIGHT, CONNECTORS, current_layer

app=SeamlessOpenWorld3DApp()
app.geometry('1280x720')
app.update_idletasks(); app.update()
assert app.world=='OPEN_WORLD'
assert app.overlay=='welcome_open'
app.overlay=None
app._render(); app.update_idletasks()
assert len(app.canvas.find_all())>30

# Physically move from shore side of the gangway into the hangar without a world switch.
app.x,app.y,app.z=62.0,29.0,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
app.yaw=0.0
app._move_open_world(1,0,0.75)
assert app.world=='OPEN_WORLD'
assert current_layer(app.x,app.y,app.z).key in ('BASE','HANGAR')
app.x,app.y=65.0,29.0
assert current_layer(app.x,app.y,app.z).key=='HANGAR'

# Seamless vertical connector changes z only, not scene/world.
c=CONNECTORS['HANGAR_FLIGHT_MID']
app.x,app.y,app.z=c.x,c.y,LAYERS['HANGAR'].floor_z+CAMERA_HEIGHT
app._interact()
assert app.vertical_travel is not None
app.vertical_travel['start']-=2
app._update(.02)
assert app.vertical_travel is None
assert abs((app.z-CAMERA_HEIGHT)-LAYERS['FLIGHT'].floor_z)<.05
assert app.world=='OPEN_WORLD'

# Operate a physical Enterprise console from the seamless world.
layer,lx,ly=SHIP_EQUIPMENT_WORLD['RADIO_RACK']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
before=app.shipboard.interactions
app._interact(); app.update_idletasks()
assert app.shipboard.interactions>before

# Living-world clock and needs run alongside Midway.
app.running_time=True; app.shipboard.running=True; app._life_accum=.99
life_before=app.life.minute_of_day; hist_before=app.shipboard.enterprise.current_minute
app._update(.05)
assert app.life.minute_of_day>=life_before+1
assert app.shipboard.enterprise.current_minute>=hist_before+1

# Render high deck after all systems have updated.
app._render(); app.update_idletasks()
assert len(app.canvas.find_all())>30
app.destroyed=True; app.destroy()
print('GUI_SMOKE_V08_PASS')
