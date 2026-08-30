from types import SimpleNamespace

from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT, LAYERS

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
app.profile.rank_index=max(app.profile.rank_index,14)

# Permanent D regression inside the new industrial district.
app.x,app.y,app.z=32,301,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
start=(app.x,app.y); app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
for _ in range(4): app._update(.04)
app._key_up(SimpleNamespace(keysym='d')); assert (app.x,app.y)!=start and app.overlay is None

# Physical National War Production Board opens v2.3 economy UI.
hq=next(p for p in all_static_interactions() if p.action=='economy_console')
app.x,app.y,app.z=hq.x,hq.y,hq.floor_z+CAMERA_HEIGHT; app._interact(); assert app.overlay=='economy_console'
app._overlay_key('s'); assert app.war_economy.active
app._overlay_key('p'); assert app.war_economy.selected_order.status=='ACTIVE'
app._overlay_key('i'); assert app.war_economy.selected_research.status=='ACTIVE'
# Damage and repair a selected facility through the physical board.
app.war_economy.selected_facility.damage=40
repairs=app.war_economy.facilities_repaired; app._overlay_key('f'); assert app.war_economy.facilities_repaired==repairs+1
# Damage and repair transport infrastructure.
app.war_economy.network.rail_damage=45
infra=app.war_economy.infrastructure_repairs; app._overlay_key('x'); assert app.war_economy.infrastructure_repairs==infra+1
# Allocate national stocks to the theater.
alloc=app.war_economy.allocations; app._overlay_key('a'); assert app.war_economy.allocations==alloc+1
app._overlay_key('e'); assert app.overlay is None

# Run production long enough to create output and render the industrial district.
for _ in range(20): app._update(.25)
app.x,app.y,app.z=31,278,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>100
app.overlay='economy_console'; app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>40

# Economy state persists with the career snapshot.
app._sync_physics_profile(); assert 'facilities' in app.profile.war_economy_snapshot and 'stockpiles' in app.profile.war_economy_snapshot

app.destroyed=True; app.destroy(); print('GUI_SMOKE_V23_PASS')
