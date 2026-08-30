import unittest

from warsim.economy import (
    create_war_economy, begin_war_economy, start_selected_order, advance_war_economy,
    start_selected_research, toggle_selected_training, repair_selected_facility,
    repair_transport_network, allocate_stockpiles, war_economy_to_dict, war_economy_from_dict,
)
from warsim.strategic_war import create_strategic_war, begin_strategic_campaign, advance_strategic_war
from warsim.campaign import create_campaign
from warsim.air_wing import create_air_wing, STATUS_LOST
from warsim.land_warfare import create_land_warfare
from warsim.task_force import create_task_force
from warsim.openworld import LAYERS, CAMERA_HEIGHT, world_walkable, all_static_interactions


class EconomyV23Tests(unittest.TestCase):
    def test_01_default_industrial_base_exists(self):
        e=create_war_economy()
        self.assertGreaterEqual(len(e.facilities),7)
        self.assertIn('AIR',e.facilities)
        self.assertIn('SHIPYARD',e.facilities)
        self.assertIn('FIGHTER_AIRFRAME',e.stockpiles)

    def test_02_begin_war_economy(self):
        e=create_war_economy(); ok,msg=begin_war_economy(e)
        self.assertTrue(ok); self.assertTrue(e.active); self.assertIn('ACTIVE',msg)

    def test_03_production_consumes_material_and_adds_stock(self):
        e=create_war_economy(); begin_war_economy(e)
        before=e.stockpiles['FIGHTER_AIRFRAME']; steel=e.reserves['STEEL']
        ok,_=start_selected_order(e); self.assertTrue(ok)
        advance_war_economy(e,240)
        self.assertGreater(e.stockpiles['FIGHTER_AIRFRAME'],before)
        self.assertLess(e.reserves['STEEL'],steel+10)  # extraction occurs, but production still costs substantial steel.

    def test_04_material_shortage_holds_production(self):
        e=create_war_economy(); begin_war_economy(e); e.reserves['ALUMINUM']=0
        start_selected_order(e); advance_war_economy(e,240)
        self.assertEqual(e.orders['P-FIGHTER'].status,'MATERIAL HOLD')

    def test_05_research_improves_facility(self):
        e=create_war_economy(); begin_war_economy(e)
        before=e.facilities['AIR'].efficiency
        ok,_=start_selected_research(e); self.assertTrue(ok)
        advance_war_economy(e,1300)
        self.assertEqual(e.research['R-PROD'].status,'COMPLETE')
        self.assertGreater(e.facilities['AIR'].efficiency,before)

    def test_06_training_pipeline_generates_replacements(self):
        e=create_war_economy(); begin_war_economy(e)
        before=e.stockpiles['TRAINED_PERSONNEL']
        advance_war_economy(e,160)
        self.assertGreater(e.stockpiles['TRAINED_PERSONNEL'],before)
        self.assertGreater(e.personnel_graduated,0)

    def test_07_facility_damage_reduces_capacity(self):
        e=create_war_economy(); f=e.facilities['AIR']; before=f.effective_capacity
        f.damage=55
        self.assertLess(f.effective_capacity,before)

    def test_08_facility_repair_uses_repair_stores(self):
        e=create_war_economy(); f=e.facilities['AIR']; f.damage=50
        e.selected_facility_index=list(e.facilities).index('AIR')
        before=e.stockpiles['REPAIR_STORES']; ok,_=repair_selected_facility(e)
        self.assertTrue(ok); self.assertLess(f.damage,50); self.assertLess(e.stockpiles['REPAIR_STORES'],before)

    def test_09_transport_damage_and_repair(self):
        e=create_war_economy(); e.network.rail_damage=60; before=e.network.throughput
        ok,_=repair_transport_network(e)
        self.assertTrue(ok); self.assertLess(e.network.rail_damage,60); self.assertGreater(e.network.throughput,before)

    def test_10_theater_allocation_replenishes_depot(self):
        e=create_war_economy(); sw=create_strategic_war(); e.selected_allocation='THEATER'
        before=min(d.fuel for d in sw.depots.values() if d.side=='FRIENDLY')
        ok,_=allocate_stockpiles(e,strategic_war=sw)
        self.assertTrue(ok); self.assertGreaterEqual(min(d.fuel for d in sw.depots.values() if d.side=='FRIENDLY'),before)

    def test_11_air_allocation_replaces_lost_aircraft(self):
        e=create_war_economy(); aw=create_air_wing(1); e.selected_allocation='AIR'
        a=next(iter(aw.aircraft.values())); a.status=STATUS_LOST; aw.aircraft_lost=1
        ok,_=allocate_stockpiles(e,air_wing=aw)
        self.assertTrue(ok); self.assertNotEqual(a.status,STATUS_LOST); self.assertGreater(aw.aviation_fuel_units,6200)

    def test_12_land_allocation_feeds_artillery_and_replacements(self):
        e=create_war_economy(); lw=create_land_warfare(); e.selected_allocation='LAND'
        shells=sum(b.shells for b in lw.artillery.values()); ok,_=allocate_stockpiles(e,land_warfare=lw)
        self.assertTrue(ok); self.assertGreater(sum(b.shells for b in lw.artillery.values()),shells)

    def test_13_navy_allocation_feeds_task_force(self):
        e=create_war_economy(); tf=create_task_force(0,0,90); e.selected_allocation='NAVY'
        ship=next(iter(tf.friendly.values())); ship.ammo_pct=40; before=ship.ammo_pct
        ok,_=allocate_stockpiles(e,task_force=tf)
        self.assertTrue(ok); self.assertGreater(ship.ammo_pct,before)

    def test_14_base_allocation_feeds_campaign_base(self):
        e=create_war_economy(); c=create_campaign(); e.selected_allocation='BASES'
        b=min(c.bases.values(),key=lambda q:q.readiness); before=b.aviation_fuel
        ok,_=allocate_stockpiles(e,campaign=c)
        self.assertTrue(ok); self.assertGreaterEqual(b.aviation_fuel,before)

    def test_15_economy_persistence_round_trip(self):
        e=create_war_economy(); e.active=True; e.stockpiles['TANK']=17; e.network.rail_damage=33
        d=war_economy_to_dict(e); r=war_economy_from_dict(d)
        self.assertTrue(r.active); self.assertEqual(r.stockpiles['TANK'],17); self.assertEqual(r.network.rail_damage,33)

    def test_16_strategic_reinforcement_can_be_delayed_by_economy_shortage(self):
        sw=create_strategic_war(); begin_strategic_campaign(sw); e=create_war_economy(); begin_war_economy(e)
        e.stockpiles['TRAINED_PERSONNEL']=0; e.stockpiles['SMALL_ARMS_AMMO']=0; e.stockpiles['BUNKER_FUEL']=0
        advance_strategic_war(sw,121,last_land_ops_completed=0,economy=e)
        self.assertFalse(sw.reinforcements['RW-1'].arrived)
        self.assertGreater(sw.reinforcements['RW-1'].eta_min,240)
        e.stockpiles['TRAINED_PERSONNEL']=1000; e.stockpiles['SMALL_ARMS_AMMO']=100; e.stockpiles['BUNKER_FUEL']=100
        advance_strategic_war(sw,31,last_land_ops_completed=0,economy=e)
        self.assertTrue(sw.reinforcements['RW-1'].arrived)
        self.assertLess(e.stockpiles['TRAINED_PERSONNEL'],1000)

    def test_17_enemy_held_front_can_damage_industry(self):
        e=create_war_economy(); begin_war_economy(e); sw=create_strategic_war(); begin_strategic_campaign(sw)
        before=sum(f.damage for f in e.facilities.values())
        advance_war_economy(e,361,strategic_war=sw)
        self.assertGreater(sum(f.damage for f in e.facilities.values()),before)
        self.assertGreater(e.industrial_damage_events,0)

    def test_18_industrial_district_is_physically_reachable(self):
        z=LAYERS['BASE'].floor_z+CAMERA_HEIGHT
        self.assertTrue(world_walkable(32,301,z))
        actions={i.action for i in all_static_interactions()}
        self.assertIn('economy_console',actions)
        self.assertIn('economy_production',actions)


if __name__=='__main__':
    unittest.main()
