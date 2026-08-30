import tempfile
import unittest
from pathlib import Path

from warsim.ground_combat import (
    create_ground_combat, begin_engagement, cycle_weapon, cycle_stance, toggle_aim,
    reload_weapon, fire_weapon, order_squad, request_air_support, request_naval_support,
    use_first_aid, treat_selected_squad_casualty, advance_ground_combat,
    ground_combat_to_dict, ground_combat_from_dict,
)
from warsim.ground_ops import create_ground_ops
from warsim.task_force import create_task_force
from warsim.openworld import all_static_interactions, LAYERS, world_walkable, CAMERA_HEIGHT
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile


class GroundCombatV20Tests(unittest.TestCase):
    def test_01_ground_combat_has_player_weapons_squad_contacts_objectives(self):
        s=create_ground_combat()
        self.assertGreaterEqual(len(s.weapons),3)
        self.assertGreaterEqual(len(s.squad),4)
        self.assertGreaterEqual(len(s.contacts),4)
        self.assertGreaterEqual(len(s.objectives),3)

    def test_02_begin_engagement_activates_player_and_checkpoint(self):
        s=create_ground_combat(); ok,msg=begin_engagement(s)
        self.assertTrue(ok); self.assertTrue(s.player.active); self.assertTrue(s.engagement_active)
        self.assertEqual('CHECKPOINT',s.active_objective.key); self.assertIn('FIELD EXERCISE',msg)

    def test_03_weapon_cycle_stance_and_aim(self):
        s=create_ground_combat(); self.assertEqual('RIFLE',s.player.selected_weapon)
        self.assertEqual('AUTO',cycle_weapon(s).key)
        self.assertIn('CROUCHED',cycle_stance(s)); self.assertIn('ON',toggle_aim(s))

    def test_04_fire_consumes_ammunition_and_can_hit_aligned_contact(self):
        s=create_ground_combat(); begin_engagement(s); c=s.selected_contact
        c.x,c.y=20,78; c.cover_pct=0; c.confidence=100; c.identified=True
        s.player.aiming=True; w=s.weapons['RIFLE']; before=w.magazine_rounds
        ok,msg=fire_weapon(s,12,78,0)
        self.assertTrue(ok); self.assertEqual(before-1,w.magazine_rounds); self.assertEqual(1,s.player.shots_fired)
        self.assertLess(c.health,100,msg)

    def test_05_reload_uses_reserve(self):
        s=create_ground_combat(); begin_engagement(s); w=s.weapons['RIFLE']; w.magazine_rounds=3; reserve=w.reserve_rounds
        ok,_=reload_weapon(s); self.assertTrue(ok)
        advance_ground_combat(s,w.reload_seconds+.1,12,78,0)
        self.assertEqual(w.magazine_capacity,w.magazine_rounds); self.assertLess(w.reserve_rounds,reserve)

    def test_06_squad_orders_propagate(self):
        s=create_ground_combat(); begin_engagement(s)
        ok,msg=order_squad(s,'SUPPRESS',12,78)
        self.assertTrue(ok); self.assertTrue(all(m.order=='SUPPRESS' for m in s.squad.values())); self.assertIn('SUPPRESS',msg)

    def test_07_air_support_is_finite_and_affects_target(self):
        s=create_ground_combat(); begin_engagement(s); go=create_ground_ops(); go.air_support_points=30
        c=s.selected_contact; before=c.health
        ok,msg=request_air_support(s,go,12,78)
        self.assertTrue(ok); self.assertLess(go.air_support_points,30); self.assertLess(c.health,before); self.assertIn('AIR SUPPORT',msg)

    def test_08_naval_support_consumes_escort_ammunition(self):
        s=create_ground_combat(); begin_engagement(s); tf=create_task_force(); c=s.selected_contact
        ship=next(iter(tf.friendly.values())); before=ship.ammo_pct; c.health=100
        ok,msg=request_naval_support(s,tf,12,78)
        self.assertTrue(ok); self.assertLess(ship.ammo_pct,before); self.assertLess(c.health,100); self.assertIn('NAVAL FIRE',msg)

    def test_09_first_aid_restores_player(self):
        s=create_ground_combat(); begin_engagement(s); s.player.health=48; s.player.wounded=True
        ok,_=use_first_aid(s); self.assertTrue(ok); self.assertGreater(s.player.health,48); self.assertEqual(1,s.player.first_aid_kits)

    def test_10_corpsman_treats_fireteam_casualty(self):
        s=create_ground_combat(); begin_engagement(s); m=s.squad['RIFLE']; m.health=42; m.wounded=True
        ok,_=treat_selected_squad_casualty(s); self.assertTrue(ok); self.assertGreater(m.health,42)

    def test_11_checkpoint_objective_completes_by_physical_presence(self):
        s=create_ground_combat(); begin_engagement(s); o=s.objectives['CHECKPOINT']
        advance_ground_combat(s,o.required_seconds+.2,o.x,o.y,0)
        self.assertEqual('COMPLETE',o.status); self.assertEqual('VILLAGE',s.active_objective.key)

    def test_12_training_contacts_begin_hidden_and_gain_confidence(self):
        s=create_ground_combat(); begin_engagement(s); c=s.contacts['RED-1']; self.assertEqual(0,c.confidence)
        # face the contact from close range
        heading=0.0
        x,y=20,86
        heading=0.0 if c.x>=x else 180.0
        advance_ground_combat(s,3,x,y,heading)
        self.assertGreater(c.confidence,0)

    def test_13_full_objective_sequence_can_complete(self):
        s=create_ground_combat(); begin_engagement(s)
        o=s.objectives['CHECKPOINT']; advance_ground_combat(s,o.required_seconds+.1,o.x,o.y,0)
        for c in s.contacts.values(): c.health=0; c.status='NEUTRALIZED'
        o=s.objectives['VILLAGE']; advance_ground_combat(s,o.required_seconds+.2,o.x,o.y,0)
        self.assertEqual('COMPLETE',o.status)
        o=s.objectives['AID']; advance_ground_combat(s,o.required_seconds+.2,o.x,o.y,0)
        self.assertTrue(s.engagement_complete); self.assertEqual(1,s.engagements_completed)

    def test_14_ground_combat_roundtrip(self):
        s=create_ground_combat(); begin_engagement(s); s.player.health=73; s.weapons['RIFLE'].magazine_rounds=7; s.score=84
        r=ground_combat_from_dict(ground_combat_to_dict(s))
        self.assertEqual(73,r.player.health); self.assertEqual(7,r.weapons['RIFLE'].magazine_rounds); self.assertEqual(84,r.score)

    def test_15_physical_combined_arms_interactions_exist_and_reachable(self):
        wanted=('infantry_armory','infantry_command','infantry_aid','infantry_range')
        interactions=all_static_interactions(); z=LAYERS['BASE'].floor_z+CAMERA_HEIGHT
        for action in wanted:
            p=next(x for x in interactions if x.action==action)
            self.assertTrue(world_walkable(p.x,p.y,z),action)

    def test_16_training_village_expands_same_base_world(self):
        z=LAYERS['BASE'].floor_z+CAMERA_HEIGHT
        self.assertGreaterEqual(LAYERS['BASE'].height,100)
        self.assertTrue(world_walkable(31,84,z))
        self.assertTrue(world_walkable(35,99,z))

    def test_17_profile_backward_compatibility_adds_ground_combat_fields(self):
        p=CareerProfile.from_dict({'name':'Old Save','ground_missions_completed':2})
        self.assertEqual({},p.ground_combat_snapshot); self.assertEqual(0,p.ground_combat_runs)

    def test_18_profile_persists_ground_combat_snapshot_and_stats(self):
        p=CareerProfile(name='Infantry Tester',ground_combat_runs=2,ground_combat_best_score=91,ground_enemies_neutralized=7)
        p.ground_combat_snapshot=ground_combat_to_dict(create_ground_combat())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'career.json'; save_profile(p,path); q=load_profile(path)
        self.assertEqual(2,q.ground_combat_runs); self.assertEqual(91,q.ground_combat_best_score); self.assertIn('squad',q.ground_combat_snapshot)


if __name__=='__main__': unittest.main()
