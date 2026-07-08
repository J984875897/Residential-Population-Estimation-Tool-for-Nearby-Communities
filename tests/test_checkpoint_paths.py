import tempfile
import unittest
from pathlib import Path

import main


class CheckpointPathTests(unittest.TestCase):
    def tearDown(self):
        main.set_checkpoint_dir("checkpoints")

    def test_set_checkpoint_dir_controls_checkpoint_files_and_json_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "custom-data"
            main.set_checkpoint_dir(data_dir)
            step1, step2 = main.get_checkpoint_files()

            self.assertEqual(step1, data_dir / "step1_urls.json")
            self.assertEqual(step2, data_dir / "step2_details.json")

            main._save_json(step1, {"urls": ["https://gz.ke.com/xiaoqu/123/"]})

            self.assertTrue(step1.exists())
            self.assertEqual(main._load_json(step1)["urls"], ["https://gz.ke.com/xiaoqu/123/"])


if __name__ == "__main__":
    unittest.main()
