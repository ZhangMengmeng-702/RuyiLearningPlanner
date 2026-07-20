"""用户画像管理测试"""
import os, json, tempfile, unittest
from src.profile_manager import ProfileManager, Profile

class TestProfileManager(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.mgr = ProfileManager(data_dir=self.tmp_dir)

    def tearDown(self):
        for f in os.listdir(self.tmp_dir):
            os.remove(os.path.join(self.tmp_dir, f))
        os.rmdir(self.tmp_dir)

    def test_create_and_get(self):
        profile = self.mgr.create("user_001")
        self.assertEqual(profile.user_id, "user_001")
        self.assertFalse(profile.is_complete())

        fetched = self.mgr.get("user_001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.user_id, "user_001")

    def test_get_nonexistent_returns_none(self):
        self.assertIsNone(self.mgr.get("nonexistent"))

    def test_update_sets_fields(self):
        self.mgr.create("user_002")
        updated = self.mgr.update("user_002",
                                  goal="学Python",
                                  current_level="beginner",
                                  hours_per_week=10,
                                  preference="hands-on")
        self.assertTrue(updated.is_complete())
        self.assertEqual(updated.goal, "学Python")

    def test_save_persists_to_file(self):
        self.mgr.create("user_003")
        path = os.path.join(self.tmp_dir, "user_003.json")
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["user_id"], "user_003")

if __name__ == "__main__":
    unittest.main()