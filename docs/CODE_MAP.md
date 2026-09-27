# 🗺️ Code Map & Symbol Index

> **Agent Token Optimization Notice:**  
> Use this file to locate classes, methods, and line ranges **before** viewing or editing files.  
> Do **NOT** dump entire files into context—request only the targeted line ranges.

---

## 📦 `src/scoring.py` (~3700 lines)

The central briefing, debriefing, scoring, and video analytics application.

### 1. Dive Pool Reference & Helpers (Lines 54 – 202)
- `FAI_RANDOMS: Dict[str, str]`: Lookup table of random formations A–Q.
- `FAI_BLOCKS: Dict[str, str]`: Lookup table of block formations 1–22.
- `parse_formations_string(text: str) -> List[str]`: Splits draw strings into tokens.
- `is_block_formation(code: str) -> bool`: Checks if code is FAI block 1–22.
- `get_block_names(code: str) -> Tuple[str, str]`: Returns initial and closing formation names.
- `expand_draw_to_points_sequence(draw_tokens: List[str]) -> List[Dict[str, Any]]`: Expands draw tokens into cycle points (Randoms = 1 pt, Blocks = 2 pts).
- `format_seconds(seconds: Optional[float], show_decimals: bool = True) -> str`: Formats seconds to `MM:SS.ss` or `SS.ss`.
- `parse_time_string(text: str) -> Optional[float]`: Parses user strings (`14.5`, `14.5s`, `01:15.50`) into seconds float.

### 2. Data Models (Lines 203 – 405)
- `LineShape`, `ArrowShape`, `AngleShape`, `FreehandShape`: Telestration drawing primitives.
- `ScoringPoint` (Line 256):
  - `point_num: int`, `formation: str`, `status: str` (`"APPROVED"` / `"BUST"`), `time_complete: float`, `time_key: Optional[float]`, `notes: str`
  - `hold_time() -> Optional[float]`: $t_{\text{key}} - t_{\text{complete}}$
  - `transition_time(prev_point, exit_time) -> Optional[float]`: $t_{\text{complete}} - t_{\text{ref}}$
  - `is_in_working_time(exit_time, duration) -> bool`: Verifies whether point completed within working time.
- `JumpSession` (Line 309):
  - Session state container (video paths, draw string, exit time, trimmer points, list of `ScoringPoint`).
  - `points_per_cycle() -> int`, `expected_formation_for_point(idx) -> Dict`, `points_in_working_time() -> int`.
  - `average_hold_time()`, `average_transition_time()`.

### 3. Worker & Sub-Widgets (Lines 406 – 1453)
- `VideoCutterDialog(QDialog)` (Line 410): Asynchronous ffmpeg video trimmer (extracts In/Out range without audio `-an`).
- `DrawingOverlayWidget(QWidget)` (Line 508): Transparent glass pane capturing mouse events for telestration (lines, arrows, 3-point angles, freehand).
- `MPVVideoWidget(QWidget)` (Line 724): Embedded `libmpv` video player widget with frame stepping, seek, speed control.
- `DrawingMPVContainer(QWidget)` (Line 827): Composite container synchronizing geometry between MPV video widget and telestration overlay.
- `ScoringTimelineWidget(QWidget)` (Line 872): Interactive graphical timeline with working time window, point badges, key diamonds, and scrubber.
- `DivePoolDialog(QDialog)` (Line 1146): Visual dive pool helper and selector.
- `VideoPathsDialog(QDialog)` (Line 1261): Config dialog for default video folder, quick-link bookmarks, and GoPro SD-card auto-detection.
- `GlobalShortcutFilter(QObject)` (Line 1407): Application-wide event filter ensuring keyboard shortcuts execute regardless of widget focus.

### 4. `DebriefMainWindow(QMainWindow)` (Lines 1454 – 3685)
- **UI Initialization & Styling** (Lines 1459 – 2160):
  - `_init_ui()`: Header bar, video container layout (Cam 1 & Cam 2), timeline bar, scoring control bar, point selection bar, table & analytics panel.
  - `_apply_dark_theme()`: Dark stylesheet.
  - `_init_timer()` / `_on_ui_tick()`: 30Hz timer updating timeline position, working time countdown, and status.
- **Shortcuts & Global Key Handling** (Lines 2189 – 2500):
  - `handle_global_key(event)`: Dispatches `Space` (Play/Pause), `Left/Right` (Frame step), `Shift+Left/Right` (Jump 1s), `T` (Exit timer), `F` (Formation complete), `K` (Key given), `S/1` (Score), `B/0` (Bust), `Esc` (Clear selection / Reset tool).
  - `_show_shortcuts_help()`: Interactive F1 documentation window with tabs for Scoring Guide and Shortcuts.
- **Video Playback & Dual Cam** (Lines 2501 – 2570):
  - `_toggle_play_pause()`, `_step_frame()`, `_seek_to_time()`, `_on_speed_changed()`, `_toggle_dual_cam()`.
- **Quick Links & Video Loading** (Lines 2573 – 2748):
  - `get_default_video_dir()`, `set_default_video_dir()`, `_choose_video_file()`, `_open_raw_video()`, `_load_selected_video1()`, `_open_cam2_video()`.
- **Video Trimming** (Lines 2749 – 2834):
  - `_mark_in_point()`, `_mark_out_point()`, `_cut_video_ffmpeg()`, `_on_video_cut_success()`.
- **Draw Sequence & FAI Blocks** (Lines 2835 – 2996):
  - `_on_draw_changed()`, `_apply_draw_to_existing_points()`, `_update_sequence_chips()`, `_open_3d_explorer_for_formation()`, `_get_next_expected_formation()`.
- **Working Time & Timer** (Lines 2997 – 3024):
  - `_on_wt_preset_changed()`, `_set_exit_timer_now()`, `_reset_exit_timer()`.
- **Point Selection & Editing** (Lines 3025 – 3184):
  - `_update_selection_controls()`, `_set_selected_point_complete_to_current()`, `_set_selected_point_key_to_current()`, `_toggle_selected_point_status()`, `_clear_point_selection()`, `_show_table_context_menu()`, `_on_table_cell_double_clicked()`.
- **Judging & Point Scoring** (Lines 3185 – 3274):
  - `_mark_formation_complete()`, `_mark_key_given()`, `_judge_point()`.
- **Table & Statistics Updates** (Lines 3275 – 3491):
  - `_update_table_and_stats()`: Rebuilds point rows, hold/transition calculation, error highlighting (`⚠️`), average analytics.
  - `_on_table_item_changed()`: In-cell editing for formation, status, completion time, key time, notes.
- **Session Persistence & Report Export** (Lines 3528 – 3672):
  - `_get_debriefs_dir()`: Resolves local `debriefs/` directory.
  - `_save_session_file()`, `_load_session_file()`, `_export_debrief_report()`, `_save_report_to_file()`.

---

## 📦 `src/formation_tool.py` (~1440 lines)

The standalone and integrated 3D formation explorer.

- `Formation3DWidget(QWidget)` (Line 120): Custom OpenGL/QPainter 3D rendering widget showing the 4 flyers, relative orientations, grips, and head switch lines.
- `FormationDetailWidget(QWidget)` (Line 846): Side panel showing slot assignments, FAI codes, grip descriptions, and technical notes.
- `FormationExplorerWindow(QMainWindow)` (Line 1062): Full application window with formation browser, search filter, phase slider (0% to 100% for blocks), and launch button for scoring.

---

## 📦 `src/formation_db.py` (~1300 lines)

FAI 4-Way Dive Pool database and 3D coordinate definitions.

- `Flyer3DState`: 3D position $(x, y, z)$, yaw rotation, head switch state.
- `SlotDetail`: Slot name (Point, Outside Center, Inside Center, Tail), color, grip targets.
- `FormationDefinition`: Code, name, is_block, flyer states for start/close phases, grip definitions.
- `_build_dive_pool()`: Constructs all 16 Randoms (A–Q) and 22 Blocks (1–22).
- `get_formation(code: str) -> Optional[FormationDefinition]`: Retrieval helper.
