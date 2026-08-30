import unittest

from warsim.firstperson3d import (
    HUB_MAP, BRIDGE_MAP, DAMAGE_MAP, SYSTEMS_MAP, HUB_NODES, BRIDGE_NODES, DAMAGE_NODES, SYSTEMS_NODES, project_point, grid_walkable, FirstPerson3DApp
)


class FirstPerson3DLogicTests(unittest.TestCase):
    def test_3d_maps_are_rectangular(self):
        for grid in (HUB_MAP, BRIDGE_MAP, SYSTEMS_MAP):
            self.assertEqual(1, len(set(map(len, grid))))

    def test_projection_has_real_depth_and_perspective(self):
        near = project_point(5, 1, 1.6, 0, 0, 1.6, 0, 0, 1200, 800)
        far = project_point(10, 1, 1.6, 0, 0, 1.6, 0, 0, 1200, 800)
        self.assertIsNotNone(near)
        self.assertIsNotNone(far)
        self.assertLess(near[2], far[2])
        self.assertGreater(abs(near[0] - 600), abs(far[0] - 600))

    def test_point_behind_camera_is_clipped(self):
        self.assertIsNone(project_point(-1, 0, 1.6, 0, 0, 1.6, 0, 0, 1200, 800))

    def test_hub_is_walkable_and_contains_all_game_access_stations(self):
        required = {"CAREER", "ACADEMY", "BRIDGE", "DAMAGE", "SYSTEMS", "ENTERPRISE", "HISTORY", "CREW", "TIMELINE", "QUALS", "PROMOTION"}
        self.assertTrue(required.issubset(HUB_NODES))
        for key in required:
            node = HUB_NODES[key]
            self.assertTrue(grid_walkable(HUB_MAP, node.x, node.y), key)

    def test_every_3d_interaction_station_is_physically_reachable(self):
        for grid, nodes in ((HUB_MAP, HUB_NODES), (BRIDGE_MAP, BRIDGE_NODES), (DAMAGE_MAP, DAMAGE_NODES), (SYSTEMS_MAP, SYSTEMS_NODES)):
            for key, node in nodes.items():
                self.assertTrue(grid_walkable(grid, node.x, node.y), key)

    def test_3d_ship_systems_room_exposes_coordinated_response_controls(self):
        actions = {node.action for node in SYSTEMS_NODES.values()}
        required = {
            "systems_fire", "systems_pump", "systems_portable_pump",
            "systems_electrical", "systems_ventilation", "systems_repair",
            "systems_boundary", "systems_breaker", "systems_eval"
        }
        self.assertTrue(required.issubset(actions))

    def test_main_launcher_imports_3d_app(self):
        with open("main.py", encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("FirstPerson3DApp", source)
        self.assertNotIn("WarSimulatorApp", source)


if __name__ == "__main__":
    unittest.main()
