# Persistent Config And Checkpoint Folder Design

## Goal

Keep the user's last GUI/CLI inputs across restarts, explain coordinate assumptions without changing distance math, and let users choose where checkpoint data is saved and resumed.

## Design

Add a small persistence module that stores the last run settings in a local JSON file. The saved values include city, target point, radius, districts, optional crawl limit, and the selected data folder. At startup, GUI and CLI load those values and apply them to the imported `config` module.

Checkpoint files remain named `step1_urls.json` and `step2_details.json`, but their parent folder becomes selectable. `main.py` exposes a setter for the checkpoint directory, and all read/write/reset logic uses the active directory. If the selected directory has checkpoint files, the existing continue/restart menu is shown. If not, the program logs that no checkpoint exists and starts from Step 1.

Coordinate calculation code stays unchanged. Documentation and UI text state that Beike community coordinates are scraped from Beike pages, the target coordinate should use the same coordinate system where possible, and the program uses Haversine directly without coordinate-system conversion.

## Scope

- Modify `main.py`, `gui.py`, `config.py`, `config.example.py`, `README.md`.
- Add `runtime_state.py` and tests for persistence and checkpoint directory behavior.
- Do not change `distance.py` or the Haversine formula.
