import tempfile
from pathlib import Path
import unittest
from warsim.models import CareerProfile, BridgeState, DamageState
from warsim.persistence import save_profile, load_profile
from warsim.systems import promotion_status, can_promote, promote, update_bridge, damage_action, damage_tick

class CoreTests(unittest.TestCase):
    def test_save_roundtrip(self):
        p=CareerProfile(name="Test Sailor")
        p.xp=444
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"save.json"
            save_profile(p,path)
            q=load_profile(path)
            self.assertEqual(q.name,"Test Sailor")
            self.assertEqual(q.xp,444)

    def test_promotion_requires_all_fields(self):
        p=CareerProfile()
        self.assertFalse(can_promote(p))
        p.written_exam=80;p.practical_exam=80;p.performance_review=80;p.leadership_eval=80
        p.recommendations=1;p.schools_completed=1;p.duty_periods=3;p.xp=400;p.mission_performance=80
        self.assertTrue(can_promote(p))
        ok,_=promote(p)
        self.assertTrue(ok)
        self.assertEqual(p.rank,"Seaman Recruit")

    def test_bridge_weather_drift_changes_heading(self):
        st=BridgeState(heading=0,rudder=0,wind_heading=90,wind_speed=30)
        update_bridge(st,1.0)
        self.assertNotEqual(st.heading,0)

    def test_damage_actions_have_consequences(self):
        st=DamageState()
        f=st.fire
        damage_action(st,"fire_team")
        self.assertLess(st.fire,f)
        for _ in range(3): damage_tick(st)
        self.assertGreater(st.elapsed,0)

if __name__ == '__main__':
    unittest.main()
