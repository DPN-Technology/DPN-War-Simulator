from types import SimpleNamespace
from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import LAYERS,CAMERA_HEIGHT,SHIP_ORIGIN_X,SHIP_ORIGIN_Y,SHIP_LENGTH_M,SHIP_WIDTH_M,SHIP_CENTER_X
from warsim.config import VERSION

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
assert tuple(map(int,VERSION.split('.'))) >= (2,5,0)
assert SHIP_LENGTH_M==245 and SHIP_WIDTH_M==30
assert app.hud_expanded is False

# D remains a movement key only.
app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
app._key_up(SimpleNamespace(keysym='d')); assert 'd' not in app.keys

# Mid-flight-deck render exercises real-scale deck silhouette, island/funnel/mast, compact HUD and culling.
app.x=SHIP_ORIGIN_X+105; app.y=SHIP_ORIGIN_Y+15; app.z=LAYERS['FLIGHT'].floor_z+CAMERA_HEIGHT
app.yaw=.08; app.pitch=-.02
app._render(); app.update_idletasks()
items=len(app.canvas.find_all()); assert 120 < items < 1000, items

# Full-scale geometry collection is merged, not one polygon per 1m tile.
faces=[]; app._collect_open_geometry(faces,1280,720); assert len(faces)<160, len(faces)

# Tab exposes deep systems picture without blocking the world by default.
app._key_down(SimpleNamespace(keysym='Tab')); assert app.hud_expanded is True
app._key_up(SimpleNamespace(keysym='Tab'))
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>items
app._key_down(SimpleNamespace(keysym='Tab')); assert app.hud_expanded is False
app._key_up(SimpleNamespace(keysym='Tab'))

# Quality modes remain user-selectable; default returns to balanced.
app._key_down(SimpleNamespace(keysym='F4')); assert app.visual_quality=='HIGH'; app._key_up(SimpleNamespace(keysym='F4'))
app._key_down(SimpleNamespace(keysym='F4')); assert app.visual_quality=='PERFORMANCE'; app._key_up(SimpleNamespace(keysym='F4'))
app._key_down(SimpleNamespace(keysym='F4')); assert app.visual_quality=='BALANCED'; app._key_up(SimpleNamespace(keysym='F4'))

# Save marks the real-scale layout so migrated coordinates are never stretched twice.
app._sync_physics_profile(); assert app.profile.ship_layout_version==2
assert app.profile.player_world_x > SHIP_ORIGIN_X+70
app.destroyed=True; app.destroy(); print('GUI_SMOKE_V25_PASS')
