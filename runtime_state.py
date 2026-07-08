"""
Persist the last GUI/CLI inputs without modifying config.py.
"""

import json
from pathlib import Path
from typing import Optional


STATE_FILE = Path("last_run_config.json")
DEFAULT_DATA_DIR = "checkpoints"


def load_state(path: Path = STATE_FILE) -> dict:
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(state: dict, path: Path = STATE_FILE) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_state_to_config(config_module, state: dict) -> None:
    if not state:
        return

    city_code = str(state.get("city_code") or getattr(config_module, "CITY_CODE", "")).strip().lower()
    if city_code:
        config_module.CITY_CODE = city_code
        config_module.BASE_URL = f"https://{city_code}.ke.com"

    if state.get("city_name"):
        config_module.CITY_NAME = str(state["city_name"])
    if state.get("target_name"):
        config_module.TARGET_NAME = str(state["target_name"])
    if state.get("target_lng") is not None:
        config_module.TARGET_LNG = float(state["target_lng"])
    if state.get("target_lat") is not None:
        config_module.TARGET_LAT = float(state["target_lat"])
    if state.get("radius_km") is not None:
        config_module.RADIUS_KM = float(state["radius_km"])
    if state.get("search_districts"):
        config_module.SEARCH_DISTRICTS = list(state["search_districts"])


def state_from_config(config_module, data_dir: str, max_communities: Optional[int] = None) -> dict:
    return {
        "city_code": config_module.CITY_CODE,
        "city_name": config_module.CITY_NAME,
        "target_name": config_module.TARGET_NAME,
        "target_lng": config_module.TARGET_LNG,
        "target_lat": config_module.TARGET_LAT,
        "radius_km": config_module.RADIUS_KM,
        "search_districts": list(config_module.SEARCH_DISTRICTS),
        "data_dir": str(data_dir or DEFAULT_DATA_DIR),
        "max_communities": max_communities,
    }


def get_saved_data_dir(default: str = DEFAULT_DATA_DIR, path: Path = STATE_FILE) -> str:
    state = load_state(path)
    return str(state.get("data_dir") or default)
