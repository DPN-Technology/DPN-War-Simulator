import unittest
from types import SimpleNamespace

from warsim.campaign import (
    create_campaign, accept_selected_mission, advance_campaign, campaign_to_dict, campaign_from_dict,
    set_time_compression, effective_time_scale, request_port_service, dispatch_selected_for_repair,
)
from warsim.task_force import create_task_force, advance_task_force
from warsim.survivability import create_survivability
from warsim.models import CareerProfile
from warsim.openworld import all_static_interactions


class CampaignV14Tests(unittest.TestCase):
    def physics(self, e=0.0, n=0.0, speed=0.0):
        return SimpleNamespace(east_nm=e,north_nm=n,heading_deg=90.0,speed_knots=speed,hull_integrity=80.0)

    def test_01_campaign_is_large_operational_space(self):
        s=create_campaign()
        pts=[(b.east_nm,b.north_nm) for b in s.bases.values()]
        span=max(((a[0]-b[0])**2+(a[1]-b[1])**2)**0.5 for a in pts for b in pts)
        self.assertGreater(span,250.0)
        self.assertGreaterEqual(len(s.bases),4)

    def test_02_accept_selected_mission(self):
        s=create_campaign()
        ok,msg=accept_selected_mission(s)
        self.assertTrue(ok)
        self.assertEqual(s.active_mission.status,"ACTIVE")
        self.assertIn("accepted",msg.lower())

    def test_03_patrol_mission_completes_in_sector(self):
        s=create_campaign(); accept_selected_mission(s)
        m=s.active_mission
        p=self.physics(m.target_east_nm,m.target_north_nm)
        tf=create_task_force(p.east_nm,p.north_nm,90)
        advance_campaign(s,p,tf,(m.required_minutes+1)*60)
        self.assertEqual(m.status,"COMPLETE")
        self.assertEqual(s.missions_completed,1)

    def test_04_convoy_moves_toward_destination(self):
        s=create_campaign(); c=s.convoys["CONVOY_A"]
        dest=s.bases[c.destination_key]
        before=((c.east_nm-dest.east_nm)**2+(c.north_nm-dest.north_nm)**2)**0.5
        p=self.physics(-200,-200); tf=create_task_force()
        advance_campaign(s,p,tf,3600)
        after=((c.east_nm-dest.east_nm)**2+(c.north_nm-dest.north_nm)**2)**0.5
        self.assertLess(after,before)

    def test_05_convoy_delivery_replenishes_forward_base(self):
        s=create_campaign(); c=s.convoys["CONVOY_A"]; dest=s.bases["FORWARD"]
        c.east_nm,c.north_nm=dest.east_nm-.05,dest.north_nm
        before=dest.fuel; p=self.physics(-200,-200); tf=create_task_force()
        advance_campaign(s,p,tf,60)
        self.assertGreater(dest.fuel,before)
        self.assertEqual(s.convoy_deliveries,1)

    def test_06_unescorted_convoy_takes_hazard_damage(self):
        s=create_campaign(); c=s.convoys["CONVOY_A"]
        c.east_nm,c.north_nm=72.0,34.0; c.destination_key="FORWARD"; c.threat_exposure_s=299
        p=self.physics(-200,-200); tf=create_task_force()
        advance_campaign(s,p,tf,2)
        self.assertLess(c.health_pct,100.0)

    def test_07_escorted_convoy_avoids_hazard_damage(self):
        s=create_campaign(); c=s.convoys["CONVOY_A"]
        c.east_nm,c.north_nm=72.0,34.0; c.destination_key="FORWARD"; c.threat_exposure_s=299
        p=self.physics(72.0,34.0); tf=create_task_force(72,34,90)
        advance_campaign(s,p,tf,10)
        self.assertEqual(c.health_pct,100.0)
        self.assertTrue(c.escorted)

    def test_08_port_service_requires_proximity(self):
        s=create_campaign(); tf=create_task_force(); p=self.physics(30,30,0)
        ok,_=request_port_service(s,tf,p,create_survivability())
        self.assertFalse(ok)

    def test_09_port_service_uses_finite_base_stock(self):
        s=create_campaign(); tf=create_task_force(); p=self.physics(0,0,.2); sv=create_survivability()
        tf.logistics.bunker_fuel_pct=30; s.bases["HOME"].fuel=40
        before=s.bases["HOME"].fuel
        ok,_=request_port_service(s,tf,p,sv)
        self.assertTrue(ok)
        self.assertLess(s.bases["HOME"].fuel,before)
        self.assertGreater(tf.logistics.bunker_fuel_pct,30)
        self.assertEqual(s.port_services,1)

    def test_10_port_service_rejects_high_speed(self):
        s=create_campaign(); tf=create_task_force(); p=self.physics(0,0,4)
        ok,msg=request_port_service(s,tf,p,create_survivability())
        self.assertFalse(ok); self.assertIn("speed",msg.lower())

    def test_11_repair_dispatch_requires_capable_base(self):
        s=create_campaign(); tf=create_task_force(); tf.selected_friendly.hull_pct=50
        s.selected_base_index=1 # forward base
        ok,_=dispatch_selected_for_repair(s,tf)
        self.assertFalse(ok)
        s.selected_base_index=3 # repair yard
        ok,_=dispatch_selected_for_repair(s,tf)
        self.assertTrue(ok)
        self.assertEqual(tf.selected_friendly.repair_destination,"REPAIR")

    def test_12_repair_yard_restores_damaged_escort(self):
        s=create_campaign(); tf=create_task_force(); v=tf.selected_friendly; v.hull_pct=70; v.propulsion_pct=75; v.steering_pct=80
        s.selected_base_index=3; ok,_=dispatch_selected_for_repair(s,tf); self.assertTrue(ok)
        b=s.bases["REPAIR"]; v.east_nm,v.north_nm=b.east_nm,b.north_nm
        p=self.physics(0,0,0)
        for _ in range(200):
            advance_campaign(s,p,tf,10)
            if not v.repair_destination: break
        self.assertGreater(v.hull_pct,70)
        self.assertGreaterEqual(s.escort_repairs,1)

    def test_13_campaign_roundtrip_persistence(self):
        s=create_campaign(); s.time_scale=15; s.operational_score=83; s.convoys["CONVOY_A"].health_pct=72
        restored=campaign_from_dict(campaign_to_dict(s))
        self.assertEqual(restored.time_scale,15)
        self.assertEqual(restored.operational_score,83)
        self.assertEqual(restored.convoys["CONVOY_A"].health_pct,72)

    def test_14_time_compression_and_emergency_safety(self):
        s=create_campaign(); set_time_compression(s,30)
        self.assertEqual(effective_time_scale(s),30)
        self.assertEqual(effective_time_scale(s,combat_active=True),1)
        self.assertEqual(effective_time_scale(s,casualty_active=True),1)
        self.assertEqual(effective_time_scale(s,collision_alarm=True),1)

    def test_15_physical_campaign_stations_exist(self):
        actions={p.action for p in all_static_interactions()}
        self.assertIn("campaign_console",actions)
        self.assertIn("campaign_logistics",actions)

    def test_16_profile_backward_compatible_campaign_fields(self):
        p=CareerProfile.from_dict({"name":"Old Save","fleet_orders_issued":3})
        self.assertEqual(p.name,"Old Save")
        self.assertEqual(p.campaign_snapshot,{})
        self.assertEqual(p.campaign_missions_completed,0)


if __name__ == '__main__':
    unittest.main()
