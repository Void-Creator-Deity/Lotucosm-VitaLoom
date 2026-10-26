# Archived Legacy Tools

These files are preserved only as migration history. They are not active development
tools for the FrameCore plugin architecture.

Archived here:

- one-off docstring/comment enrichment scripts that can rewrite source files;
- repair scripts for pre-migration indentation or encoding damage;
- legacy gap inventory scripts for the old `core/` + `builtin/` root layout;
- sample branding copy scripts tied to old/generated asset names;
- stale generated audit output.

Use the active commands in `tools/` instead:

- `python tools/check_core_boundaries.py`
- `python tools/check_release_consistency.py`
- `python tools/run_routine_maintenance.py --skip-audit`
- `python tools/build_exe.py --console`
- `python tools/export_player.py`
- `python tools/update_project_lock.py`
