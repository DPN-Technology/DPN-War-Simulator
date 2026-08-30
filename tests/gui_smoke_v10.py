from warsim.seamless3d import SeamlessOpenWorld3DApp, SHIP_EQUIPMENT_WORLD
from warsim.openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, CAMERA_HEIGHT
from warsim.naval_combat import advance_naval_combat

app=SeamlessOpenWorld3DApp()
app.geometry('1280x720')
app.update_idletasks(); app.update(); app.overlay=None

# Physical CIC plot -> combat plot -> explicitly simulated raid.
layer,lx,ly=SHIP_EQUIPMENT_WORLD['CIC_PLOT']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='combat_plot'
app._overlay_key('g'); assert app.combat.general_quarters
app._overlay_key('t'); assert app.combat.raid_active and len(app.combat.tracks)==3
app._overlay_key('a')
app._overlay_key('e'); assert app.overlay is None

# Physical AA director -> solution -> fire.
track=next(iter(app.combat.tracks.values())); track.range_nm=7.0; app.combat.selected_track=track.key
layer,lx,ly=SHIP_EQUIPMENT_WORLD['AA_DIRECTOR']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='weapons_control'
app._overlay_key('a'); app._overlay_key('s')
health=track.health
app._overlay_key('space'); assert track.health<health
app._overlay_key('e')

# Prepare a fighter package and launch CAP from the physical Flight Control console.
ac=app.shipboard.aircraft['F4F_CAP']; ac.deck='FLIGHT'; ac.fueled=True; ac.armed=True; ac.spotted=True
layer,lx,ly=SHIP_EQUIPMENT_WORLD['FLIGHT_CONTROL']
app.x,app.y,app.z=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z+CAMERA_HEIGHT
app._interact(); assert app.overlay=='air_combat'
app._overlay_key('c'); assert app.combat.air.cap_airborne
app._overlay_key('e')

# Exterior renderer sees combat contacts/CAP and HUD remains alive.
app.x,app.y,app.z=SHIP_ORIGIN_X+30,SHIP_ORIGIN_Y+12,LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>35

# A simulated raid hit flows into physical hull/equipment damage.
target=next(t for t in app.combat.tracks.values() if not t.destroyed)
target.range_nm=0.02; target.health=100
hull=app.physics.hull_integrity
advance_naval_combat(app.combat,app.physics,app.shipboard,.25)
assert app.physics.hull_integrity<hull
assert any(rt.fault=='SIMULATED COMBAT DAMAGE' for rt in app.shipboard.equipment_runtime.values())

# Magazine and tactical overlays render.
app.overlay='magazine_combat'; app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>25
app.overlay='combat_plot'; app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>25

app.destroyed=True; app.destroy()
print('GUI_SMOKE_V10_PASS')
