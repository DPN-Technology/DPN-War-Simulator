import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import warsim.persistence as persistence
from warsim.config import SAVE_SCHEMA
from warsim.models import CareerProfile
from warsim.persistence import (
    SaveCorruptionError,
    backup_path,
    load_profile,
    recover_profile,
    save_profile,
)


class PersistenceRecoveryTests(unittest.TestCase):
    def test_missing_save_is_distinct_from_corrupt_save(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            self.assertIsNone(load_profile(path))
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(SaveCorruptionError):
                load_profile(path)

    def test_schema_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            payload = {"schema": SAVE_SCHEMA + 99, "profile": CareerProfile().to_dict()}
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(SaveCorruptionError):
                load_profile(path)

    def test_second_save_preserves_previous_verified_recovery_copy(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            save_profile(CareerProfile(name="First", xp=100), path)
            save_profile(CareerProfile(name="Second", xp=200), path)
            self.assertEqual(load_profile(path).name, "Second")
            recovery = backup_path(path)
            self.assertTrue(recovery.exists())
            recovered_payload = json.loads(recovery.read_text(encoding="utf-8"))
            self.assertEqual(recovered_payload["profile"]["name"], "First")

    def test_corruption_never_overwrites_known_good_recovery_copy(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            save_profile(CareerProfile(name="Known Good", xp=123), path)
            save_profile(CareerProfile(name="Newest", xp=456), path)
            recovery = backup_path(path)
            before = recovery.read_bytes()
            path.write_bytes(b"corrupt-career-state")

            with self.assertRaises(SaveCorruptionError):
                save_profile(CareerProfile(name="Must Not Save"), path)
            self.assertEqual(recovery.read_bytes(), before)

    def test_failed_post_write_verification_restores_previous_live_save(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            save_profile(CareerProfile(name="Known Good", xp=111), path)
            original_atomic_write = persistence._atomic_write

            def corrupt_new_live_save(target, data):
                original_atomic_write(target, data)
                if Path(target) == path and b'"Broken Replacement"' in data:
                    path.write_bytes(b"corrupt-after-atomic-replace")

            with mock.patch("warsim.persistence._atomic_write", side_effect=corrupt_new_live_save):
                with self.assertRaises(SaveCorruptionError):
                    save_profile(CareerProfile(name="Broken Replacement", xp=999), path)

            restored = load_profile(path)
            self.assertEqual(restored.name, "Known Good")
            self.assertEqual(restored.xp, 111)

    def test_verified_recovery_restores_previous_profile(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            save_profile(CareerProfile(name="Recovery Marker", xp=321), path)
            save_profile(CareerProfile(name="Later State", xp=654), path)
            path.write_bytes(b"damaged")

            with self.assertRaises(SaveCorruptionError):
                load_profile(path)
            recovered = recover_profile(path)
            self.assertEqual(recovered.name, "Recovery Marker")
            self.assertEqual(recovered.xp, 321)
            reloaded = load_profile(path)
            self.assertEqual(reloaded.name, "Recovery Marker")
            self.assertEqual(reloaded.xp, 321)

    def test_symlinked_save_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = root / "career.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaises(SaveCorruptionError):
                load_profile(link)


if __name__ == "__main__":
    unittest.main()
