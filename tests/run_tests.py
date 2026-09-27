#!/usr/bin/env python3
"""
Fast Headless Test Suite for FAI 4-Way Debriefing & Scoring Tool.
Designed for high speed and token-efficient agent verification.
Usage:
    python3 tests/run_tests.py
"""

import os
import sys
import time
import py_compile

# Configure headless offscreen mode before importing PyQt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def test_syntax():
    """Verify syntax of all project Python files."""
    files = [
        os.path.join(PROJECT_ROOT, "run.py"),
        os.path.join(SRC_DIR, "scoring.py"),
        os.path.join(SRC_DIR, "formation_tool.py"),
        os.path.join(SRC_DIR, "formation_db.py"),
        os.path.join(SRC_DIR, "__init__.py"),
    ]
    for f in files:
        py_compile.compile(f, doraise=True)
    return len(files)


def test_dive_pool_logic():
    """Test FAI block detection, names, and sequence expansion."""
    from scoring import (
        is_block_formation,
        get_block_names,
        expand_draw_to_points_sequence,
        JumpSession
    )

    # Blocks vs Randoms
    assert is_block_formation("1") is True
    assert is_block_formation("12") is True
    assert is_block_formation("22") is True
    assert is_block_formation("A") is False
    assert is_block_formation("Q") is False
    assert is_block_formation("23") is False

    n1, n2 = get_block_names("12")
    assert n1 == "Bundy" and n2 == "Bundy"

    n1, n2 = get_block_names("10")
    assert n1 == "Diamond" and n2 == "Bunyip"

    # Sequence Expansion
    seq = expand_draw_to_points_sequence(["A", "12", "7", "B"])
    codes = [x["code"] for x in seq]
    assert codes == ["A", "12-1", "12-2", "7-1", "7-2", "B"]

    # JumpSession cycles
    sess = JumpSession(draw_string="A - 12 - 7 - B")
    assert sess.points_per_cycle() == 6
    assert sess.expected_formation_for_point(0)["code"] == "A"
    assert sess.expected_formation_for_point(1)["code"] == "12-1"
    assert sess.expected_formation_for_point(2)["code"] == "12-2"
    assert sess.expected_formation_for_point(5)["code"] == "B"
    assert sess.expected_formation_for_point(6)["code"] == "A"


def test_timing_and_models():
    """Test timing calculations, hold time, transition time, and working time."""
    from scoring import ScoringPoint, JumpSession, parse_time_string

    # Parser
    assert parse_time_string("14.5") == 14.5
    assert parse_time_string("14.5s") == 14.5
    assert parse_time_string("01:15.50") == 75.50
    assert parse_time_string("-") is None
    assert parse_time_string("invalid") is None

    # Points & timing math
    p1 = ScoringPoint(point_num=1, formation="A", status="APPROVED", time_complete=5.0, time_key=7.5)
    assert p1.hold_time() == 2.5
    assert p1.transition_time(prev_point=None, exit_time=2.0) == 3.0

    p2 = ScoringPoint(point_num=2, formation="12-1", status="APPROVED", time_complete=10.0, time_key=12.0)
    assert p2.hold_time() == 2.0
    assert p2.transition_time(prev_point=p1, exit_time=2.0) == 2.5  # 10.0 - 7.5

    # Negative timing error detection
    p_err = ScoringPoint(point_num=3, formation="12-2", status="APPROVED", time_complete=15.0, time_key=13.0)
    assert p_err.hold_time() == -2.0  # Must expose negative delta, not mask with 0

    # Session stats
    sess = JumpSession(exit_time=2.0, working_time_duration=35.0, points=[p1, p2])
    assert sess.points_in_working_time() == 2
    assert sess.total_score() == 2
    assert sess.average_hold_time() == 2.25

    # Point out of working time
    p_late = ScoringPoint(point_num=3, formation="12-2", status="APPROVED", time_complete=38.0, time_key=40.0)
    sess.points.append(p_late)
    assert sess.points_in_working_time() == 2
    assert sess.total_score() == 3


def test_gui_and_interactions():
    """Test GUI initialization, point selection, table updates, and draw update."""
    from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
    app = QApplication.instance() or QApplication(sys.argv)

    # Mock blocking dialogs
    QDialog.exec = lambda self: 1
    QMessageBox.question = lambda *a, **kw: QMessageBox.StandardButton.Yes
    QMessageBox.information = lambda *a, **kw: None
    QMessageBox.warning = lambda *a, **kw: None

    from scoring import DebriefMainWindow, ScoringPoint

    w = DebriefMainWindow()
    w.session.exit_time = 10.0
    w.edit_draw.setText("A - 12 - 7 - B")
    w._on_draw_changed("A - 12 - 7 - B")

    # Add points
    p1 = ScoringPoint(point_num=1, formation="A", status="APPROVED", time_complete=14.0, time_key=16.0)
    p2 = ScoringPoint(point_num=2, formation="12-1", status="APPROVED", time_complete=18.5, time_key=20.0)
    w.session.points = [p1, p2]
    w._update_table_and_stats()

    # Selection mode
    w._on_timeline_point_clicked(1)
    assert w.selected_point_index == 1
    assert not w.btn_set_sel_key.isHidden()

    w._set_selected_point_key_to_current(21.5)
    assert p2.time_key == 21.5
    assert p2.hold_time() == 3.0

    w._toggle_selected_point_status()
    assert p2.status == "BUST"
    w._toggle_selected_point_status()
    assert p2.status == "APPROVED"

    w._clear_point_selection()
    assert w.selected_point_index is None
    assert w.btn_set_sel_key.isHidden()

    # Apply draw change to existing points
    w.edit_draw.setText("B - 1 - C")
    w._apply_draw_to_existing_points()
    assert w.session.points[0].formation == "B"
    assert w.session.points[1].formation == "1-1"
    assert w.session.points[1].time_key == 21.5

    # Direct in-cell editing
    item_key = w.points_table.item(1, 4)
    item_key.setText("22.5s")
    assert w.session.points[1].time_key == 22.5


def test_card_manager():
    """Test Rhythm XP formation card path resolution and pixmap loading."""
    import card_manager

    # Randoms
    assert card_manager.get_card_path("A") is not None
    assert card_manager.get_card_path("Q") is not None
    pix_a = card_manager.get_card_pixmap("A", max_width=100, max_height=100)
    assert pix_a is not None and not pix_a.isNull()

    # Blocks (full and split parts)
    assert card_manager.get_card_path("12") is not None
    assert card_manager.get_card_path("12-1") is not None
    assert card_manager.get_card_path("12-2") is not None
    pix_12 = card_manager.get_card_pixmap("12", max_width=100, max_height=100)
    assert pix_12 is not None and not pix_12.isNull()


def test_training_db_and_draw_generator():
    """Test TrainingDatabase indexing and FAI AAA DrawGenerator rules."""
    from training_db import TrainingDatabase
    from draw_generator import DrawGenerator
    from draw_dialog import DrawGeneratorDialog
    from scoring import DebriefMainWindow

    # Training DB
    db = TrainingDatabase()
    assert len(db.formation_stats) == 39
    db.scan_debriefs_folder()
    least = db.get_least_trained_formations()
    assert len(least) == 39
    # Least trained should be sorted ascending by jump_count
    assert least[0][1] <= least[-1][1]

    # Draw Generator: FAI AAA Rules (10 rounds)
    gen = DrawGenerator(training_db=db)
    rounds = gen.generate_draw(num_rounds=10, mode="fai_aaa", seed=123)
    assert len(rounds) == 10
    for r in rounds:
        assert 5 <= r.total_points <= 6
        # No duplicate formation in a round
        assert len(r.formations) == len(set(r.formations))
        # Points tally verification
        expected_pts = sum(2 if f.isdigit() else 1 for f in r.formations)
        assert expected_pts == r.total_points

    # Least trained mode
    lt_rounds = gen.generate_draw(num_rounds=5, mode="least_trained", seed=123)
    assert len(lt_rounds) == 5
    for r in lt_rounds:
        assert 5 <= r.total_points <= 6

    # DrawGeneratorDialog offscreen test
    w = DebriefMainWindow()
    dlg = DrawGeneratorDialog(main_window=w)
    assert len(dlg.current_rounds) >= 1
    assert dlg.table_stats.rowCount() == 39
    # Test applying round to main window
    dlg.list_rounds.setCurrentRow(0)
    first_round = dlg.current_rounds[0]
    dlg._apply_current_round_to_debrief()
    assert w.edit_draw.text() == first_round.draw_string


def main():
    start = time.time()
    print("=" * 60)
    print("🚀 FAI 4-Way Debriefing Suite: Automated Headless Test Runner")
    print("=" * 60)

    suites = [
        ("Python Syntax & Compilation", test_syntax),
        ("FAI Dive Pool & Sequence Logic", test_dive_pool_logic),
        ("Timing Math & Working Time Models", test_timing_and_models),
        ("GUI Offscreen, Selection & Table Edit", test_gui_and_interactions),
        ("Rhythm XP Card Manager & Pixmaps", test_card_manager),
        ("Training DB & FAI AAA Draw Generator", test_training_db_and_draw_generator),
    ]

    passed = 0
    for name, func in suites:
        t0 = time.time()
        try:
            func()
            elapsed = time.time() - t0
            print(f"  ✅ PASS: {name} ({elapsed:.3f}s)")
            passed += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ❌ FAIL: {name} ({elapsed:.3f}s)")
            print(f"     Error: {e}")
            sys.exit(1)

    total_elapsed = time.time() - start
    print("-" * 60)
    print(f"✨ All {passed}/{len(suites)} test suites passed successfully in {total_elapsed:.2f}s!")
    print("=" * 60)
    # Clean exit to prevent libmpv headless teardown issues
    os._exit(0)


if __name__ == "__main__":
    main()
