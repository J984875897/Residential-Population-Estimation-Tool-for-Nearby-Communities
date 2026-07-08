# Persistent Config And Checkpoint Folder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist the user's last run inputs and make checkpoint storage user-selectable.

**Architecture:** A new `runtime_state.py` module owns JSON persistence and applying saved values to `config`. `main.py` owns the active checkpoint directory through a setter. `gui.py` exposes a data folder picker and saves inputs before launching the scraper.

**Tech Stack:** Python standard library, Tkinter, existing JSON checkpoint files, pytest-compatible tests using `unittest`.

## Global Constraints

- Keep coordinate calculation code unchanged.
- Use local JSON files only; add no new third-party dependencies.
- Keep existing checkpoint file names: `step1_urls.json` and `step2_details.json`.
- If a selected folder has no checkpoint files, tell the user and start from Step 1.

---

### Task 1: Runtime State Persistence

**Files:**
- Create: `runtime_state.py`
- Test: `tests/test_runtime_state.py`

**Interfaces:**
- Produces: `load_state(path: Path = STATE_FILE) -> dict`, `save_state(state: dict, path: Path = STATE_FILE) -> None`, `apply_state_to_config(config_module, state: dict) -> None`, `state_from_config(config_module, data_dir: str, max_communities: int | None = None) -> dict`, `get_saved_data_dir(default: str = "checkpoints") -> str`

- [ ] Write failing tests for round-trip save/load and applying saved config values.
- [ ] Run `python3 -m unittest tests.test_runtime_state -v` and confirm missing-module failure.
- [ ] Implement `runtime_state.py`.
- [ ] Re-run the runtime-state tests and confirm pass.

### Task 2: Checkpoint Directory Selection In Main

**Files:**
- Modify: `main.py`
- Test: `tests/test_checkpoint_paths.py`

**Interfaces:**
- Consumes: `runtime_state.get_saved_data_dir`
- Produces: `set_checkpoint_dir(path) -> None`, `get_checkpoint_dir() -> Path`, `get_checkpoint_files() -> tuple[Path, Path]`

- [ ] Write failing tests proving `set_checkpoint_dir` changes where `_save_json`, `_load_json`, and reset/checkpoint detection look.
- [ ] Run `python3 -m unittest tests.test_checkpoint_paths -v` and confirm failure.
- [ ] Replace fixed checkpoint path usage with helper functions.
- [ ] Add CLI folder prompt before normal run and `--reset`.
- [ ] Re-run checkpoint tests and existing import tests.

### Task 3: GUI Data Folder And Saved Inputs

**Files:**
- Modify: `gui.py`

**Interfaces:**
- Consumes: `runtime_state.load_state`, `runtime_state.apply_state_to_config`, `runtime_state.save_state`, `runtime_state.state_from_config`
- Consumes: `main.set_checkpoint_dir` indirectly through the `data_dir` argument added to `main.main`

- [ ] Initialize GUI fields from saved state.
- [ ] Add a data folder entry and "选择..." button using `filedialog.askdirectory`.
- [ ] Save current inputs before switching to the run window.
- [ ] Pass selected data folder to the scraper entry point.

### Task 4: Coordinate Documentation

**Files:**
- Modify: `config.py`
- Modify: `config.example.py`
- Modify: `README.md`
- Modify: `gui.py`

**Interfaces:**
- Produces: user-facing explanation only; no distance-code change.

- [ ] Update coordinate comments and README notes.
- [ ] Replace GUI "not written to config.py" copy with saved-input and coordinate notes.
- [ ] Run syntax/import checks.
