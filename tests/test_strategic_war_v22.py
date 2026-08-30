import tempfile
import unittest
from pathlib import Path

from warsim.strategic_war import (
    create_strategic_war, begin_strategic_campaign, cycle_sector, cycle_formation, cycle_depot, cycle_operation,
    order_selected_formation, accept_selected_operation, request_recon, request_strategic_artillery,
    request_air_interdiction, request_coastal_naval_support, reinforce_selected_formation, repair_selected_bridge,
    advance_strategic_war, strategic_war_to_dict, strategic_war_from_dict,
)
from warsim.land_warfare import create_land_warfare
from warsim.ground_ops import create_ground_ops
from warsim.task_force import create_task_force
from warsim.openworld import all_static_interactions, LAYERS, world_walkable, CAMERA_HEIGHT
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile


class StrategicWarV22Tests(unittest.TestCase):
    def test_01_state_has_front_formations_depots_routes_operations(self):
        s=create_strategic_war()
        self.assertEqual(6,len(s.sectors)); self.assertGreaterEqual(len(s.formations),7)
        self.assertGreaterEqual(len(s.depots),3); self.assertGreaterEqual(len(s.routes),5); self.assertGreaterEqual(len(s.operations),4)

    def test_02_begin_campaign_activates_persistent_front(self):
        s=create_strategic_war(); ok,msg=begin_strategic_campaign(s)
        self.assertTrue(ok); self.assertTrue(s.active); self.assertIn('STRATEGIC CAMPAIGN',msg)

    def test_03_selectors_cycle(self):
        s=create_strategic_war(); a=s.selected_sector.key; b=s.selected_formation.key; c=s.selected_depot.key; d=s.selected_operation.key
        self.assertNotEqual(a,cycle_sector(s).key); self.assertNotEqual(b,cycle_formation(s).key)
        self.assertNotEqual(c,cycle_depot(s).key); self.assertNotEqual(d,cycle_operation(s).key)

    def test_04_formation_attack_order_targets_sector_and_spends_cp(self):
        s=create_strategic_war(); f=s.selected_formation; sec=s.selected_sector; cp=s.command_points
        ok,msg=order_selected_formation(s,'ATTACK')
        self.assertTrue(ok); self.assertEqual(sec.key,f.target_sector); self.assertEqual('ATTACK',f.order); self.assertLess(s.command_points,cp)

    def test_05_recon_improves_intelligence(self):
        s=create_strategic_war(); sec=s.selected_sector; before=sec.intel_confidence
        ok,msg=request_recon(s)
        self.assertTrue(ok); self.assertGreater(sec.intel_confidence,before); self.assertEqual(0,sec.recon_age_min); self.assertGreater(s.recon_reports,0)

    def test_06_strategic_artillery_consumes_land_shells(self):
        s=create_strategic_war(); lw=create_land_warfare(); b=next(iter(lw.artillery.values())); before=b.shells; enemy=s.selected_sector.enemy_power
        ok,msg=request_strategic_artillery(s,lw)
        self.assertTrue(ok); self.assertLess(b.shells,before); self.assertLess(s.selected_sector.enemy_power,enemy)

    def test_07_air_interdiction_consumes_support_points_and_disrupts_supply(self):
        s=create_strategic_war(); go=create_ground_ops(); go.air_support_points=50; before=s.selected_sector.supply_level
        ok,msg=request_air_interdiction(s,go)
        self.assertTrue(ok); self.assertLess(go.air_support_points,50); self.assertLess(s.selected_sector.supply_level,before)

    def test_08_coastal_naval_support_requires_coastal_sector_and_ammo(self):
        s=create_strategic_war(); tf=create_task_force()
        # select COAST (third sector)
        s.selected_sector_index=2; sec=s.selected_sector; self.assertTrue(sec.coastal)
        ship=next(iter(tf.friendly.values())); ammo=ship.ammo_pct; enemy=sec.enemy_power
        ok,msg=request_coastal_naval_support(s,tf)
        self.assertTrue(ok); self.assertLess(ship.ammo_pct,ammo); self.assertLess(sec.enemy_power,enemy)

    def test_09_reinforce_formation_consumes_depot_stocks(self):
        s=create_strategic_war(); f=s.selected_formation; dep=s.selected_depot
        f.manpower-=150; f.strength=70; repl=dep.replacements
        ok,msg=reinforce_selected_formation(s)
        self.assertTrue(ok); self.assertGreater(f.manpower,f.max_manpower-150); self.assertLess(dep.replacements,repl)

    def test_10_engineers_can_repair_damaged_bridge_route(self):
        s=create_strategic_war(); s.selected_sector_index=1 # RIVER
        r=s.routes['R-RIVER']; r.bridge_integrity=35; r.open=True; dep=s.selected_depot; repair=dep.repair
        ok,msg=repair_selected_bridge(s)
        self.assertTrue(ok); self.assertGreater(r.bridge_integrity,35); self.assertLess(dep.repair,repair); self.assertEqual(1,s.bridges_repaired)

    def test_11_front_line_can_shift_from_concentrated_power(self):
        s=create_strategic_war(); begin_strategic_campaign(s); sec=s.sectors['NORTH']; sec.owner='CONTESTED'; sec.control=66; sec.enemy_power=0; sec.fortification=0
        f=s.formations['F-1BDE']; f.x,f.y=sec.x,sec.y; f.order='ATTACK'; f.target_sector=sec.key
        for ef in [x for x in s.formations.values() if x.side=='ENEMY']: ef.x,ef.y=60,240
        msgs,last=advance_strategic_war(s,5.1,create_land_warfare(),create_ground_ops(),create_task_force(),None,0)
        self.assertEqual('FRIENDLY',sec.owner); self.assertGreaterEqual(s.front_shifts,1)

    def test_12_enemy_ai_launches_operational_pressure(self):
        s=create_strategic_war(); begin_strategic_campaign(s)
        msgs,last=advance_strategic_war(s,31.0,create_land_warfare(),create_ground_ops(),create_task_force(),None,0) # >60 strategic minutes
        self.assertGreaterEqual(s.enemy_offensives,1); self.assertTrue(any(f.order=='ATTACK' for f in s.formations.values() if f.side=='ENEMY'))

    def test_13_reinforcement_wave_arrives_over_time(self):
        s=create_strategic_war(); begin_strategic_campaign(s); f=s.formations['F-1BDE']; f.manpower-=400; f.strength=70
        advance_strategic_war(s,121.0,create_land_warfare(),create_ground_ops(),create_task_force(),None,0) # 242 strategic min
        self.assertTrue(s.reinforcements['RW-1'].arrived); self.assertGreaterEqual(s.reinforcement_waves,1); self.assertGreater(f.strength,70)

    def test_14_multiple_operations_can_progress_and_complete(self):
        s=create_strategic_war(); begin_strategic_campaign(s); op=s.operations['OP-RIVER']; op.status='ACTIVE'; sec=s.sectors['RIVER']; sec.owner='FRIENDLY'; sec.control=80
        advance_strategic_war(s,120.0,create_land_warfare(),create_ground_ops(),create_task_force(),None,0)
        self.assertEqual('COMPLETE',op.status); self.assertGreaterEqual(s.operations_completed,1)

    def test_15_tactical_battalion_victory_feeds_selected_strategic_sector(self):
        s=create_strategic_war(); begin_strategic_campaign(s); lw=create_land_warfare(); sec=s.selected_sector; before=(sec.control,sec.enemy_power)
        lw.operations_completed=1
        msgs,last=advance_strategic_war(s,.2,lw,create_ground_ops(),create_task_force(),None,0)
        self.assertEqual(1,last); self.assertGreater(sec.control,before[0]); self.assertLess(sec.enemy_power,before[1])

    def test_16_roundtrip_preserves_strategic_state(self):
        s=create_strategic_war(); begin_strategic_campaign(s); s.sectors['TOWN'].control=61; s.formations['F-ARM'].fuel=47; s.strategic_score=88
        r=strategic_war_from_dict(strategic_war_to_dict(s))
        self.assertTrue(r.active); self.assertEqual(61,r.sectors['TOWN'].control); self.assertEqual(47,r.formations['F-ARM'].fuel); self.assertEqual(88,r.strategic_score)

    def test_17_physical_theater_sites_share_the_same_walkable_world(self):
        wanted=('strategic_command','strategic_recon','strategic_logistics','strategic_front')
        interactions=all_static_interactions(); z=LAYERS['BASE'].floor_z+CAMERA_HEIGHT
        self.assertGreaterEqual(LAYERS['BASE'].height,240)
        for action in wanted:
            p=next(x for x in interactions if x.action==action)
            self.assertTrue(world_walkable(p.x,p.y,z),action)
        self.assertTrue(world_walkable(33,227,z))

    def test_18_old_profiles_and_persistence_support_v22_fields(self):
        old=CareerProfile.from_dict({'name':'v2.1 Save','land_operations_completed':2})
        self.assertEqual({},old.strategic_war_snapshot); self.assertEqual(0,old.strategic_operations_completed)
        p=CareerProfile(name='Strategic Tester',strategic_operations_completed=2,strategic_front_shifts=4,strategic_best_score=91)
        p.strategic_war_snapshot=strategic_war_to_dict(create_strategic_war())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'career.json'; save_profile(p,path); q=load_profile(path)
        self.assertEqual(2,q.strategic_operations_completed); self.assertEqual(4,q.strategic_front_shifts); self.assertEqual(91,q.strategic_best_score); self.assertIn('sectors',q.strategic_war_snapshot)

if __name__=='__main__': unittest.main()
