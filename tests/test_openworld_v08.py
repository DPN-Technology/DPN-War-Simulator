import unittest

from warsim.openworld import (
    LAYERS, CONNECTORS, CAMERA_HEIGHT, SHIP_ORIGIN_X, SHIP_ORIGIN_Y,
    layer_walkable, world_walkable, current_layer, all_static_interactions,
)
from warsim.living_world import (
    create_living_world, advance_life, eat_meal, sleep_period, complete_maintenance,
)
from warsim.seamless3d import SHIP_EQUIPMENT_WORLD, SHIP_HATCH_WORLD


class SeamlessOpenWorldV08Tests(unittest.TestCase):
    def test_world_contains_base_and_six_enterprise_levels(self):
        required={"BASE","LOWER","ENGINEERING","HANGAR","FLIGHT","ISLAND","BRIDGE"}
        self.assertEqual(required,set(LAYERS))
        self.assertGreater(max(l.floor_z for l in LAYERS.values())-min(l.floor_z for l in LAYERS.values()),15)

    def test_gangway_is_continuously_walkable_without_world_switch(self):
        z=LAYERS["BASE"].floor_z+CAMERA_HEIGHT
        for x in (61,62,63,64,65,66):
            self.assertTrue(world_walkable(x,29,z),x)
        self.assertEqual("BASE",current_layer(62,29,z).key)
        self.assertEqual("HANGAR",current_layer(65,29,z).key)

    def test_every_vertical_connector_is_walkable_at_both_ends(self):
        for key,c in CONNECTORS.items():
            self.assertTrue(layer_walkable(c.from_layer,c.x,c.y),f"{key} from")
            self.assertTrue(layer_walkable(c.to_layer,c.x,c.y),f"{key} to")

    def test_static_real_life_interactions_are_physically_reachable(self):
        for p in all_static_interactions():
            matching=[l for l in LAYERS.values() if abs(l.floor_z-p.floor_z)<.1 and layer_walkable(l.key,p.x,p.y)]
            self.assertTrue(matching,p.key)

    def test_ship_operational_equipment_is_reachable_in_new_world(self):
        for key,(layer,lx,ly) in SHIP_EQUIPMENT_WORLD.items():
            self.assertTrue(layer_walkable(layer,SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly),key)

    def test_dynamic_hatches_are_on_walkable_passages(self):
        for key,(layer,lx,ly) in SHIP_HATCH_WORLD.items():
            self.assertTrue(layer_walkable(layer,SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly),key)

    def test_daily_life_needs_advance(self):
        s=create_living_world(1)
        before=(s.needs.hunger,s.needs.hydration,s.needs.fatigue)
        advance_life(s,60)
        self.assertGreater(s.needs.hunger,before[0])
        self.assertGreater(s.needs.hydration,before[1])
        self.assertGreater(s.needs.fatigue,before[2])

    def test_meal_and_sleep_restore_player(self):
        s=create_living_world(2)
        s.needs.hunger=90;s.needs.hydration=80;s.needs.fatigue=90
        eat_meal(s); self.assertLess(s.needs.hunger,40); self.assertLess(s.needs.hydration,60)
        sleep_period(s); self.assertLess(s.needs.fatigue,40)

    def test_maintenance_work_package_can_be_completed(self):
        s=create_living_world(3)
        self.assertGreaterEqual(len(s.work_orders),5)
        for key in list(s.work_orders):
            ok,_=complete_maintenance(s,key); self.assertTrue(ok)
        self.assertTrue(all(w.completed for w in s.work_orders.values()))
        self.assertEqual(len(s.work_orders),s.maintenance_completed)

    def test_crew_schedule_changes_targets(self):
        s=create_living_world(4)
        before={k:(c.target_x,c.target_y,c.target_z,c.duty) for k,c in s.crew.items()}
        advance_life(s,61)
        after={k:(c.target_x,c.target_y,c.target_z,c.duty) for k,c in s.crew.items()}
        self.assertNotEqual(before,after)


    def test_world_has_large_continuous_horizontal_extent(self):
        max_x=max(l.origin_x+l.width for l in LAYERS.values())
        max_y=max(l.origin_y+l.height for l in LAYERS.values())
        self.assertGreaterEqual(max_x,136)
        self.assertGreaterEqual(max_y,44)

    def test_all_enterprise_decks_are_connected_to_shore_graph(self):
        graph={k:set() for k in LAYERS}
        graph["BASE"].add("HANGAR"); graph["HANGAR"].add("BASE")
        for c in CONNECTORS.values():
            graph[c.from_layer].add(c.to_layer); graph[c.to_layer].add(c.from_layer)
        seen={"BASE"}; stack=["BASE"]
        while stack:
            cur=stack.pop()
            for nxt in graph[cur]:
                if nxt not in seen: seen.add(nxt); stack.append(nxt)
        self.assertEqual(set(LAYERS),seen)

    def test_launcher_uses_seamless_open_world(self):
        with open("main.py",encoding="utf-8") as fh: source=fh.read()
        self.assertIn("SeamlessOpenWorld3DApp",source)


if __name__=="__main__": unittest.main()
