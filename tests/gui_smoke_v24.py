from types import SimpleNamespace

from warsim.seamless3d import SeamlessOpenWorld3DApp
from warsim.openworld import all_static_interactions, CAMERA_HEIGHT, LAYERS

app=SeamlessOpenWorld3DApp(); app.geometry('1280x720'); app.update_idletasks(); app.update(); app.overlay=None
app.profile.rank_index=max(app.profile.rank_index,14)

# Permanent D-key regression inside the new strategic mobility district.
app.x,app.y,app.z=32,313,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
start=(app.x,app.y); app._key_down(SimpleNamespace(keysym='d')); assert app.overlay is None and 'd' in app.keys
for _ in range(4): app._update(.04)
app._key_up(SimpleNamespace(keysym='d')); assert (app.x,app.y)!=start and app.overlay is None

# Physical Strategic Mobility Command opens the v2.4 logistics interface.
hq=next(p for p in all_static_interactions() if p.action=='logistics_console')
app.x,app.y,app.z=hq.x,hq.y,hq.floor_z+CAMERA_HEIGHT; app._interact(); assert app.overlay=='logistics_console'
app._overlay_key('s'); assert app.logistics_network.active
stock_before=app.war_economy.stockpiles['BUNKER_FUEL']
app.logistics_network.routes['R-RAIL-1'].distance_km=.2
app._overlay_key('a'); assert len(app.logistics_network.shipments)==1 and app.war_economy.stockpiles['BUNKER_FUEL']<stock_before
app._update(1.0); assert app.logistics_network.hubs['RAIL-ECHO'].inventory.get('BUNKER_FUEL',0)>0

# Once strategic logistics is active, the old direct economy allocation shortcut is blocked.
app.overlay='economy_console'; allocations=app.war_economy.allocations; app._overlay_key('a')
assert app.war_economy.allocations==allocations and 'DIRECT ALLOCATION DISABLED' in app.message

# Stage ammunition at the port through the national -> port route. This proves downstream routes cannot source national stock directly.
app.overlay='logistics_console'
app.logistics_network.selected_route_index=list(app.logistics_network.routes).index('R-PORT')
app.logistics_network.selected_package_index=list(app.logistics_network.packages).index('PKG-AMMO')
app.logistics_network.routes['R-PORT'].distance_km=.2
app._overlay_key('a'); app._update(1.0)
assert app.logistics_network.hubs['PORT-DELTA'].inventory.get('NAVAL_AMMO',0)>0

# Move the staged port inventory over the sea leg, assign a real task-force escort, then stage at Fleet Anchorage.
app.logistics_network.selected_route_index=list(app.logistics_network.routes).index('R-SEA-1')
app.logistics_network.routes['R-SEA-1'].distance_km=.2
app._overlay_key('a')
active=app.logistics_network.selected_shipment; assert active and active.mode=='SEA'
app._overlay_key('c'); assert active.escort
app.task_force.logistics.ammunition_pct=25
app._update(1.0)
assert app.logistics_network.hubs['ANCHOR-HOTEL'].inventory.get('NAVAL_AMMO',0)>0
assert app.task_force.logistics.ammunition_pct==25

# Final operational issue is a separate command; only now does the fleet receive the staged cargo.
app.logistics_network.selected_hub_index=list(app.logistics_network.hubs).index('ANCHOR-HOTEL')
app._overlay_key('i'); assert app.task_force.logistics.ammunition_pct>25 and app.logistics_network.hub_issues>=1

# Render the expanded freight / port / rail district and overlay.
app.overlay=None; app.x,app.y,app.z=31,323,LAYERS['BASE'].floor_z+CAMERA_HEIGHT
app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>100
app.overlay='logistics_console'; app._render(); app.update_idletasks(); assert len(app.canvas.find_all())>40

# Full logistics state persists in the career snapshot, including multi-leg hub issue state.
app._sync_physics_profile(); assert 'routes' in app.profile.logistics_network_snapshot and 'shipments' in app.profile.logistics_network_snapshot
assert app.profile.logistics_hub_issues>=1

app.destroyed=True; app.destroy(); print('GUI_SMOKE_V24_PASS')
