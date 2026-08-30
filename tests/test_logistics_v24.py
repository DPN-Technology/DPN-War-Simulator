import unittest

from warsim.logistics_network import (
    create_logistics_network, begin_logistics_network, dispatch_selected_shipment,
    assign_escort, repair_selected_route, repair_selected_hub, issue_selected_hub,
    advance_logistics_network, logistics_network_to_dict, logistics_network_from_dict,
    cycle_route, cycle_hub, cycle_package, cycle_priority,
)
from warsim.economy import create_war_economy, allocate_stockpiles
from warsim.strategic_war import create_strategic_war
from warsim.task_force import create_task_force
from warsim.ground_ops import create_ground_ops
from warsim.air_wing import create_air_wing
from warsim.land_warfare import create_land_warfare
from warsim.openworld import LAYERS, CAMERA_HEIGHT, world_walkable, all_static_interactions
from warsim.models import CareerProfile


class LogisticsV24Tests(unittest.TestCase):
    def _select_route(self,s,key):
        s.selected_route_index=list(s.routes).index(key)
    def _select_pkg(self,s,key):
        s.selected_package_index=list(s.packages).index(key)
    def _select_hub(self,s,key):
        s.selected_hub_index=list(s.hubs).index(key)
    def _stage(self,s,hub_key,pkg_key):
        cargo=s.packages[pkg_key].cargo
        h=s.hubs[hub_key]
        for k,v in cargo.items(): h.inventory[k]=h.inventory.get(k,0)+v
    def _short(self,s,key,d=.5):
        s.routes[key].distance_km=d

    def test_01_default_network_exists(self):
        s=create_logistics_network()
        self.assertGreaterEqual(len(s.hubs),6); self.assertGreaterEqual(len(s.routes),6)
        self.assertIn('R-SEA-1',s.routes); self.assertIn('PKG-FUEL',s.packages)
        self.assertEqual(s.hubs['PORT-DELTA'].recipient,'TRANSIT')
        self.assertEqual(s.hubs['RAIL-ECHO'].recipient,'TRANSIT')

    def test_02_begin_network(self):
        s=create_logistics_network(); ok,msg=begin_logistics_network(s)
        self.assertTrue(ok); self.assertTrue(s.active); self.assertIn('ACTIVE',msg)

    def test_03_dispatch_reserves_national_stock(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy()
        before=e.stockpiles['BUNKER_FUEL']; self._select_pkg(s,'PKG-FUEL')
        ok,_=dispatch_selected_shipment(s,e)
        self.assertTrue(ok); self.assertLess(e.stockpiles['BUNKER_FUEL'],before); self.assertEqual(len(s.shipments),1)

    def test_04_downstream_dispatch_requires_staged_origin_inventory(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy()
        self._select_route(s,'R-ROAD-2'); self._select_pkg(s,'PKG-REPAIR')
        ok,msg=dispatch_selected_shipment(s,e)
        self.assertFalse(ok); self.assertIn('SOURCE SHORTAGE',msg); self.assertIn('preceding route legs',msg)

    def test_05_route_congestion_limits_parallel_lifts(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); self._select_route(s,'R-ROAD-2')
        s.routes['R-ROAD-2'].capacity=30; self._select_pkg(s,'PKG-REPAIR'); self._stage(s,'FWD-FOXTROT','PKG-REPAIR'); self._stage(s,'FWD-FOXTROT','PKG-REPAIR')
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok)
        ok,msg=dispatch_selected_shipment(s,e); self.assertFalse(ok); self.assertIn('CONGESTION',msg)

    def test_06_multileg_rail_road_then_issue_replenishes_theater(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); sw=create_strategic_war(); lw=create_land_warfare()
        before=sum(d.replacements for d in sw.depots.values() if d.side=='FRIENDLY')
        self._select_route(s,'R-RAIL-1'); self._select_pkg(s,'PKG-REPL'); self._short(s,'R-RAIL-1')
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok); advance_logistics_network(s,1,e,sw,None,None,None,lw,None)
        self.assertGreater(s.hubs['RAIL-ECHO'].inventory.get('TRAINED_PERSONNEL',0),0)
        self.assertEqual(sum(d.replacements for d in sw.depots.values() if d.side=='FRIENDLY'),before)
        self._select_route(s,'R-ROAD-1'); self._short(s,'R-ROAD-1',.2)
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok); advance_logistics_network(s,1,e,sw,None,None,None,lw,None)
        self._select_hub(s,'FWD-FOXTROT'); ok,msg=issue_selected_hub(s,strategic_war=sw,land_warfare=lw)
        self.assertTrue(ok); self.assertIn('HUB ISSUE COMPLETE',msg)
        self.assertGreater(sum(d.replacements for d in sw.depots.values() if d.side=='FRIENDLY'),before)

    def test_07_unescorted_sea_shipment_can_be_lost(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); self._select_route(s,'R-SEA-1'); self._select_pkg(s,'PKG-FUEL')
        self._stage(s,'PORT-DELTA','PKG-FUEL'); s.routes['R-SEA-1'].interdiction=80
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok)
        advance_logistics_network(s,2000,e)
        self.assertGreaterEqual(s.lost_shipments,1)

    def test_08_escort_protects_sea_delivery_then_hub_issue_feeds_fleet(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); tf=create_task_force(0,0,90)
        self._select_route(s,'R-SEA-1'); self._select_pkg(s,'PKG-FUEL'); self._stage(s,'PORT-DELTA','PKG-FUEL'); self._short(s,'R-SEA-1')
        tf.logistics.bunker_fuel_pct=30
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok); ok,_=assign_escort(s,tf); self.assertTrue(ok)
        advance_logistics_network(s,1,e,task_force=tf)
        self.assertEqual(s.delivered_shipments,1); self.assertEqual(tf.logistics.bunker_fuel_pct,30)
        self._select_hub(s,'ANCHOR-HOTEL'); ok,_=issue_selected_hub(s,task_force=tf)
        self.assertTrue(ok); self.assertGreater(tf.logistics.bunker_fuel_pct,30)

    def test_09_route_repair_uses_repair_stock(self):
        s=create_logistics_network(); e=create_war_economy(); self._select_route(s,'R-ROAD-1'); r=s.selected_route; r.damage=55; r.bridge_integrity=45
        before=e.stockpiles['REPAIR_STORES']; ok,_=repair_selected_route(s,e)
        self.assertTrue(ok); self.assertLess(r.damage,55); self.assertGreater(r.bridge_integrity,45); self.assertLess(e.stockpiles['REPAIR_STORES'],before)

    def test_10_hub_failure_delays_arrival(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); self._select_route(s,'R-ROAD-2'); self._select_pkg(s,'PKG-REPAIR')
        self._stage(s,'FWD-FOXTROT','PKG-REPAIR'); s.hubs['AIR-GOLF'].damage=96
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok); advance_logistics_network(s,10,e)
        self.assertEqual(next(iter(s.shipments.values())).status,'DELAYED'); self.assertGreater(s.delayed_shipments,0)

    def test_11_hub_repair_restores_capacity(self):
        s=create_logistics_network(); e=create_war_economy(); self._select_hub(s,'AIR-GOLF'); h=s.selected_hub; h.damage=70
        before=h.effective_capacity; ok,_=repair_selected_hub(s,e)
        self.assertTrue(ok); self.assertGreater(h.effective_capacity,before); self.assertEqual(s.hub_repairs,1)

    def test_12_damaged_bridge_can_close_road(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); self._select_route(s,'R-ROAD-1'); self._select_pkg(s,'PKG-REPAIR')
        self._stage(s,'RAIL-ECHO','PKG-REPAIR'); r=s.selected_route; r.bridge_integrity=5; r.damage=70
        ok,msg=dispatch_selected_shipment(s,e)
        self.assertFalse(ok); self.assertIn('not capable',msg)

    def test_13_air_hub_stages_then_issue_feeds_airfield_and_airwing(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); go=create_ground_ops(); aw=create_air_wing(2)
        self._select_route(s,'R-ROAD-2'); self._select_pkg(s,'PKG-AIR'); self._stage(s,'FWD-FOXTROT','PKG-AIR'); self._short(s,'R-ROAD-2',.2)
        af=go.selected_airfield; af.aviation_fuel=15; before=aw.aviation_fuel_units
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok); advance_logistics_network(s,1,e,ground_ops=go,air_wing=aw)
        self.assertEqual(af.aviation_fuel,15)
        self._select_hub(s,'AIR-GOLF'); ok,_=issue_selected_hub(s,ground_ops=go,air_wing=aw)
        self.assertTrue(ok); self.assertGreater(af.aviation_fuel,15); self.assertGreater(aw.aviation_fuel_units,before)

    def test_14_transit_hub_cannot_issue_operationally(self):
        s=create_logistics_network(); self._stage(s,'RAIL-ECHO','PKG-REPAIR'); self._select_hub(s,'RAIL-ECHO')
        ok,msg=issue_selected_hub(s)
        self.assertFalse(ok); self.assertIn('staging/transit',msg)

    def test_15_persistence_round_trip_includes_hub_inventory_and_issues(self):
        s=create_logistics_network(); begin_logistics_network(s); self._stage(s,'FWD-FOXTROT','PKG-REPAIR'); s.hub_issues=3
        s.routes['R-RAIL-1'].damage=27; d=logistics_network_to_dict(s); r=logistics_network_from_dict(d)
        self.assertTrue(r.active); self.assertEqual(r.routes['R-RAIL-1'].damage,27); self.assertGreater(r.hubs['FWD-FOXTROT'].inventory['REPAIR_STORES'],0); self.assertEqual(r.hub_issues,3)

    def test_16_direct_economy_allocation_disabled_when_network_active(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); sw=create_strategic_war(); e.selected_allocation='THEATER'
        ok,msg=allocate_stockpiles(e,strategic_war=sw,logistics_network=s)
        self.assertFalse(ok); self.assertIn('DIRECT ALLOCATION DISABLED',msg)

    def test_17_logistics_district_is_physically_reachable(self):
        z=LAYERS['BASE'].floor_z+CAMERA_HEIGHT
        self.assertTrue(world_walkable(32,313,z)); self.assertTrue(world_walkable(31,323,z)); self.assertTrue(world_walkable(34,350,z))
        actions={i.action for i in all_static_interactions()}
        self.assertIn('logistics_console',actions); self.assertIn('logistics_dispatch',actions); self.assertIn('logistics_receiving',actions)

    def test_18_selection_and_priority_controls(self):
        s=create_logistics_network(); r0=s.selected_route.key; h0=s.selected_hub.key; p0=s.selected_package.key
        self.assertNotEqual(cycle_route(s).key,r0); self.assertNotEqual(cycle_hub(s).key,h0); self.assertNotEqual(cycle_package(s).key,p0)
        self.assertEqual(cycle_priority(s),3)

    def test_19_lost_shipments_reduce_logistics_score(self):
        s=create_logistics_network(); begin_logistics_network(s); e=create_war_economy(); self._select_route(s,'R-SEA-1'); self._select_pkg(s,'PKG-FUEL')
        self._stage(s,'PORT-DELTA','PKG-FUEL'); s.routes['R-SEA-1'].interdiction=90; before=s.logistics_score
        ok,_=dispatch_selected_shipment(s,e); self.assertTrue(ok); advance_logistics_network(s,2200,e)
        self.assertGreater(s.lost_shipments,0); self.assertLess(s.logistics_score,before)

    def test_20_career_profile_back_compat_has_hub_issue_stat(self):
        p=CareerProfile.from_dict({'name':'Legacy','rank_index':0})
        self.assertEqual(p.logistics_hub_issues,0)


if __name__=='__main__':
    unittest.main()
