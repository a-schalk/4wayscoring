"""
Draw Generator & Training Database Hub Dialog.
Provides FAI AAA draw generation, least-trained weighting, training metrics,
and visual Rhythm XP card previews.
"""

import os
from typing import Optional, List, Dict, Any

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QSpinBox, QComboBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame,
    QMessageBox, QSplitter, QLineEdit, QFileDialog, QApplication
)

import card_manager
from training_db import TrainingDatabase, ALL_RANDOMS, ALL_BLOCKS
from draw_generator import DrawGenerator, GeneratedRound


class DrawGeneratorDialog(QDialog):
    """Integrated Hub for FAI Draw Generation, Training History & Rhythm XP Visualizer."""

    def __init__(self, main_window: Any, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.generator = DrawGenerator()
        self.training_db = self.generator.training_db
        self.current_rounds: List[GeneratedRound] = []

        self.setWindowTitle("🎲 FAI AAA Draw Generator & Training Hub")
        self.resize(980, 680)
        self._init_ui()

        # Initial generation of a 10-round draw
        self._generate_draw()
        # Initial population of training table
        self._refresh_training_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Tabs
        self.tabs = QTabWidget(self)
        self.tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Tab 1: Draw Generator
        tab_draw = QWidget()
        self._setup_draw_tab(tab_draw)
        self.tabs.addTab(tab_draw, "🎲 FAI AAA Draw Generator")

        # Tab 2: Training Database
        tab_stats = QWidget()
        self._setup_training_tab(tab_stats)
        self.tabs.addTab(tab_stats, "📊 Trainings-Datenbank & Häufigkeiten")

        # Tab 3: Rhythm XP Dive Pool Cards
        tab_cards = QWidget()
        self._setup_cards_tab(tab_cards)
        self.tabs.addTab(tab_cards, "🖼️ Rhythm XP Dive Pool Karten")

        layout.addWidget(self.tabs)

        # Bottom Dialog Controls
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Schließen")
        btn_close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    # =========================================================================
    # TAB 1: Draw Generator & Visual Cards
    # =========================================================================
    def _setup_draw_tab(self, parent: QWidget):
        l = QVBoxLayout(parent)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(8)

        # Configuration Bar
        cfg_frame = QFrame()
        cfg_frame.setStyleSheet("background: #18181b; border: 1px solid #3f3f46; border-radius: 6px; padding: 6px;")
        cfg_layout = QHBoxLayout(cfg_frame)
        cfg_layout.setContentsMargins(8, 4, 8, 4)
        cfg_layout.setSpacing(10)

        cfg_layout.addWidget(QLabel("<b>Anzahl Runden:</b>"))
        self.spin_rounds = QSpinBox()
        self.spin_rounds.setRange(1, 20)
        self.spin_rounds.setValue(10)
        self.spin_rounds.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cfg_layout.addWidget(self.spin_rounds)

        cfg_layout.addWidget(QLabel("<b>Modus:</b>"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("🏆 FAI AAA Wettbewerb (5–6 Pkt/Runde)", "fai_aaa")
        self.combo_mode.addItem("🎯 Trainings-Fokus (Selten trainiert zuerst)", "least_trained")
        self.combo_mode.addItem("🔤 Nur Randoms (A–Q)", "randoms_only")
        self.combo_mode.addItem("🧱 Nur Blöcke (3 Blöcke = 6 Pkt)", "blocks_only")
        self.combo_mode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cfg_layout.addWidget(self.combo_mode)

        self.btn_gen = QPushButton("🎲 Draw generieren")
        self.btn_gen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_gen.setStyleSheet("background: #059669; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        self.btn_gen.clicked.connect(self._generate_draw)
        cfg_layout.addWidget(self.btn_gen)

        cfg_layout.addStretch()

        btn_copy_all = QPushButton("📋 Alle Runden kopieren")
        btn_copy_all.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_copy_all.clicked.connect(self._copy_all_rounds)
        cfg_layout.addWidget(btn_copy_all)

        btn_export = QPushButton("💾 Exportieren...")
        btn_export.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_export.clicked.connect(self._export_draw_text)
        cfg_layout.addWidget(btn_export)

        l.addWidget(cfg_frame)

        # Splitter: Left = Rounds list, Right = Round details + Rhythm XP Cards
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Rounds List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("<b>Ausgeloste Runden:</b>"))
        self.list_rounds = QListWidget()
        self.list_rounds.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_rounds.currentRowChanged.connect(self._on_round_selected)
        left_layout.addWidget(self.list_rounds)
        splitter.addWidget(left_widget)

        # Right panel: Round Details & Rhythm XP Cards
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(6)

        # Round Header
        self.lbl_round_title = QLabel("<b>Wähle eine Runde aus</b>")
        self.lbl_round_title.setStyleSheet("font-size: 14px; color: #38bdf8;")
        right_layout.addWidget(self.lbl_round_title)

        # Scroll Area for Formation Cards
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.cards_scroll.setStyleSheet("background: #18181b; border: 1px solid #27272a; border-radius: 6px;")

        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(12, 12, 12, 12)
        self.cards_layout.setSpacing(14)
        self.cards_layout.addStretch()
        self.cards_scroll.setWidget(self.cards_container)

        right_layout.addWidget(self.cards_scroll)

        # Apply to main debriefing button bar
        action_bar = QHBoxLayout()
        self.btn_apply_round = QPushButton("▶️ Diese Runde als aktuelles Draw ins Debriefing übernehmen")
        self.btn_apply_round.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_apply_round.setStyleSheet("background: #0284c7; color: white; font-weight: bold; padding: 8px 14px; border-radius: 4px;")
        self.btn_apply_round.clicked.connect(self._apply_current_round_to_debrief)
        action_bar.addWidget(self.btn_apply_round)

        action_bar.addStretch()

        right_layout.addLayout(action_bar)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        l.addWidget(splitter)

    def _generate_draw(self):
        num_rounds = self.spin_rounds.value()
        mode = self.combo_mode.currentData()
        self.current_rounds = self.generator.generate_draw(num_rounds=num_rounds, mode=mode)

        self.list_rounds.clear()
        for r in self.current_rounds:
            item_text = f"Runde {r.round_number:2d}:  {r.draw_string}  ({r.total_points} Pkt)"
            item = QListWidgetItem(item_text)
            self.list_rounds.addItem(item)

        if self.current_rounds:
            self.list_rounds.setCurrentRow(0)

    def _on_round_selected(self, row: int):
        if not (0 <= row < len(self.current_rounds)):
            return
        rnd = self.current_rounds[row]
        self.lbl_round_title.setText(
            f"🎯 <b>Runde {rnd.round_number}</b>: {rnd.draw_string} &nbsp;|&nbsp; <b>{rnd.total_points} Punkte</b>"
        )

        # Clear existing card widgets
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Render Rhythm XP Cards for each formation in the drawn round
        for i, code in enumerate(rnd.formations):
            card_box = QFrame()
            card_box.setStyleSheet(
                "background: #27272a; border: 1px solid #3f3f46; border-radius: 8px; padding: 6px;"
            )
            c_layout = QVBoxLayout(card_box)
            c_layout.setContentsMargins(6, 6, 6, 6)
            c_layout.setSpacing(4)
            c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            is_blk = code.isdigit()
            pts_badge = "2 Pkt" if is_blk else "1 Pkt"
            badge_color = "#3b82f6" if is_blk else "#10b981"

            lbl_header = QLabel(f"<b>{code}</b> <span style='color:{badge_color};'>({pts_badge})</span>")
            lbl_header.setStyleSheet("font-size: 13px;")
            lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(lbl_header)

            # Image
            pix = card_manager.get_card_pixmap(code, max_width=180, max_height=200)
            lbl_img = QLabel()
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if pix:
                lbl_img.setPixmap(pix)
            else:
                lbl_img.setText(f"<i>Kein Bild für {code}</i>")
                lbl_img.setFixedSize(140, 140)
            c_layout.addWidget(lbl_img)

            # Name
            name = rnd.formation_names[i] if i < len(rnd.formation_names) else code
            lbl_name = QLabel(f"<b>{name}</b>")
            lbl_name.setStyleSheet("color: #e4e4e7; font-size: 11px;")
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(lbl_name)

            # 3D View Button
            btn_3d = QPushButton("🎯 3D Ansicht")
            btn_3d.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_3d.setStyleSheet("background: #1e293b; color: #38bdf8; font-size: 10px; padding: 2px 6px;")
            btn_3d.clicked.connect(lambda ch, c=code: self._open_3d_explorer(c))
            c_layout.addWidget(btn_3d)

            self.cards_layout.addWidget(card_box)

            if i < len(rnd.formations) - 1:
                lbl_arrow = QLabel("➔")
                lbl_arrow.setStyleSheet("color: #71717a; font-size: 16px; font-weight: bold;")
                self.cards_layout.addWidget(lbl_arrow)

        self.cards_layout.addStretch()

    def _apply_current_round_to_debrief(self):
        row = self.list_rounds.currentRow()
        if not (0 <= row < len(self.current_rounds)):
            return
        rnd = self.current_rounds[row]
        if hasattr(self.main_window, 'edit_jump_name'):
            self.main_window.edit_jump_name.setText(f"Runde {rnd.round_number}")
        if hasattr(self.main_window, 'edit_draw'):
            self.main_window.edit_draw.setText(rnd.draw_string)
            self.main_window._on_draw_changed(rnd.draw_string)
        QMessageBox.information(
            self, "Runde übernommen",
            f"Runde {rnd.round_number} ({rnd.draw_string}) wurde erfolgreich als aktuelles Draw ins Debriefing geladen!"
        )
        self.accept()

    def _open_3d_explorer(self, code: str):
        if hasattr(self.main_window, '_open_3d_explorer_for_formation'):
            base = code.split("-")[0]
            self.main_window._open_3d_explorer_for_formation(base, 0)

    def _copy_all_rounds(self):
        if not self.current_rounds:
            return
        lines = [f"Runde {r.round_number:2d}: {r.draw_string} ({r.total_points} Pkt)" for r in self.current_rounds]
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Kopiert", "Alle Runden wurden in die Zwischenablage kopiert!")

    def _export_draw_text(self):
        if not self.current_rounds:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Draw exportieren", "4way_draw.txt", "Text Files (*.txt);;Markdown (*.md)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("# FAI 4-Way Formation Skydiving Draw\n\n")
                    for r in self.current_rounds:
                        names_str = ", ".join(r.formation_names)
                        f.write(f"### Runde {r.round_number}: {r.draw_string} ({r.total_points} Punkte)\n")
                        f.write(f"- Formationen: {names_str}\n\n")
                QMessageBox.information(self, "Gespeichert", f"Draw erfolgreich exportiert nach:\n{os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Konnte Datei nicht schreiben: {e}")

    # =========================================================================
    # TAB 2: Training Database & Frequencies
    # =========================================================================
    def _setup_training_tab(self, parent: QWidget):
        l = QVBoxLayout(parent)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(10)

        # Overview Stats Header
        stat_frame = QFrame()
        stat_frame.setStyleSheet("background: #18181b; border: 1px solid #3f3f46; border-radius: 6px; padding: 6px;")
        stat_layout = QHBoxLayout(stat_frame)
        stat_layout.setContentsMargins(10, 6, 10, 6)

        self.lbl_db_total_sessions = QLabel("Gestrackte Sessions: <b>0</b>")
        self.lbl_db_total_points = QLabel("Formationen absolviert: <b>0</b>")
        self.lbl_db_accuracy = QLabel("Gesamt-Erfolgsquote: <b>0.0%</b>")
        stat_layout.addWidget(self.lbl_db_total_sessions)
        stat_layout.addWidget(self.lbl_db_total_points)
        stat_layout.addWidget(self.lbl_db_accuracy)
        stat_layout.addStretch()

        btn_rescan = QPushButton("🔄 Debriefs-Ordner scannen & synchronisieren")
        btn_rescan.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_rescan.setStyleSheet("background: #3b82f6; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
        btn_rescan.clicked.connect(self._rescan_debriefs)
        stat_layout.addWidget(btn_rescan)

        l.addWidget(stat_frame)

        # Splitter: Table on left, preview on right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Table
        self.table_stats = QTableWidget()
        self.table_stats.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_stats.setColumnCount(9)
        self.table_stats.setHorizontalHeaderLabels([
            "Code", "Name", "Typ", "Trainiert", "Score (+1)", "Bust (0)", "Quote", "Avg Hold", "Avg Trans"
        ])
        self.table_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_stats.horizontalHeader().setStretchLastSection(True)
        self.table_stats.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_stats.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_stats.itemSelectionChanged.connect(self._on_stat_selection_changed)
        splitter.addWidget(self.table_stats)

        # Preview Side Panel
        side_panel = QFrame()
        side_panel.setFixedWidth(240)
        side_panel.setStyleSheet("background: #18181b; border: 1px solid #27272a; border-radius: 6px; padding: 8px;")
        side_layout = QVBoxLayout(side_panel)
        side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.lbl_side_title = QLabel("<b>Details</b>")
        self.lbl_side_title.setStyleSheet("font-size: 13px; color: #38bdf8;")
        self.lbl_side_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self.lbl_side_title)

        self.lbl_side_card = QLabel()
        self.lbl_side_card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self.lbl_side_card)

        self.lbl_side_info = QLabel("<i>Wähle eine Formation in der Tabelle</i>")
        self.lbl_side_info.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        self.lbl_side_info.setWordWrap(True)
        side_layout.addWidget(self.lbl_side_info)

        splitter.addWidget(side_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        l.addWidget(splitter)

    def _refresh_training_table(self):
        rows = self.training_db.get_summary_table_data()

        # Update summary labels
        total_sessions = len(self.training_db.sessions_history)
        total_points = sum(r["jump_count"] for r in rows)
        total_scores = sum(r["score_count"] for r in rows)
        acc = round((total_scores / total_points * 100.0), 1) if total_points > 0 else 0.0

        self.lbl_db_total_sessions.setText(f"Gestrackte Sessions: <b>{total_sessions}</b>")
        self.lbl_db_total_points.setText(f"Formationen absolviert: <b>{total_points}</b>")
        self.lbl_db_accuracy.setText(f"Gesamt-Erfolgsquote: <b>{acc}%</b>")

        self.table_stats.setRowCount(len(rows))
        for i, r in enumerate(rows):
            item_code = QTableWidgetItem(r["code"])
            item_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stats.setItem(i, 0, item_code)

            item_name = QTableWidgetItem(r["name"])
            self.table_stats.setItem(i, 1, item_name)

            item_type = QTableWidgetItem(r["type"])
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stats.setItem(i, 2, item_type)

            # Jump Count
            cnt = r["jump_count"]
            item_cnt = QTableWidgetItem(str(cnt))
            item_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if cnt == 0:
                item_cnt.setBackground(QColor(69, 26, 3))  # Dark amber/brown (0 times trained!)
                item_cnt.setForeground(QColor(251, 191, 36))
            elif cnt >= 5:
                item_cnt.setBackground(QColor(6, 78, 59))  # Dark green
            self.table_stats.setItem(i, 3, item_cnt)

            item_score = QTableWidgetItem(str(r["score_count"]))
            item_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stats.setItem(i, 4, item_score)

            item_bust = QTableWidgetItem(str(r["bust_count"]))
            item_bust.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stats.setItem(i, 5, item_bust)

            # Accuracy
            acc_str = f"{r['accuracy']:.1f}%" if cnt > 0 else "-"
            item_acc = QTableWidgetItem(acc_str)
            item_acc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stats.setItem(i, 6, item_acc)

            # Hold & Trans
            h_str = f"{r['avg_hold']:.2f}s" if r["avg_hold"] is not None else "-"
            t_str = f"{r['avg_trans']:.2f}s" if r["avg_trans"] is not None else "-"
            item_h = QTableWidgetItem(h_str)
            item_h.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_t = QTableWidgetItem(t_str)
            item_t.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stats.setItem(i, 7, item_h)
            self.table_stats.setItem(i, 8, item_t)

    def _rescan_debriefs(self):
        c = self.training_db.scan_debriefs_folder()
        self._refresh_training_table()
        QMessageBox.information(
            self, "Synchronisiert",
            f"Debriefs-Ordner erfolgreich synchronisiert: {c} Sessions eingelesen und aktualisiert!"
        )

    def _on_stat_selection_changed(self):
        row = self.table_stats.currentRow()
        if row < 0:
            return
        code_item = self.table_stats.item(row, 0)
        if not code_item:
            return
        code = code_item.text()
        stat = self.training_db.formation_stats.get(code)
        if not stat:
            return

        self.lbl_side_title.setText(f"<b>{code}: {stat.name}</b>")
        pix = card_manager.get_card_pixmap(code, max_width=200, max_height=200)
        if pix:
            self.lbl_side_card.setPixmap(pix)
        else:
            self.lbl_side_card.setText(f"<i>Keine Bildkarte für {code}</i>")

        info_lines = [
            f"<b>Typ:</b> {'Block (2 Pkt)' if stat.is_block else 'Random (1 Pkt)'}",
            f"<b>Trainiert:</b> {stat.jump_count}x",
            f"<b>Punkte:</b> {stat.score_count} ✓ | <b>Busts:</b> {stat.bust_count} ✗",
            f"<b>Erfolgsquote:</b> {stat.accuracy}%",
            f"<b>Avg Hold Time:</b> {stat.average_hold or '--'} s",
            f"<b>Avg Transition:</b> {stat.average_transition or '--'} s",
            f"<b>Zuletzt trainiert:</b> {stat.last_trained or 'Nie'}",
        ]
        self.lbl_side_info.setText("<br>".join(info_lines))

    # =========================================================================
    # TAB 3: Rhythm XP Cards Browser
    # =========================================================================
    def _setup_cards_tab(self, parent: QWidget):
        l = QVBoxLayout(parent)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(8)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("<b>Kategorie:</b>"))
        self.combo_card_filter = QComboBox()
        self.combo_card_filter.addItem("Alle (Randoms & Blöcke)", "all")
        self.combo_card_filter.addItem("Nur Randoms (A–Q)", "randoms")
        self.combo_card_filter.addItem("Nur Blöcke (1–22)", "blocks")
        self.combo_card_filter.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_card_filter.currentIndexChanged.connect(self._refresh_cards_grid)
        filter_bar.addWidget(self.combo_card_filter)

        filter_bar.addSpacing(15)
        filter_bar.addWidget(QLabel("<b>Suche:</b>"))
        self.edit_card_search = QLineEdit()
        self.edit_card_search.setPlaceholderText("Code oder Name suchen...")
        self.edit_card_search.textChanged.connect(self._refresh_cards_grid)
        filter_bar.addWidget(self.edit_card_search)

        filter_bar.addStretch()
        l.addLayout(filter_bar)

        # Scroll area for cards grid
        self.cards_browser_scroll = QScrollArea()
        self.cards_browser_scroll.setWidgetResizable(True)
        self.cards_browser_scroll.setStyleSheet("background: #18181b; border: 1px solid #27272a; border-radius: 6px;")

        self.cards_grid_widget = QWidget()
        self.cards_grid_layout = QVBoxLayout(self.cards_grid_widget)
        self.cards_grid_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_grid_layout.setSpacing(10)
        self.cards_browser_scroll.setWidget(self.cards_grid_widget)

        l.addWidget(self.cards_browser_scroll)

        self._refresh_cards_grid()

    def _refresh_cards_grid(self):
        while self.cards_grid_layout.count():
            item = self.cards_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cat = self.combo_card_filter.currentData()
        search = self.edit_card_search.text().strip().upper()

        codes = []
        if cat in ("all", "randoms"):
            codes.extend(ALL_RANDOMS)
        if cat in ("all", "blocks"):
            codes.extend(ALL_BLOCKS)

        # Filter by search
        filtered = []
        for c in codes:
            stat = self.training_db.formation_stats.get(c)
            name = stat.name.upper() if stat else ""
            if not search or (search in c or search in name):
                filtered.append(c)

        # Build rows of 4 cards each
        current_row_layout = None
        for i, code in enumerate(filtered):
            if i % 4 == 0:
                row_widget = QWidget()
                current_row_layout = QHBoxLayout(row_widget)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setSpacing(10)
                self.cards_grid_layout.addWidget(row_widget)

            card_frame = QFrame()
            card_frame.setStyleSheet("background: #27272a; border: 1px solid #3f3f46; border-radius: 6px; padding: 4px;")
            cf_layout = QVBoxLayout(card_frame)
            cf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            stat = self.training_db.formation_stats.get(code)
            lbl_title = QLabel(f"<b>{code}</b>: {stat.name if stat else ''}")
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cf_layout.addWidget(lbl_title)

            pix = card_manager.get_card_pixmap(code, max_width=160, max_height=180)
            lbl_pix = QLabel()
            lbl_pix.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if pix:
                lbl_pix.setPixmap(pix)
            cf_layout.addWidget(lbl_pix)

            current_row_layout.addWidget(card_frame)

        # Fill remaining slots of last row
        if current_row_layout and len(filtered) % 4 != 0:
            for _ in range(4 - (len(filtered) % 4)):
                current_row_layout.addStretch()

        self.cards_grid_layout.addStretch()
