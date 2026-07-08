import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import runtime_state


class RuntimeStateTests(unittest.TestCase):
    def test_save_load_and_apply_state_to_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "last_run.json"
            data_dir = Path(tmp) / "data"
            state = {
                "city_code": "gz",
                "city_name": "广州",
                "target_name": "天河北",
                "target_lng": 113.327817,
                "target_lat": 23.145135,
                "radius_km": 1.0,
                "search_districts": ["tianhe"],
                "data_dir": str(data_dir),
                "max_communities": 20,
            }

            runtime_state.save_state(state, state_file)
            loaded = runtime_state.load_state(state_file)

            cfg = SimpleNamespace()
            runtime_state.apply_state_to_config(cfg, loaded)

            self.assertEqual(cfg.CITY_CODE, "gz")
            self.assertEqual(cfg.CITY_NAME, "广州")
            self.assertEqual(cfg.BASE_URL, "https://gz.ke.com")
            self.assertEqual(cfg.TARGET_NAME, "天河北")
            self.assertEqual(cfg.TARGET_LNG, 113.327817)
            self.assertEqual(cfg.TARGET_LAT, 23.145135)
            self.assertEqual(cfg.RADIUS_KM, 1.0)
            self.assertEqual(cfg.SEARCH_DISTRICTS, ["tianhe"])
            self.assertEqual(runtime_state.get_saved_data_dir("fallback", state_file), str(data_dir))

    def test_state_from_config_keeps_checkpoint_folder_and_limit(self):
        cfg = SimpleNamespace(
            CITY_CODE="sh",
            CITY_NAME="上海",
            TARGET_NAME="人民广场",
            TARGET_LNG=121.4737,
            TARGET_LAT=31.2304,
            RADIUS_KM=2.5,
            SEARCH_DISTRICTS=["huangpu"],
        )

        state = runtime_state.state_from_config(cfg, "runs/sh-renminguangchang", 5)

        self.assertEqual(state["city_code"], "sh")
        self.assertEqual(state["city_name"], "上海")
        self.assertEqual(state["data_dir"], "runs/sh-renminguangchang")
        self.assertEqual(state["max_communities"], 5)


if __name__ == "__main__":
    unittest.main()
