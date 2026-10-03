"""
FAI 4-Way Skydiving Debriefing & Scoring System
Personal briefing and debriefing tool for 4-way formation skydiving teams.

Features:
- Video Trimmer / Cutter (GoPro footage without audio using ffmpeg)
- FAI 4-Way dive pool & jump sequence management
- Working Time Timer (35s competition, 20s short, 60s training, custom)
- Point judging: Counted / Approved (+1) and Busted (0)
- Formation Finished & Key Given event tracking (Hold time & Transition time calculation)
- Interactive Graphical Timeline with approved/busted point representation & scrubber
- Frame-accurate video playback with speed control (0.1x to 2.0x) and frame stepping
- Telestration Glass Pane Overlay (Lines, Arrows, 3-point Angles with degrees, Freehand, Undo, Clear)
- Debrief Analytics: Hold times, Transition times, Cycle Pace, Scorecard
- Session Save / Load (JSON) and Debrief Report Export (Markdown/Text)
"""

import sys
import os
import math
import json
import re
import locale
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union, Dict, Tuple, Any

# Set C numeric locale before importing mpv
try:
    locale.setlocale(locale.LC_NUMERIC, 'C')
except Exception:
    pass

from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, pyqtSignal, QObject, QTimer, QProcess, QEvent, QSettings, QUrl
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush, QPolygonF, QPainterPath,
    QKeySequence, QShortcut, QAction, QIcon
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSlider, QLabel, QTableWidget, QTableWidgetItem,
    QFileDialog, QHeaderView, QSplitter, QButtonGroup, QRadioButton,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QProgressBar,
    QMessageBox, QDialog, QTextEdit, QPlainTextEdit, QFrame, QGroupBox, QToolTip,
    QCheckBox, QAbstractItemView, QMenu, QListWidget, QListWidgetItem, QTabWidget,
    QSizePolicy
)

try:
    import mpv
except (OSError, ImportError):
    print("FEHLER: libmpv oder das mpv Python-Modul wurde nicht gefunden.")
    sys.exit(1)


# =====================================================================
# FAI 4-Way Formation Skydiving Dive Pool Reference Data
# =====================================================================

try:
    import formation_db
    FAI_RANDOMS: Dict[str, str] = {
        f.code: f.name for f in formation_db.get_all_formations() if not f.is_block
    }
    FAI_BLOCKS: Dict[str, str] = {
        f.code: f.name for f in formation_db.get_all_formations() if f.is_block
    }
except Exception:
    FAI_RANDOMS = {
        "A": "Unipod", "B": "Stairstep Diamond", "C": "Murphy Flake", "D": "Yuan",
        "E": "Meeker", "F": "Open Accordion", "G": "Cataccord", "H": "Bow",
        "I": "Satellite", "J": "Donut", "K": "Hook", "L": "Adder",
        "M": "Star", "N": "Crank", "O": "Satellite", "P": "Sidebody", "Q": "Phalanx",
    }
    FAI_BLOCKS = {
        "1": "Molar - Molar", "2": "Sidebody Donut - Sideflake Donut",
        "3": "Sideflake Opal - Turf", "4": "Monopod - Monopod",
        "5": "Opal - Opal", "6": "Stardian - Stardian",
        "7": "Sidebuddies - Sidebuddies", "8": "Canadian Tee - Canadian Tee",
        "9": "Cat + Accordion - Cat + Accordion", "10": "Diamond - Bunyip",
        "11": "Photon - Photon", "12": "Bundy - Bundy",
        "13": "Mixed Accordion - Mixed Accordion", "14": "Bipole - Bipole",
        "15": "Caterpillar - Caterpillar", "16": "Compressed Accordion - Box",
        "17": "Danish Tee - Murphy", "18": "Zircon - Zircon",
        "19": "Ritz - Ice Pick", "20": "Piver - Viper",
        "21": "Zig Zag - Marquis", "22": "Tee - Chinese Tee",
    }


def parse_formations_string(text: str) -> List[str]:
    """Parses a jump draw string into individual formation tokens."""
    tokens = [t.strip().upper() for t in re.split(r'[-,\s/]+', text) if t.strip()]
    return tokens


def is_block_formation(code: str) -> bool:
    """Prüft, ob ein Formations-Code einen FAI-Block (1-22) darstellt."""
    clean = re.sub(r'[-._].*$', '', code.strip())
    return clean in FAI_BLOCKS or (clean.isdigit() and 1 <= int(clean) <= 22)


def get_block_names(code: str) -> Tuple[str, str]:
    """Liefert (initial_name, second_name) für einen Block-Code."""
    clean = re.sub(r'[-._].*$', '', code.strip())
    name = FAI_BLOCKS.get(clean, "")
    if " - " in name:
        parts = name.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return name, name


def expand_draw_to_points_sequence(draw_tokens: List[str]) -> List[Dict[str, Any]]:
    """
    Entfaltet die Draw-Tokens in eine Sequenz gewerteter Punkte für einen Zyklus.
    - Randoms (A-Q): 1 Punkt (z.B. 'A')
    - FAI Blöcke (1-22): 2 getrennte Punkte (z.B. '12-1' für Initial und '12-2' für Close)
    """
    seq: List[Dict[str, Any]] = []
    for token in draw_tokens:
        clean = token.strip().upper()
        # Falls bereits mit Unterteilung eingegeben (z.B. 12-1 oder 12.2)
        m = re.match(r'^(\d+)[-._]([12])$', clean)
        if m:
            base, part = m.group(1), int(m.group(2))
            n1, n2 = get_block_names(base)
            name = n1 if part == 1 else n2
            seq.append({
                'code': f"{base}-{part}",
                'base': base,
                'part': part,
                'name': name,
                'is_block': True
            })
        elif is_block_formation(clean):
            base = re.sub(r'[-._].*$', '', clean)
            n1, n2 = get_block_names(base)
            seq.append({
                'code': f"{base}-1",
                'base': base,
                'part': 1,
                'name': n1,
                'is_block': True
            })
            seq.append({
                'code': f"{base}-2",
                'base': base,
                'part': 2,
                'name': n2,
                'is_block': True
            })
        else:
            name = FAI_RANDOMS.get(clean, clean)
            seq.append({
                'code': clean,
                'base': clean,
                'part': 0,
                'name': name,
                'is_block': False
            })
    return seq


def format_seconds(seconds: Optional[float], show_decimals: bool = True) -> str:
    """Formats float seconds as MM:SS.ss or SS.ss."""
    if seconds is None:
        return "--:--"
    if seconds < 0:
        return f"-{format_seconds(abs(seconds), show_decimals)}"
    mins = int(seconds // 60)
    secs = seconds % 60
    if mins > 0:
        if show_decimals:
            return f"{mins:02d}:{secs:05.2f}"
        return f"{mins:02d}:{int(secs):02d}"
    else:
        if show_decimals:
            return f"{secs:05.2f}s"
        return f"{int(secs):02d}s"


def parse_time_string(text: str) -> Optional[float]:
    """Parst Zeiteingaben (z.B. '01:14.50', '14.5s', '14.5') in Sekunden (float)."""
    text = text.strip()
    if not text or text in ("-", "--:--", "--"):
        return None
    text = text.rstrip("sS").strip()
    try:
        if ":" in text:
            parts = text.split(":")
            if len(parts) == 2:
                mins = float(parts[0])
                secs = float(parts[1])
                sign = -1.0 if text.startswith("-") else 1.0
                return sign * (abs(mins) * 60.0 + abs(secs))
            elif len(parts) == 3:
                hrs = float(parts[0])
                mins = float(parts[1])
                secs = float(parts[2])
                return hrs * 3600.0 + mins * 60.0 + secs
        return float(text)
    except Exception:
        return None


# =====================================================================
# Data Models
# =====================================================================

@dataclass
class LineShape:
    p1: QPointF
    p2: QPointF
    color: QColor = field(default_factory=lambda: QColor(255, 215, 0))
    width: int = 3


@dataclass
class ArrowShape:
    p1: QPointF
    p2: QPointF
    color: QColor = field(default_factory=lambda: QColor(255, 215, 0))
    width: int = 3


@dataclass
class AngleShape:
    vertex: QPointF  # Scheitelpunkt
    p1: QPointF      # Schenkel 1
    p2: QPointF      # Schenkel 2
    color: QColor = field(default_factory=lambda: QColor(0, 230, 118))
    width: int = 3

    def calculate_angle(self) -> float:
        """Calculates angle in degrees between legs."""
        v1 = QPointF(self.p1.x() - self.vertex.x(), self.p1.y() - self.vertex.y())
        v2 = QPointF(self.p2.x() - self.vertex.x(), self.p2.y() - self.vertex.y())
        angle1 = math.atan2(v1.y(), v1.x())
        angle2 = math.atan2(v2.y(), v2.x())
        angle_deg = math.degrees(angle2 - angle1)
        if angle_deg < 0:
            angle_deg += 360
        if angle_deg > 180:
            angle_deg = 360 - angle_deg
        return angle_deg


@dataclass
class FreehandShape:
    points: List[QPointF] = field(default_factory=list)
    color: QColor = field(default_factory=lambda: QColor(255, 215, 0))
    width: int = 3


DrawingShape = Union[LineShape, ArrowShape, AngleShape, FreehandShape]


@dataclass
class ScoringPoint:
    point_num: int
    formation: str
    status: str  # "APPROVED" or "BUST"
    time_complete: float
    time_key: Optional[float] = None
    notes: str = ""

    def hold_time(self) -> Optional[float]:
        """Calculates hold duration between completion and key."""
        if self.time_key is not None and self.time_complete is not None:
            return round(self.time_key - self.time_complete, 3)
        return None

    def transition_time(self, prev_point: Optional['ScoringPoint'], exit_time: Optional[float] = None) -> Optional[float]:
        """Calculates transition time from previous key to this formation completion."""
        if prev_point is not None:
            ref_time = prev_point.time_key if prev_point.time_key is not None else prev_point.time_complete
            if ref_time is not None:
                return round(self.time_complete - ref_time, 3)
        elif exit_time is not None:
            return round(self.time_complete - exit_time, 3)
        return None

    def is_in_working_time(self, exit_time: Optional[float], duration: float = 35.0) -> bool:
        """Prüft, ob der Punkt innerhalb der Arbeitszeit ab Exit vollendet wurde."""
        if exit_time is None:
            return True
        return self.time_complete <= (exit_time + duration)

    def to_dict(self) -> dict:
        return {
            "point_num": self.point_num,
            "formation": self.formation,
            "status": self.status,
            "time_complete": self.time_complete,
            "time_key": self.time_key,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ScoringPoint':
        return cls(
            point_num=data["point_num"],
            formation=data["formation"],
            status=data["status"],
            time_complete=data["time_complete"],
            time_key=data.get("time_key"),
            notes=data.get("notes", "")
        )


@dataclass
class JumpSession:
    jump_name: str = "Round 1"
    video_path: str = ""
    video_path_cam2: str = ""
    cam2_offset: float = 0.0
    draw_string: str = "A - 12 - 7 - B"
    working_time_duration: float = 35.0
    exit_time: Optional[float] = None
    in_point: Optional[float] = None
    out_point: Optional[float] = None
    points: List[ScoringPoint] = field(default_factory=list)

    @property
    def formations(self) -> List[str]:
        return parse_formations_string(self.draw_string)

    @property
    def draw_sequence(self) -> List[Dict[str, Any]]:
        """Returns expanded points sequence for 1 cycle of this draw (Blocks = 2 points)."""
        return expand_draw_to_points_sequence(self.formations)

    def points_per_cycle(self) -> int:
        seq = self.draw_sequence
        return len(seq) if seq else 1

    def expected_formation_for_point(self, point_index: int) -> Dict[str, Any]:
        """Returns expected formation info dict for a 0-indexed point."""
        seq = self.draw_sequence
        if not seq:
            return {'code': 'A', 'base': 'A', 'part': 0, 'name': 'A', 'is_block': False}
        idx = point_index % len(seq)
        return seq[idx]

    def points_in_working_time(self) -> int:
        """Returns count of approved points completed within working time."""
        if self.exit_time is None:
            return self.total_score()
        return sum(
            1 for p in self.points
            if p.status == "APPROVED" and p.is_in_working_time(self.exit_time, self.working_time_duration)
        )

    def total_score(self) -> int:
        return sum(1 for p in self.points if p.status == "APPROVED")

    def total_busts(self) -> int:
        return sum(1 for p in self.points if p.status == "BUST")

    def average_hold_time(self) -> Optional[float]:
        holds = [p.hold_time() for p in self.points if p.hold_time() is not None and p.hold_time() >= 0]
        if holds:
            return round(sum(holds) / len(holds), 3)
        return None

    def average_transition_time(self) -> Optional[float]:
        transitions = []
        for i, p in enumerate(self.points):
            prev = self.points[i - 1] if i > 0 else None
            t = p.transition_time(prev, self.exit_time)
            if t is not None and t >= 0:
                transitions.append(t)
        if transitions:
            return round(sum(transitions) / len(transitions), 3)
        return None

    def to_dict(self) -> dict:
        return {
            "version": "1.0",
            "jump_name": self.jump_name,
            "video_path": self.video_path,
            "video_path_cam2": self.video_path_cam2,
            "cam2_offset": self.cam2_offset,
            "draw_string": self.draw_string,
            "working_time_duration": self.working_time_duration,
            "exit_time": self.exit_time,
            "in_point": self.in_point,
            "out_point": self.out_point,
            "points": [p.to_dict() for p in self.points]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JumpSession':
        session = cls(
            jump_name=data.get("jump_name", "Round 1"),
            video_path=data.get("video_path", ""),
            video_path_cam2=data.get("video_path_cam2", ""),
            cam2_offset=data.get("cam2_offset", 0.0),
            draw_string=data.get("draw_string", "A - 12 - 7 - B"),
            working_time_duration=data.get("working_time_duration", 35.0),
            exit_time=data.get("exit_time"),
            in_point=data.get("in_point"),
            out_point=data.get("out_point")
        )
        session.points = [ScoringPoint.from_dict(p) for p in data.get("points", [])]
        return session


# =====================================================================
# Video Cutter Worker (ffmpeg QProcess)
# =====================================================================

class VideoCutterDialog(QDialog):
    """Progress dialog for trimming GoPro video using ffmpeg without audio."""
    cut_completed = pyqtSignal(str)

    def __init__(self, input_path: str, start_sec: float, end_sec: float, output_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✂️ Video schneiden (GoPro Trimmer)")
        self.resize(450, 180)
        self.setModal(True)

        self.input_path = input_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.output_path = output_path
        self.duration = max(0.1, end_sec - start_sec)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.info_label = QLabel(
            f"<b>Eingabe:</b> {os.path.basename(input_path)}<br>"
            f"<b>Schnittbereich:</b> {format_seconds(start_sec)} ➔ {format_seconds(end_sec)} "
            f"(Dauer: {self.duration:.2f}s)<br>"
            f"<b>Ausgabe:</b> {os.path.basename(output_path)}<br>"
            f"<i>Tonspur wird entfernt (Kein Sound benötigt).</i>"
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Starte ffmpeg Prozess...", self)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Abbrechen", self)
        self.btn_cancel.clicked.connect(self._cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.process = QProcess(self)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._on_finished)

    def start_cut(self):
        # ffmpeg with fast CRF re-encoding and -an (no audio)
        cmd_args = [
            "-y",
            "-ss", f"{self.start_sec:.3f}",
            "-to", f"{self.end_sec:.3f}",
            "-i", self.input_path,
            "-c:v", "libx264",
            "-vf", "scale=-2:720",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-an",  # No sound is needed!
            self.output_path
        ]
        self.process.start("ffmpeg", cmd_args)

    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", data)
        if match:
            hours = int(match.group(1))
            mins = int(match.group(2))
            secs = float(match.group(3))
            current = hours * 3600 + mins * 60 + secs
            pct = min(100, int((current / self.duration) * 100))
            self.progress_bar.setValue(pct)
            self.status_label.setText(f"Exportiere Clip... {pct}% ({current:.1f}s / {self.duration:.1f}s)")

    def _on_finished(self, exit_code, exit_status):
        if exit_code == 0 and os.path.exists(self.output_path):
            self.progress_bar.setValue(100)
            self.status_label.setText("Fertiggestellt!")
            self.cut_completed.emit(self.output_path)
            self.accept()
        else:
            err = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
            QMessageBox.critical(self, "Fehler beim Schneiden", f"ffmpeg Fehler (Code {exit_code}):\n{err[-300:]}")
            self.reject()

    def _cancel(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
        self.reject()


# =====================================================================
# Telestration Transparent Glass Pane Overlay Widget
# =====================================================================

class DrawingOverlayWidget(QWidget):
    """Transparentes Overlay zum Zeichnen von Linien, Pfeilen, Freihand & Winkeln über dem Video."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.mode = "NONE"  # "NONE", "LINE", "ARROW", "ANGLE", "FREEHAND"
        self.shapes_history: List[DrawingShape] = []
        self.current_color = QColor(255, 215, 0)  # Gold/Gelb
        self.pen_width = 3

        self.current_points: List[QPointF] = []
        self.current_freehand_stroke: List[QPointF] = []
        self.mouse_pos: Optional[QPointF] = None

    def keyPressEvent(self, event):
        # Leitet Tastatureingaben vom Overlay an das Hauptfenster weiter
        p = self.parent()
        while p and not isinstance(p, QMainWindow):
            p = p.parent()
        if p and hasattr(p, 'handle_global_key'):
            if p.handle_global_key(event, self):
                event.accept()
                return
        super().keyPressEvent(event)

    def set_mode(self, mode: str):
        self.mode = mode
        self.current_points.clear()
        self.current_freehand_stroke.clear()
        self.mouse_pos = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, self.mode == "NONE")
        self.update()

    def set_draw_color(self, color: QColor):
        self.current_color = color

    def clear_drawings(self):
        self.shapes_history.clear()
        self.current_points.clear()
        self.current_freehand_stroke.clear()
        self.mouse_pos = None
        self.update()

    def undo_last(self):
        if self.shapes_history:
            self.shapes_history.pop()
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            # Rechtsklick bricht aktuelle Zeichnung ab
            self.current_points.clear()
            self.current_freehand_stroke.clear()
            self.mouse_pos = None
            self.update()
            return

        if event.button() != Qt.MouseButton.LeftButton or self.mode == "NONE":
            super().mousePressEvent(event)
            return

        pos = event.position()

        if self.mode == "FREEHAND":
            self.current_freehand_stroke = [pos]
            self.update()
            return

        if self.mode in ("LINE", "ARROW"):
            self.current_points.append(pos)
            if len(self.current_points) == 2:
                if self.mode == "LINE":
                    shape = LineShape(p1=self.current_points[0], p2=self.current_points[1],
                                      color=self.current_color, width=self.pen_width)
                else:
                    shape = ArrowShape(p1=self.current_points[0], p2=self.current_points[1],
                                       color=self.current_color, width=self.pen_width)
                self.shapes_history.append(shape)
                self.current_points.clear()
                self.mouse_pos = None

        elif self.mode == "ANGLE":
            self.current_points.append(pos)
            # 3 Punkte: 0 = Scheitelpunkt, 1 = Schenkel A, 2 = Schenkel B
            if len(self.current_points) == 3:
                shape = AngleShape(vertex=self.current_points[0],
                                   p1=self.current_points[1],
                                   p2=self.current_points[2],
                                   color=self.current_color,
                                   width=self.pen_width)
                self.shapes_history.append(shape)
                self.current_points.clear()
                self.mouse_pos = None

        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.mode == "FREEHAND" and (event.buttons() & Qt.MouseButton.LeftButton):
            self.current_freehand_stroke.append(pos)
            self.update()
        elif self.mode != "NONE" and self.current_points:
            self.mouse_pos = pos
            self.update()

    def mouseReleaseEvent(self, event):
        if self.mode == "FREEHAND" and self.current_freehand_stroke:
            if len(self.current_freehand_stroke) >= 2:
                shape = FreehandShape(points=list(self.current_freehand_stroke),
                                      color=self.current_color, width=self.pen_width)
                self.shapes_history.append(shape)
            self.current_freehand_stroke.clear()
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Gespeicherte Formen zeichnen
        for shape in self.shapes_history:
            if isinstance(shape, LineShape):
                pen = QPen(shape.color, shape.width, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawLine(shape.p1, shape.p2)

            elif isinstance(shape, ArrowShape):
                self._draw_arrow(painter, shape.p1, shape.p2, shape.color, shape.width)

            elif isinstance(shape, AngleShape):
                pen = QPen(shape.color, shape.width, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawLine(shape.vertex, shape.p1)
                painter.drawLine(shape.vertex, shape.p2)
                painter.setBrush(QBrush(shape.color))
                painter.drawEllipse(shape.vertex, 4, 4)

                angle_val = shape.calculate_angle()
                text_pos = shape.vertex + QPointF(12, -12)

                # Text Hintergrund-Badge
                painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                text_rect = QRectF(text_pos.x() - 4, text_pos.y() - 14, 55, 20)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(0, 0, 0, 180))
                painter.drawRoundedRect(text_rect, 4, 4)
                painter.setPen(QPen(shape.color))
                painter.drawText(text_pos, f"{angle_val:.1f}°")

            elif isinstance(shape, FreehandShape):
                if len(shape.points) >= 2:
                    pen = QPen(shape.color, shape.width, Qt.PenStyle.SolidLine,
                               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(pen)
                    for i in range(len(shape.points) - 1):
                        painter.drawLine(shape.points[i], shape.points[i + 1])

        # 2. Live-Vorschau bei Benutzerinteraktion
        if self.current_points and self.mouse_pos:
            pen_preview = QPen(QColor(255, 255, 255, 200), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen_preview)

            if self.mode == "LINE":
                painter.drawLine(self.current_points[0], self.mouse_pos)

            elif self.mode == "ARROW":
                self._draw_arrow(painter, self.current_points[0], self.mouse_pos,
                                 QColor(255, 255, 255, 200), 2)

            elif self.mode == "ANGLE":
                if len(self.current_points) == 1:
                    painter.drawLine(self.current_points[0], self.mouse_pos)
                    painter.drawEllipse(self.current_points[0], 5, 5)
                elif len(self.current_points) == 2:
                    painter.drawLine(self.current_points[0], self.current_points[1])
                    painter.drawLine(self.current_points[0], self.mouse_pos)

        # 3. Live-Vorschau Freihand
        if self.current_freehand_stroke and len(self.current_freehand_stroke) >= 2:
            pen = QPen(self.current_color, self.pen_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            for i in range(len(self.current_freehand_stroke) - 1):
                painter.drawLine(self.current_freehand_stroke[i], self.current_freehand_stroke[i + 1])

    def _draw_arrow(self, painter: QPainter, p1: QPointF, p2: QPointF, color: QColor, width: int):
        pen = QPen(color, width, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = math.hypot(dx, dy)
        if length > 8:
            angle = math.atan2(dy, dx)
            arrow_size = 14
            arrow_angle = math.radians(25)
            p_left = QPointF(p2.x() - arrow_size * math.cos(angle - arrow_angle),
                             p2.y() - arrow_size * math.sin(angle - arrow_angle))
            p_right = QPointF(p2.x() - arrow_size * math.cos(angle + arrow_angle),
                              p2.y() - arrow_size * math.sin(angle + arrow_angle))
            painter.setBrush(QBrush(color))
            poly = QPolygonF([p2, p_left, p_right])
            painter.drawPolygon(poly)


# =====================================================================
# MPV Video Player Widget & Container
# =====================================================================

class MPVVideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        try:
            locale.setlocale(locale.LC_NUMERIC, 'C')
        except Exception:
            pass

        self.mpv_instance = mpv.MPV(
            wid=str(int(self.winId())),
            vo="gpu",
            keep_open="yes",
            audio="no",  # Muted by default: No sound is needed!
            input_default_bindings=False,
            input_vo_keyboard=False
        )

    def load_video(self, path: str):
        if self.mpv_instance:
            self.mpv_instance.play(path)
            self.mpv_instance.pause = True

    def set_pause(self, pause: bool):
        if self.mpv_instance:
            try:
                self.mpv_instance.pause = pause
            except Exception:
                pass

    def is_paused(self) -> bool:
        if self.mpv_instance:
            try:
                return bool(self.mpv_instance.pause)
            except Exception:
                pass
        return True

    def seek(self, seconds: float, exact: bool = True):
        if self.mpv_instance:
            try:
                mode = "exact" if exact else "keyframes"
                self.mpv_instance.command("seek", seconds, "absolute", mode)
            except Exception:
                pass

    def set_speed(self, speed: float):
        if self.mpv_instance:
            try:
                self.mpv_instance.speed = speed
            except Exception:
                pass

    def step_frame(self, forward: bool = True):
        if self.mpv_instance:
            cmd = "frame-step" if forward else "frame-back-step"
            try:
                self.mpv_instance.command(cmd)
            except Exception:
                pass

    def get_time(self) -> Optional[float]:
        if self.mpv_instance:
            try:
                return self.mpv_instance.time_pos
            except Exception:
                pass
        return None

    def get_duration(self) -> Optional[float]:
        if self.mpv_instance:
            try:
                return self.mpv_instance.duration
            except Exception:
                pass
        return None

    def get_fps(self) -> float:
        if self.mpv_instance:
            try:
                fps = self.mpv_instance.container_fps or self.mpv_instance.estimated_vf_fps
                if fps and fps > 0:
                    return float(fps)
            except Exception:
                pass
        return 30.0

    def terminate(self):
        if hasattr(self, 'mpv_instance') and self.mpv_instance is not None:
            try:
                self.mpv_instance.terminate()
            except Exception:
                pass
            self.mpv_instance = None

    def closeEvent(self, event):
        self.terminate()
        super().closeEvent(event)


class DrawingMPVContainer(QWidget):
    """Kapselt MPVVideoWidget und transparentes Overlay sauber übereinander."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.mpv_widget = MPVVideoWidget(self)
        self.overlay = DrawingOverlayWidget(self)

    def sync_overlay(self):
        if not self.isVisible():
            self.overlay.hide()
            return
        p = self.mapToGlobal(QPoint(0, 0))
        self.overlay.setGeometry(p.x(), p.y(), self.width(), self.height())
        if not self.overlay.isVisible():
            self.overlay.show()
        self.overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.mpv_widget.setGeometry(0, 0, self.width(), self.height())
        self.sync_overlay()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.sync_overlay()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.overlay.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self.sync_overlay()

    def closeEvent(self, event):
        self.overlay.close()
        self.mpv_widget.terminate()
        super().closeEvent(event)


# =====================================================================
# Custom Interactive Graphical Timeline Widget
# =====================================================================

class ScoringTimelineWidget(QWidget):
    """
    Interaktive grafische Zeitleiste zur Navigation und Darstellung von:
    - Schnittpunkten (Start/End Frame)
    - Working Time Timer (35s, 20s, 60s)
    - Gezählten Punkten (Grün = Approved, Rot = Busted)
    - Formation Finished & Key Given Zeitpunkten
    - Playhead Scrubber
    """
    seek_requested = pyqtSignal(float)
    point_clicked = pyqtSignal(int)  # point index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(92)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.duration: float = 60.0
        self.current_time: float = 0.0
        self.in_point: Optional[float] = None
        self.out_point: Optional[float] = None
        self.exit_time: Optional[float] = None
        self.working_time_duration: float = 35.0
        self.points: List[ScoringPoint] = []
        self.selected_point_index: Optional[int] = None

        self.is_dragging: bool = False
        self.margin_left: int = 20
        self.margin_right: int = 20

    def set_duration(self, dur: float):
        if dur > 0 and dur != self.duration:
            self.duration = dur
            self.update()

    def set_current_time(self, t: float):
        self.current_time = max(0.0, min(self.duration, t))
        self.update()

    def set_in_out(self, in_pt: Optional[float], out_pt: Optional[float]):
        self.in_point = in_pt
        self.out_point = out_pt
        self.update()

    def set_working_time(self, exit_t: Optional[float], wt_duration: float):
        self.exit_time = exit_t
        self.working_time_duration = wt_duration
        self.update()

    def set_points(self, points: List[ScoringPoint], selected_idx: Optional[int] = None):
        self.points = points
        self.selected_point_index = selected_idx
        self.update()

    def _time_to_x(self, t: float) -> float:
        usable_w = max(10, self.width() - self.margin_left - self.margin_right)
        frac = max(0.0, min(1.0, t / self.duration)) if self.duration > 0 else 0.0
        return self.margin_left + frac * usable_w

    def _x_to_time(self, x: float) -> float:
        usable_w = max(10, self.width() - self.margin_left - self.margin_right)
        frac = max(0.0, min(1.0, (x - self.margin_left) / usable_w))
        return frac * self.duration

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Hintergrund
        painter.fillRect(self.rect(), QColor(24, 24, 27))  # Dark zinc

        track_top = 26
        track_height = 42
        usable_w = w - self.margin_left - self.margin_right
        track_rect = QRectF(self.margin_left, track_top, usable_w, track_height)

        # Track Schiene
        painter.setPen(QPen(QColor(63, 63, 70), 1))
        painter.setBrush(QColor(39, 39, 42))
        painter.drawRoundedRect(track_rect, 6, 6)

        # 2. Zeitlineal / Ruler (obere 24px)
        painter.setFont(QFont("Arial", 8))
        step = 5.0 if self.duration <= 45 else (10.0 if self.duration <= 120 else 30.0)
        t = 0.0
        while t <= self.duration:
            x = self._time_to_x(t)
            painter.setPen(QPen(QColor(113, 113, 122), 1))
            painter.drawLine(QPointF(x, 18), QPointF(x, 24))
            label = format_seconds(t, show_decimals=False)
            painter.setPen(QPen(QColor(161, 161, 170)))
            painter.drawText(QRectF(x - 25, 2, 50, 15), Qt.AlignmentFlag.AlignCenter, label)
            t += step

        # 3. Trimming In/Out Schnittbereich
        if self.in_point is not None or self.out_point is not None:
            t_in = self.in_point if self.in_point is not None else 0.0
            t_out = self.out_point if self.out_point is not None else self.duration
            x_in = self._time_to_x(t_in)
            x_out = self._time_to_x(t_out)

            # In/Out Bereich hervorheben
            cut_rect = QRectF(x_in, track_top, max(1, x_out - x_in), track_height)
            painter.fillRect(cut_rect, QColor(14, 165, 233, 45))  # Sky blue transparent

            # Markierungen
            if self.in_point is not None:
                painter.setPen(QPen(QColor(56, 189, 248), 2, Qt.PenStyle.SolidLine))
                painter.drawLine(QPointF(x_in, track_top - 3), QPointF(x_in, track_top + track_height + 3))
                painter.drawText(QRectF(x_in - 25, track_top - 18, 50, 14), Qt.AlignmentFlag.AlignCenter, "[ IN")

            if self.out_point is not None:
                painter.setPen(QPen(QColor(56, 189, 248), 2, Qt.PenStyle.SolidLine))
                painter.drawLine(QPointF(x_out, track_top - 3), QPointF(x_out, track_top + track_height + 3))
                painter.drawText(QRectF(x_out - 25, track_top - 18, 50, 14), Qt.AlignmentFlag.AlignCenter, "] OUT")

        # 4. Working Time Fenster (Exit bis Exit + Working Time)
        if self.exit_time is not None:
            x_exit = self._time_to_x(self.exit_time)
            t_wt_end = self.exit_time + self.working_time_duration
            x_wt_end = self._time_to_x(t_wt_end)

            # Working Time Zone
            wt_rect = QRectF(x_exit, track_top, max(1, x_wt_end - x_exit), track_height)
            painter.fillRect(wt_rect, QColor(34, 197, 94, 50))  # Emerald transparent

            # Exit Line
            painter.setPen(QPen(QColor(74, 222, 128), 2, Qt.PenStyle.SolidLine))
            painter.drawLine(QPointF(x_exit, track_top - 2), QPointF(x_exit, track_top + track_height + 2))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(74, 222, 128)))
            painter.drawText(QRectF(x_exit - 35, track_top + track_height + 4, 70, 14),
                             Qt.AlignmentFlag.AlignCenter, "EXIT (0s)")

            # Working Time Ende Line
            painter.setPen(QPen(QColor(248, 113, 113), 2, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x_wt_end, track_top - 2), QPointF(x_wt_end, track_top + track_height + 2))
            painter.setPen(QPen(QColor(248, 113, 113)))
            painter.drawText(QRectF(x_wt_end - 35, track_top + track_height + 4, 70, 14),
                             Qt.AlignmentFlag.AlignCenter, f"{int(self.working_time_duration)}s WT")

        # 5. Gezählte Punkte & Keys (Approved / Busted Badges)
        for i, pt in enumerate(self.points):
            x_comp = self._time_to_x(pt.time_complete)

            # Falls Key vorhanden, Zeichne Verbindungs-Hold-Balken & Key-Indikator
            if pt.time_key is not None:
                x_key = self._time_to_x(pt.time_key)
                # Hold-Verbindungsbalken
                painter.setPen(QPen(QColor(251, 191, 36, 180), 3))
                painter.drawLine(QPointF(x_comp, track_top + 21), QPointF(x_key, track_top + 21))

                # Key Diamant
                painter.setPen(QPen(QColor(245, 158, 11), 1))
                painter.setBrush(QColor(245, 158, 11))
                kd = 4
                key_poly = QPolygonF([
                    QPointF(x_key, track_top + 21 - kd),
                    QPointF(x_key + kd, track_top + 21),
                    QPointF(x_key, track_top + 21 + kd),
                    QPointF(x_key - kd, track_top + 21)
                ])
                painter.drawPolygon(key_poly)

            # Punkt Badge Pill
            is_approved = (pt.status == "APPROVED")
            bg_color = QColor(22, 163, 74) if is_approved else QColor(220, 38, 38)
            border_color = QColor(255, 255, 255) if (self.selected_point_index == i) else bg_color.lighter(130)

            badge_w = 48
            badge_h = 18
            # Vertikal versetzt, damit aufeinanderfolgende Punkte nicht überlappen
            badge_y = (track_top + 4) if (i % 2 == 0) else (track_top + 22)
            badge_rect = QRectF(x_comp - badge_w / 2, badge_y, badge_w, badge_h)

            painter.setPen(QPen(border_color, 1.5 if (self.selected_point_index == i) else 1.0))
            painter.setBrush(QBrush(bg_color))
            painter.drawRoundedRect(badge_rect, 4, 4)

            # Symbol & Formationsname
            icon = "✓" if is_approved else "✗"
            text = f"{icon} {pt.point_num}:{pt.formation}"
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)

        # 6. Playhead Scrubber Cursor
        x_play = self._time_to_x(self.current_time)
        painter.setPen(QPen(QColor(250, 204, 21), 2))  # Gelber Cursor
        painter.drawLine(QPointF(x_play, 18), QPointF(x_play, track_top + track_height + 6))

        # Playhead Handle oben
        handle_poly = QPolygonF([
            QPointF(x_play - 6, 12),
            QPointF(x_play + 6, 12),
            QPointF(x_play + 6, 18),
            QPointF(x_play, 24),
            QPointF(x_play - 6, 18)
        ])
        painter.setBrush(QColor(250, 204, 21))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(handle_poly)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            # Prüfen ob ein Punkt angeklickt wurde
            clicked_idx = self._find_point_at_x(x)
            if clicked_idx is not None:
                self.selected_point_index = clicked_idx
                self.point_clicked.emit(clicked_idx)
                # Direkt zum Zeitpunkt springen
                pt = self.points[clicked_idx]
                self.seek_requested.emit(pt.time_complete)
            else:
                target_t = self._x_to_time(x)
                self.is_dragging = True
                self.seek_requested.emit(target_t)
            self.update()

    def mouseMoveEvent(self, event):
        x = event.position().x()
        if self.is_dragging:
            target_t = self._x_to_time(x)
            self.seek_requested.emit(target_t)
        else:
            # Tooltip für Punkte in der Nähe
            hover_idx = self._find_point_at_x(x)
            if hover_idx is not None:
                p = self.points[hover_idx]
                hold = p.hold_time()
                hold_str = f"{hold:.2f}s" if hold is not None else "Kein Key"
                prev = self.points[hover_idx - 1] if hover_idx > 0 else None
                trans = p.transition_time(prev, self.exit_time)
                trans_str = f"{trans:.2f}s" if trans is not None else "-"
                wt_str = ""
                if self.exit_time is not None:
                    wt_offset = p.time_complete - self.exit_time
                    wt_str = f" | WT: +{wt_offset:.2f}s"
                    if not p.is_in_working_time(self.exit_time, self.working_time_duration):
                        wt_str += " (Out of WT)"
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"Punkt #{p.point_num} ({p.formation})\n"
                    f"Status: {p.status}\n"
                    f"Zeit: {format_seconds(p.time_complete)}{wt_str}\n"
                    f"Hold: {hold_str} | Transition: {trans_str}\n"
                    f"Notizen: {p.notes or 'Keine'}",
                    self
                )
            else:
                t = self._x_to_time(x)
                QToolTip.showText(event.globalPosition().toPoint(), f"Zeit: {format_seconds(t)}", self)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def _find_point_at_x(self, x: float) -> Optional[int]:
        for i, pt in enumerate(self.points):
            px = self._time_to_x(pt.time_complete)
            if abs(x - px) <= 24:
                return i
        return None


# =====================================================================
# Dive Pool Helper Dialog
# =====================================================================

class DivePoolDialog(QDialog):
    """Auswahldialog für FAI 4-Way Randoms (A-Q) und Blocks (1-22)."""
    formation_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FAI 4-Way Dive Pool Auswahl")
        self.resize(700, 520)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Klicke auf eine Formation, um sie dem Sprung hinzuzufügen:</b>"))

        # Randoms Group
        gb_randoms = QGroupBox("Randoms (1 Punkt)")
        grid_r = QHBoxLayout(gb_randoms)
        sub_layout_r = QVBoxLayout()

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for idx, (code, name) in enumerate(FAI_RANDOMS.items()):
            btn = QPushButton(f"<b>{code}</b><br><small>{name}</small>")
            btn.setFixedHeight(46)
            btn.clicked.connect(lambda checked, c=code: self._select(c))
            if idx < 8:
                row1.addWidget(btn)
            else:
                row2.addWidget(btn)

        sub_layout_r.addLayout(row1)
        sub_layout_r.addLayout(row2)
        grid_r.addLayout(sub_layout_r)
        layout.addWidget(gb_randoms)

        # Blocks Group
        gb_blocks = QGroupBox("Blöcke 1-22 (2 Punkte)")
        grid_b = QVBoxLayout(gb_blocks)

        block_keys = list(FAI_BLOCKS.keys())
        for row_idx in range(4):
            h_row = QHBoxLayout()
            for col_idx in range(6):
                idx = row_idx * 6 + col_idx
                if idx < len(block_keys):
                    b_code = block_keys[idx]
                    b_name = FAI_BLOCKS[b_code]
                    btn = QPushButton(f"<b>{b_code}</b><br><small>{b_name.split(' - ')[0]}</small>")
                    btn.setFixedHeight(46)
                    btn.clicked.connect(lambda checked, c=b_code: self._select(c))
                    h_row.addWidget(btn)
                else:
                    h_row.addStretch()
            grid_b.addLayout(h_row)

        layout.addWidget(gb_blocks)

        bottom_row = QHBoxLayout()
        btn_open_3d = QPushButton("🎯 In 3D Formation Explorer öffnen...")
        btn_open_3d.setStyleSheet("background: #2563eb; color: #ffffff; font-weight: bold; padding: 6px 14px;")
        btn_open_3d.clicked.connect(self._open_3d_explorer)
        bottom_row.addWidget(btn_open_3d)
        bottom_row.addStretch()

        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(btn_close)
        layout.addLayout(bottom_row)

    def _select(self, code: str):
        self.formation_selected.emit(code)

    def _open_3d_explorer(self):
        try:
            import formation_tool
            self._explorer_win = formation_tool.FormationExplorerWindow("21")
            self._explorer_win.show()
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"3D Explorer konnte nicht geöffnet werden: {e}")


# =====================================================================
# Video-Pfade, Standard-Ordner & Quick Links Dialog
# =====================================================================

def find_connected_camera_folders() -> List[str]:
    """Sucht nach typischen Mount-Pfaden für angeschlossene Kameras/SD-Karten (GoPro etc.)"""
    found = []
    user = os.environ.get("USER", "")
    scan_bases = [
        f"/media/{user}",
        f"/run/media/{user}",
        "/media",
        "/mnt",
    ]
    subpaths = ["DCIM/100GOPRO", "DCIM", ""]
    for base in scan_bases:
        if os.path.isdir(base):
            try:
                for entry in os.listdir(base):
                    full_entry = os.path.join(base, entry)
                    if os.path.isdir(full_entry):
                        for sp in subpaths:
                            candidate = os.path.join(full_entry, sp) if sp else full_entry
                            if os.path.isdir(candidate) and candidate not in found:
                                try:
                                    files = os.listdir(candidate)[:20]
                                    if "DCIM" in candidate or any("GOPR" in f.upper() or f.upper().endswith(".MP4") for f in files):
                                        found.append(candidate)
                                except Exception:
                                    pass
            except Exception:
                pass
    return found


class VideoPathsDialog(QDialog):
    """Dialog zur Konfiguration des Standard-Video-Ordners und Quick-Links / Favoriten."""
    def __init__(self, main_window: 'DebriefMainWindow'):
        super().__init__(main_window)
        self.mw = main_window
        self.setWindowTitle("⚙️ Video-Ordner & Quick Links konfigurieren")
        self.resize(640, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Standard-Ordner
        grp_def = QGroupBox("Standard-Ordner (Default Video Directory)")
        l_def = QVBoxLayout(grp_def)
        lbl_def = QLabel("Dieser Ordner wird standardmäßig geöffnet, wenn Sie auf 'Video laden' klicken:")
        lbl_def.setStyleSheet("color: #888888; font-size: 11px;")
        l_def.addWidget(lbl_def)

        row_def = QHBoxLayout()
        self.txt_default = QLineEdit(self.mw.get_default_video_dir())
        self.txt_default.setReadOnly(True)
        btn_browse_def = QPushButton("📂 Auswählen...")
        btn_browse_def.clicked.connect(self._browse_default_dir)
        btn_reset_def = QPushButton("↺ Standard (~/Videos)")
        btn_reset_def.setToolTip("Auf Standard ~/Videos zurücksetzen")
        btn_reset_def.clicked.connect(self._reset_default_dir)
        row_def.addWidget(self.txt_default, 1)
        row_def.addWidget(btn_browse_def)
        row_def.addWidget(btn_reset_def)
        l_def.addLayout(row_def)
        layout.addWidget(grp_def)

        # 2. Quick Links / Favoriten
        grp_ql = QGroupBox("Quick Links / Favoriten-Ordner")
        l_ql = QVBoxLayout(grp_ql)
        lbl_ql = QLabel(
            "Diese Ordner erscheinen direkt in der Seitenleiste des Dateidialogs und im Menü '⚡ Quick Links':"
        )
        lbl_ql.setStyleSheet("color: #888888; font-size: 11px;")
        l_ql.addWidget(lbl_ql)

        self.list_links = QListWidget()
        for path in self.mw.get_quick_link_dirs():
            self._add_list_item(path)
        l_ql.addWidget(self.list_links)

        row_ql_btns = QHBoxLayout()
        btn_add = QPushButton("➕ Ordner hinzufügen...")
        btn_add.clicked.connect(self._add_quick_link)
        btn_remove = QPushButton("➖ Entfernen")
        btn_remove.clicked.connect(self._remove_quick_link)
        btn_scan = QPushButton("🔍 GoPro / SD-Karte suchen")
        btn_scan.setStyleSheet("background-color: #0284c7; color: white;")
        btn_scan.setToolTip("Automatisch nach eingesteckten SD-Karten oder GoPro DCIM-Ordnern suchen")
        btn_scan.clicked.connect(self._scan_cameras)

        row_ql_btns.addWidget(btn_add)
        row_ql_btns.addWidget(btn_remove)
        row_ql_btns.addWidget(btn_scan)
        row_ql_btns.addStretch()
        l_ql.addLayout(row_ql_btns)
        layout.addWidget(grp_ql, 1)

        # Bottom Buttons
        row_actions = QHBoxLayout()
        row_actions.addStretch()
        btn_save = QPushButton("💾 Speichern")
        btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 14px;")
        btn_save.clicked.connect(self._save_and_close)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        row_actions.addWidget(btn_save)
        row_actions.addWidget(btn_cancel)
        layout.addLayout(row_actions)

    def _add_list_item(self, path: str):
        if not path or not os.path.isdir(path):
            return
        for i in range(self.list_links.count()):
            if self.list_links.item(i).text() == path:
                return
        item = QListWidgetItem(path)
        item.setToolTip(path)
        self.list_links.addItem(item)

    def _browse_default_dir(self):
        curr = self.txt_default.text() or os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(self, "Standard Video-Ordner wählen", curr)
        if chosen:
            self.txt_default.setText(chosen)

    def _reset_default_dir(self):
        vid_dir = os.path.expanduser("~/Videos")
        if not os.path.isdir(vid_dir):
            vid_dir = os.path.expanduser("~")
        self.txt_default.setText(vid_dir)

    def _add_quick_link(self):
        curr = self.txt_default.text() or os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(self, "Quick Link Ordner hinzufügen", curr)
        if chosen:
            self._add_list_item(chosen)

    def _remove_quick_link(self):
        row = self.list_links.currentRow()
        if row >= 0:
            self.list_links.takeItem(row)

    def _scan_cameras(self):
        found = find_connected_camera_folders()
        if not found:
            QMessageBox.information(
                self, "Kamera-Suche",
                "Keine eingesteckten GoPro / SD-Karten unter /media oder /run/media gefunden.\n\n"
                "Stellen Sie sicher, dass die SD-Karte oder Kamera gemountet ist."
            )
            return
        added = 0
        for f in found:
            exists = any(self.list_links.item(i).text() == f for i in range(self.list_links.count()))
            if not exists:
                self._add_list_item(f)
                added += 1
        if added > 0:
            QMessageBox.information(self, "Kamera gefunden", f"{added} Kamera-/SD-Karten-Ordner zu Quick Links hinzugefügt!")
        else:
            QMessageBox.information(self, "Kamera gefunden", "Gefundene Kamera-Ordner sind bereits in der Quick Links Liste.")

    def _save_and_close(self):
        def_dir = self.txt_default.text().strip()
        if def_dir and os.path.isdir(def_dir):
            self.mw.set_default_video_dir(def_dir)

        links = []
        for i in range(self.list_links.count()):
            links.append(self.list_links.item(i).text())
        self.mw.set_quick_link_dirs(links)

        self.accept()


# =====================================================================
# Programmglobaler Shortcut EventFilter
# =====================================================================

class GlobalShortcutFilter(QObject):
    """
    Anwendungsweiter EventFilter, um Tastaturkürzel programmweit zuverlässig abzufangen,
    unabhängig davon, welches Child-Widget (Buttons, Tabellen, Player, Overlays)
    den Tastaturfokus besitzt.
    """
    def __init__(self, main_window: 'DebriefMainWindow'):
        super().__init__(main_window)
        self.mw = main_window

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            # 1. Modale Dialoge (z.B. Dateidialoge, MessageBox, DivePool, Trimmer) nicht stören
            if QApplication.activeModalWidget() is not None:
                return False

            # 2. Aktive Popups (z.B. QComboBox-Dropdowns, Kontextmenüs) nicht stören
            if QApplication.activePopupWidget() is not None:
                return False

            # 3. Prüfen, ob das Event zu diesem Fenster oder dessen Overlays/Kindern gehört
            if not self._is_event_for_window(watched):
                return False

            # 4. Delegation an zentralen Shortcut-Handler
            if self.mw.handle_global_key(event, watched):
                return True

        return super().eventFilter(watched, event)

    def _is_event_for_window(self, watched: QObject) -> bool:
        if watched is None or watched == self.mw:
            return True
        if isinstance(watched, QWidget):
            if watched.window() == self.mw:
                return True
            if hasattr(self.mw, 'container1'):
                if watched == self.mw.container1.overlay or watched == self.mw.container1.mpv_widget:
                    return True
            if hasattr(self.mw, 'container2'):
                if watched == self.mw.container2.overlay or watched == self.mw.container2.mpv_widget:
                    return True
            if self.mw.isActiveWindow():
                return True
        return False


# =====================================================================
# Main Application Window
# =====================================================================

class DebriefMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FAI 4-Way Formation Skydiving Debriefing & Scoring System")
        self.resize(1600, 920)

        self.session = JumpSession()
        self.fps = 30.0
        self.settings = QSettings("4WayScoring", "DebriefApp")

        # Status für temporäre Event-Erfassung
        self.pending_complete_time: Optional[float] = None
        self.pending_key_time: Optional[float] = None
        self.selected_point_index: Optional[int] = None

        self._init_ui()
        self._init_timer()
        self._apply_dark_theme()

        # Globalen Shortcut-Filter anwendungsweit registrieren
        self.shortcut_filter = GlobalShortcutFilter(self)
        app = QApplication.instance()
        if app:
            app.installEventFilter(self.shortcut_filter)

    def _init_ui(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(6)

        # -------------------------------------------------------------
        # 1. TOP HEADER: Jump Name, Draw Sequence & Session Management
        # -------------------------------------------------------------
        header_bar = QFrame(self)
        header_bar.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(10)

        header_layout.addWidget(QLabel("<b>Sprung / Runde:</b>"))
        self.edit_jump_name = QLineEdit(self.session.jump_name, self)
        self.edit_jump_name.setFixedWidth(130)
        self.edit_jump_name.textChanged.connect(self._on_jump_name_changed)
        header_layout.addWidget(self.edit_jump_name)

        header_layout.addWidget(QLabel("<b>Draw / Formationen:</b>"))
        self.edit_draw = QLineEdit(self.session.draw_string, self)
        self.edit_draw.setPlaceholderText("z.B. A - 12 - 7 - B oder C E 14")
        self.edit_draw.textChanged.connect(self._on_draw_changed)
        header_layout.addWidget(self.edit_draw)

        self.btn_apply_draw_to_points = QPushButton("🔄 Draw anwenden")
        self.btn_apply_draw_to_points.setToolTip("Formationen der bereits gewerteten Punkte an die neue Draw-Reihenfolge anpassen")
        self.btn_apply_draw_to_points.clicked.connect(self._apply_draw_to_existing_points)
        header_layout.addWidget(self.btn_apply_draw_to_points)

        btn_dive_pool = QPushButton("📋 Dive Pool...")
        btn_dive_pool.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_dive_pool.clicked.connect(self._open_dive_pool_helper)
        header_layout.addWidget(btn_dive_pool)

        btn_draw_gen = QPushButton("🎲 Draw Generator & Training...")
        btn_draw_gen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_draw_gen.setStyleSheet("background: #065f46; color: #34d399; font-weight: bold;")
        btn_draw_gen.setToolTip("Runden-Draws nach FAI AAA generieren, Trainings-Datenbank & Rhythm XP Bilder")
        btn_draw_gen.clicked.connect(self._open_draw_generator_dialog)
        header_layout.addWidget(btn_draw_gen)

        btn_3d_explorer = QPushButton("🎯 3D Formationen...")
        btn_3d_explorer.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_3d_explorer.setStyleSheet("background: #1e3a8a; color: #38bdf8; font-weight: bold;")
        btn_3d_explorer.setToolTip("Öffnet den interaktiven 3D Formation Explorer mit Head Switches & Key-Details")
        btn_3d_explorer.clicked.connect(self._open_3d_explorer_for_current)
        header_layout.addWidget(btn_3d_explorer)

        btn_shortcuts = QPushButton("❓ Hilfe & Shortcuts [F1]")
        btn_shortcuts.setToolTip("Ausführliche Anleitung zu Wertung, Zeiten, FAI-Blöcken & Tastaturkürzeln (Taste 'F1')")
        btn_shortcuts.clicked.connect(self._show_shortcuts_help)
        header_layout.addWidget(btn_shortcuts)

        header_layout.addSpacing(15)

        btn_save_session = QPushButton("💾 Speichern")
        btn_save_session.setToolTip("Session in JSON-Datei speichern (Strg+S)")
        btn_save_session.clicked.connect(self._save_session_file)
        header_layout.addWidget(btn_save_session)

        btn_load_session = QPushButton("📂 Laden")
        btn_load_session.setToolTip("Gespeicherte Session laden (Strg+O)")
        btn_load_session.clicked.connect(self._load_session_file)
        header_layout.addWidget(btn_load_session)

        btn_export_report = QPushButton("📊 Report Export...")
        btn_export_report.setToolTip("Debriefing Report exportieren (Strg+E)")
        btn_export_report.clicked.connect(self._export_debrief_report)
        header_layout.addWidget(btn_export_report)

        btn_settings = QPushButton("⚙️ Pfade & Ordner...")
        btn_settings.setToolTip("Standard-Video-Ordner und Quick-Links / Favoriten konfigurieren")
        btn_settings.clicked.connect(self._open_video_paths_dialog)
        header_layout.addWidget(btn_settings)

        self.btn_fullscreen = QPushButton("🗗 Fenster [F11]")
        self.btn_fullscreen.setToolTip("Vollbildmodus umschalten (Taste F11)")
        self.btn_fullscreen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        header_layout.addWidget(self.btn_fullscreen)

        main_layout.addWidget(header_bar)

        # Sequence Chips Display Bar
        self.chips_bar = QFrame(self)
        self.chips_layout = QHBoxLayout(self.chips_bar)
        self.chips_layout.setContentsMargins(8, 2, 8, 2)
        self.chips_layout.setSpacing(6)
        self._update_sequence_chips()
        main_layout.addWidget(self.chips_bar)

        # -------------------------------------------------------------
        # 2. MAIN SPLITTER: Left (Video & Timeline) vs Right (Scoring & Stats)
        # -------------------------------------------------------------
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.splitterMoved.connect(lambda *args: self.sync_overlays())
        main_layout.addWidget(self.splitter, stretch=1)

        # =============================================================
        # LEFT PANEL: Video Player, Trimming, Overlay & Timeline
        # =============================================================
        left_container = QWidget(self.splitter)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # A. Trimming & Video Loading Toolbar
        trim_toolbar = QFrame(left_container)
        trim_toolbar.setObjectName("SubToolbar")
        trim_layout = QHBoxLayout(trim_toolbar)
        trim_layout.setContentsMargins(8, 4, 8, 4)
        trim_layout.setSpacing(8)

        self.btn_load_raw = QPushButton("📹 Video 1 laden...")
        self.btn_load_raw.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")
        self.btn_load_raw.setToolTip("Hauptkamera / GoPro Video 1 laden")
        self.btn_load_raw.clicked.connect(self._open_raw_video)
        trim_layout.addWidget(self.btn_load_raw)

        self.btn_quick_links = QPushButton("⚡ Quick Links ▾")
        self.btn_quick_links.setStyleSheet("background-color: #0369a1; color: white; font-size: 11px;")
        self.btn_quick_links.setToolTip("Schnellzugriff auf Favoriten-Ordner & zuletzt geöffnete Videos")
        self.btn_quick_links.clicked.connect(self._show_quick_links_menu)
        trim_layout.addWidget(self.btn_quick_links)

        trim_layout.addSpacing(10)
        trim_layout.addWidget(QLabel("<b>Trimmer:</b>"))

        btn_set_in = QPushButton("[ Start Frame (In)")
        btn_set_in.setToolTip("Startpunkt für Schnitt setzen (Taste '[' oder 'I')")
        btn_set_in.clicked.connect(self._mark_in_point)
        trim_layout.addWidget(btn_set_in)

        self.lbl_in_point = QLabel("In: --:--")
        trim_layout.addWidget(self.lbl_in_point)

        btn_set_out = QPushButton("] End Frame (Out)")
        btn_set_out.setToolTip("Endpunkt für Schnitt setzen (Taste ']' oder 'O')")
        btn_set_out.clicked.connect(self._mark_out_point)
        trim_layout.addWidget(btn_set_out)

        self.lbl_out_point = QLabel("Out: --:--")
        trim_layout.addWidget(self.lbl_out_point)

        self.lbl_cut_duration = QLabel("(Dauer: --:--)")
        trim_layout.addWidget(self.lbl_cut_duration)

        btn_cut_video = QPushButton("✂️ Video schneiden (Kein Ton)")
        btn_cut_video.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")
        btn_cut_video.setToolTip("Schneidet das Video mit Start & End Frame ohne Tonspur und lädt es direkt!")
        btn_cut_video.clicked.connect(self._cut_video_ffmpeg)
        trim_layout.addWidget(btn_cut_video)

        trim_layout.addStretch()

        self.btn_toggle_dual = QPushButton("👥 Dual Cam Ansicht")
        self.btn_toggle_dual.setCheckable(True)
        self.btn_toggle_dual.setToolTip("Schaltet zwischen Einzel- und Doppel-Kamera (Dual Cam) Ansicht um")
        self.btn_toggle_dual.toggled.connect(self._toggle_dual_cam)
        trim_layout.addWidget(self.btn_toggle_dual)

        self.btn_load_cam2 = QPushButton("📹 Cam 2 laden...")
        self.btn_load_cam2.setStyleSheet("background-color: #7c3aed; color: white; font-weight: bold;")
        self.btn_load_cam2.setToolTip("Zweites Video für Dual Cam Perspektive laden")
        self.btn_load_cam2.clicked.connect(self._open_cam2_video)
        self.btn_load_cam2.hide()
        trim_layout.addWidget(self.btn_load_cam2)

        left_layout.addWidget(trim_toolbar)

        # B. Video Display Area (Single Cam primary, Dual Cam optional)
        self.video_container_layout = QHBoxLayout()
        self.video_container_layout.setContentsMargins(0, 0, 0, 0)
        self.video_container_layout.setSpacing(6)

        # Cam 1 Box (Hauptkamera)
        self.cam1_box = QWidget(left_container)
        cam1_layout = QVBoxLayout(self.cam1_box)
        cam1_layout.setContentsMargins(0, 0, 0, 0)
        cam1_layout.setSpacing(2)
        self.lbl_cam1_title = QLabel("📹 <b>Cam 1 (Hauptkamera)</b>")
        self.lbl_cam1_title.setStyleSheet("color: #38bdf8; font-size: 11px; padding: 2px 4px; background: #27272a; border-radius: 3px;")
        self.lbl_cam1_title.hide()
        cam1_layout.addWidget(self.lbl_cam1_title)
        self.container1 = DrawingMPVContainer(self.cam1_box)
        cam1_layout.addWidget(self.container1, stretch=1)

        # Cam 2 Box (Zweitkamera)
        self.cam2_box = QWidget(left_container)
        cam2_layout = QVBoxLayout(self.cam2_box)
        cam2_layout.setContentsMargins(0, 0, 0, 0)
        cam2_layout.setSpacing(2)
        cam2_header = QHBoxLayout()
        self.lbl_cam2_title = QLabel("📹 <b>Cam 2 (Zweitkamera)</b>")
        self.lbl_cam2_title.setStyleSheet("color: #c084fc; font-size: 11px; padding: 2px 4px; background: #27272a; border-radius: 3px;")
        cam2_header.addWidget(self.lbl_cam2_title)
        cam2_header.addStretch()
        btn_quick_cam2 = QPushButton("📂 Video 2 wählen...")
        btn_quick_cam2.setFixedHeight(22)
        btn_quick_cam2.setStyleSheet("background-color: #7c3aed; color: white; font-size: 11px; padding: 2px 8px; font-weight: bold;")
        btn_quick_cam2.clicked.connect(self._open_cam2_video)
        cam2_header.addWidget(btn_quick_cam2)
        cam2_layout.addLayout(cam2_header)

        self.container2 = DrawingMPVContainer(self.cam2_box)
        cam2_layout.addWidget(self.container2, stretch=1)
        self.cam2_box.hide()

        self.video_container_layout.addWidget(self.cam1_box, stretch=1)
        self.video_container_layout.addWidget(self.cam2_box, stretch=1)
        left_layout.addLayout(self.video_container_layout, stretch=1)

        # C. Telestration & Playback Control Bar
        player_control_bar = QFrame(left_container)
        player_control_bar.setObjectName("SubToolbar")
        player_control_layout = QHBoxLayout(player_control_bar)
        player_control_layout.setContentsMargins(8, 4, 8, 4)
        player_control_layout.setSpacing(8)

        # Overlay Werkzeuge
        player_control_layout.addWidget(QLabel("<b>Overlay:</b>"))
        self.btn_tool_none = QRadioButton("Cursor")
        self.btn_tool_none.setChecked(True)
        self.btn_tool_none.setToolTip("Standard Mauszeiger (Taste 'Esc')")
        self.btn_tool_none.toggled.connect(lambda ch: ch and self._set_draw_mode("NONE"))

        self.btn_tool_line = QRadioButton("Linie")
        self.btn_tool_line.toggled.connect(lambda ch: ch and self._set_draw_mode("LINE"))

        self.btn_tool_arrow = QRadioButton("Pfeil")
        self.btn_tool_arrow.toggled.connect(lambda ch: ch and self._set_draw_mode("ARROW"))

        self.btn_tool_angle = QRadioButton("Winkel (°)")
        self.btn_tool_angle.toggled.connect(lambda ch: ch and self._set_draw_mode("ANGLE"))

        self.btn_tool_freehand = QRadioButton("Freihand")
        self.btn_tool_freehand.toggled.connect(lambda ch: ch and self._set_draw_mode("FREEHAND"))

        self.tool_group = QButtonGroup(self)
        self.tool_group.addButton(self.btn_tool_none)
        self.tool_group.addButton(self.btn_tool_line)
        self.tool_group.addButton(self.btn_tool_arrow)
        self.tool_group.addButton(self.btn_tool_angle)
        self.tool_group.addButton(self.btn_tool_freehand)

        player_control_layout.addWidget(self.btn_tool_none)
        player_control_layout.addWidget(self.btn_tool_line)
        player_control_layout.addWidget(self.btn_tool_arrow)
        player_control_layout.addWidget(self.btn_tool_angle)
        player_control_layout.addWidget(self.btn_tool_freehand)

        btn_undo_draw = QPushButton("↩ Undo")
        btn_undo_draw.setToolTip("Letzte Telestration-Zeichnung rückgängig machen (Strg+Z)")
        btn_undo_draw.clicked.connect(self._undo_drawing)
        btn_clear_drawings = QPushButton("🗑️ Löschen")
        btn_clear_drawings.setToolTip("Alle Zeichnungen vom Overlay löschen")
        btn_clear_drawings.clicked.connect(self._clear_drawings)
        player_control_layout.addWidget(btn_undo_draw)
        player_control_layout.addWidget(btn_clear_drawings)

        player_control_layout.addSpacing(15)

        # Playback Controls
        self.btn_play_pause = QPushButton("▶ Play")
        self.btn_play_pause.setFixedWidth(85)
        self.btn_play_pause.setStyleSheet("font-weight: bold;")
        self.btn_play_pause.setToolTip("Video abspielen / pausieren (Leertaste)")
        self.btn_play_pause.clicked.connect(self._toggle_play_pause)
        player_control_layout.addWidget(self.btn_play_pause)

        btn_step_back = QPushButton("◀ Bild")
        btn_step_back.setToolTip("1 Einzelbild zurück (Pfeiltaste Links, Shift+Links für 1s)")
        btn_step_back.clicked.connect(lambda: self._step_frame(False))
        player_control_layout.addWidget(btn_step_back)

        btn_step_fwd = QPushButton("Bild ▶")
        btn_step_fwd.setToolTip("1 Einzelbild vor (Pfeiltaste Rechts, Shift+Rechts für 1s)")
        btn_step_fwd.clicked.connect(lambda: self._step_frame(True))
        player_control_layout.addWidget(btn_step_fwd)

        # Geschwindigkeits-Auswahl
        player_control_layout.addWidget(QLabel("Speed:"))
        self.combo_speed = QComboBox(self)
        self.combo_speed.addItems(["0.1x", "0.25x", "0.5x", "0.75x", "1.0x", "1.5x", "2.0x"])
        self.combo_speed.setCurrentText("1.0x")
        self.combo_speed.currentTextChanged.connect(self._on_speed_changed)
        player_control_layout.addWidget(self.combo_speed)

        self.lbl_timecode = QLabel("00:00.00 / 00:00.00 (Fr 0)")
        self.lbl_timecode.setStyleSheet("font-family: monospace; font-size: 13px; font-weight: bold; color: #38bdf8;")
        player_control_layout.addWidget(self.lbl_timecode)

        left_layout.addWidget(player_control_bar)

        # D. Custom Interactive Timeline
        self.timeline_widget = ScoringTimelineWidget(left_container)
        self.timeline_widget.seek_requested.connect(self._seek_to_time)
        self.timeline_widget.point_clicked.connect(self._on_timeline_point_clicked)
        left_layout.addWidget(self.timeline_widget)

        self.splitter.addWidget(left_container)

        # =============================================================
        # RIGHT PANEL: Scoring, Working Time Timer & Debrief Statistics
        # =============================================================
        right_container = QWidget(self.splitter)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 0, 4, 0)
        right_layout.setSpacing(8)

        # Card 1: Working Time & Exit Timer
        card_timer = QFrame(right_container)
        card_timer.setObjectName("DebriefCard")
        timer_layout = QVBoxLayout(card_timer)
        timer_layout.setContentsMargins(10, 10, 10, 10)
        timer_layout.setSpacing(8)

        timer_top = QHBoxLayout()
        timer_top.addWidget(QLabel("<b>⏱️ Working Time (Arbeitszeit):</b>"))
        timer_top.addStretch()

        self.combo_wt_preset = QComboBox(self)
        self.combo_wt_preset.addItems(["35s (Competition)", "20s (Rookie/Speed)", "60s (Training)", "Custom..."])
        self.combo_wt_preset.currentTextChanged.connect(self._on_wt_preset_changed)
        timer_top.addWidget(self.combo_wt_preset)
        timer_layout.addLayout(timer_top)

        # Timer Start Button & Status LCD
        timer_action_layout = QHBoxLayout()
        self.btn_start_timer = QPushButton("⏱️ Start Timer / Exit [T]")
        self.btn_start_timer.setStyleSheet("background-color: #eab308; color: black; font-weight: bold; font-size: 14px; padding: 6px;")
        self.btn_start_timer.setToolTip("Setzt den Exit-Zeitpunkt auf die aktuelle Videoposition (Taste 'T')")
        self.btn_start_timer.clicked.connect(self._set_exit_timer_now)
        timer_action_layout.addWidget(self.btn_start_timer, stretch=1)

        self.btn_clear_timer = QPushButton("Reset")
        self.btn_clear_timer.clicked.connect(self._reset_exit_timer)
        timer_action_layout.addWidget(self.btn_clear_timer)
        timer_layout.addLayout(timer_action_layout)

        # Live Timer Banner
        self.timer_banner = QFrame(self)
        self.timer_banner.setObjectName("TimerBanner")
        banner_layout = QVBoxLayout(self.timer_banner)
        banner_layout.setContentsMargins(8, 6, 8, 6)

        self.lbl_timer_status = QLabel("Timer nicht gestartet (Kein Exit gesetzt)")
        self.lbl_timer_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #facc15;")
        self.lbl_timer_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(self.lbl_timer_status)

        self.timer_progress = QProgressBar(self)
        self.timer_progress.setRange(0, 1000)
        self.timer_progress.setValue(0)
        self.timer_progress.setTextVisible(False)
        self.timer_progress.setFixedHeight(6)
        banner_layout.addWidget(self.timer_progress)

        timer_layout.addWidget(self.timer_banner)
        right_layout.addWidget(card_timer)

        # Card 2: Scoring Action Panel (Formation Complete, Key, Approve, Bust)
        card_scoring = QFrame(right_container)
        card_scoring.setObjectName("DebriefCard")
        scoring_layout = QVBoxLayout(card_scoring)
        scoring_layout.setContentsMargins(10, 10, 10, 10)
        scoring_layout.setSpacing(8)

        # Formation Indikator
        self.lbl_next_formation = QLabel("Nächste Formation: <b>A</b> (Punkt #1)")
        self.lbl_next_formation.setStyleSheet("font-size: 14px; color: #38bdf8;")
        scoring_layout.addWidget(self.lbl_next_formation)

        # Row 1: Formation Finish & Key Events
        events_btn_layout = QHBoxLayout()
        self.btn_mark_complete = QPushButton("🏁 Formation Fertig [F]")
        self.btn_mark_complete.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 6px;")
        self.btn_mark_complete.setToolTip("Markiert den Zeitpunkt, an dem die Griffe fertig geschlossen wurden (Taste 'F')")
        self.btn_mark_complete.clicked.connect(self._mark_formation_complete)
        events_btn_layout.addWidget(self.btn_mark_complete)

        self.btn_mark_key = QPushButton("🔑 Key Gegeben [K]")
        self.btn_mark_key.setStyleSheet("background-color: #f59e0b; color: black; font-weight: bold; padding: 6px;")
        self.btn_mark_key.setToolTip("Markiert den Zeitpunkt des Schlüssels/Bruchs (Taste 'K')")
        self.btn_mark_key.clicked.connect(self._mark_key_given)
        events_btn_layout.addWidget(self.btn_mark_key)
        scoring_layout.addLayout(events_btn_layout)

        self.lbl_pending_event = QLabel("Bereit für Wertung")
        self.lbl_pending_event.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        scoring_layout.addWidget(self.lbl_pending_event)

        # Row 2: Judging Decision (Score vs Bust)
        judging_btn_layout = QHBoxLayout()
        self.btn_score_point = QPushButton("✅ Punkt Zählen (+1) [S]")
        self.btn_score_point.setStyleSheet("background-color: #16a34a; color: white; font-size: 14px; font-weight: bold; padding: 8px;")
        self.btn_score_point.setToolTip("Formation anerkannt / gewertet (Taste 'S')")
        self.btn_score_point.clicked.connect(lambda: self._judge_point("APPROVED"))
        judging_btn_layout.addWidget(self.btn_score_point)

        self.btn_bust_point = QPushButton("❌ Bust (0) [B]")
        self.btn_bust_point.setStyleSheet("background-color: #dc2626; color: white; font-size: 14px; font-weight: bold; padding: 8px;")
        self.btn_bust_point.setToolTip("Fehler / Bust / Abzug (Taste 'B')")
        self.btn_bust_point.clicked.connect(lambda: self._judge_point("BUST"))
        judging_btn_layout.addWidget(self.btn_bust_point)
        scoring_layout.addLayout(judging_btn_layout)

        # Scoreboard Live Display
        scoreboard_layout = QHBoxLayout()
        self.lbl_score_display = QLabel("PUNKTE: 0")
        self.lbl_score_display.setStyleSheet("font-size: 18px; font-weight: bold; color: #22c55e;")
        scoreboard_layout.addWidget(self.lbl_score_display)

        self.lbl_bust_display = QLabel("BUSTS: 0")
        self.lbl_bust_display.setStyleSheet("font-size: 18px; font-weight: bold; color: #ef4444;")
        scoreboard_layout.addWidget(self.lbl_bust_display)

        self.lbl_total_attempted = QLabel("GESAMT: 0")
        self.lbl_total_attempted.setStyleSheet("font-size: 15px; color: #d4d4d8;")
        scoreboard_layout.addWidget(self.lbl_total_attempted)
        scoring_layout.addLayout(scoreboard_layout)

        right_layout.addWidget(card_scoring)

        # Card 3: Debrief Table & Point Log
        card_table = QFrame(right_container)
        card_table.setObjectName("DebriefCard")
        table_card_layout = QVBoxLayout(card_table)
        table_card_layout.setContentsMargins(6, 6, 6, 6)
        table_card_layout.setSpacing(6)

        table_header_layout = QHBoxLayout()
        table_header_layout.addWidget(QLabel("<b>Wertung & Übergangszeiten:</b>"))
        table_header_layout.addStretch()

        btn_delete_point = QPushButton("Punkt löschen")
        btn_delete_point.setToolTip("Ausgewählten Punkt aus Wertung löschen (Taste 'Entf')")
        btn_delete_point.clicked.connect(self._delete_selected_point)
        table_header_layout.addWidget(btn_delete_point)

        btn_clear_points = QPushButton("Alle zurücksetzen")
        btn_clear_points.clicked.connect(self._clear_all_points)
        table_header_layout.addWidget(btn_clear_points)
        table_card_layout.addLayout(table_header_layout)

        # Selected Point Quick-Edit Toolbar (Static 2-row layout prevents size/geometry jumps)
        self.selection_bar = QFrame(card_table)
        self.selection_bar.setObjectName("SelectionBar")
        self.selection_bar.setStyleSheet(
            "background-color: #27272a; border: 1px solid #3f3f46; border-radius: 4px; padding: 2px;"
        )
        self.selection_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sel_layout = QVBoxLayout(self.selection_bar)
        sel_layout.setContentsMargins(6, 4, 6, 4)
        sel_layout.setSpacing(4)

        self.lbl_selected_point_info = QLabel("<i>Kein Punkt ausgewählt &ndash; Nächster Punkt wird gewertet</i>")
        self.lbl_selected_point_info.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        self.lbl_selected_point_info.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sel_layout.addWidget(self.lbl_selected_point_info)

        sel_btns_layout = QHBoxLayout()
        sel_btns_layout.setContentsMargins(0, 0, 0, 0)
        sel_btns_layout.setSpacing(4)

        disabled_btn_style = "background-color: #1f2937; color: #4b5563; font-size: 11px; padding: 2px 6px; border: 1px solid #374151; border-radius: 3px;"

        self.btn_set_sel_complete = QPushButton("⏱️ Fertig (F)")
        self.btn_set_sel_complete.setFixedHeight(24)
        self.btn_set_sel_complete.setStyleSheet(disabled_btn_style)
        self.btn_set_sel_complete.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_set_sel_complete.setToolTip("Fertig-Zeit des ausgewählten Punkts auf die aktuelle Videozeit setzen (Taste 'F')")
        self.btn_set_sel_complete.clicked.connect(lambda: self._set_selected_point_complete_to_current())
        self.btn_set_sel_complete.setEnabled(False)
        sel_btns_layout.addWidget(self.btn_set_sel_complete)

        self.btn_set_sel_key = QPushButton("🔑 Key (K)")
        self.btn_set_sel_key.setFixedHeight(24)
        self.btn_set_sel_key.setStyleSheet(disabled_btn_style)
        self.btn_set_sel_key.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_set_sel_key.setToolTip("Key-Zeit des ausgewählten Punkts auf die aktuelle Videozeit setzen (Taste 'K')")
        self.btn_set_sel_key.clicked.connect(lambda: self._set_selected_point_key_to_current())
        self.btn_set_sel_key.setEnabled(False)
        sel_btns_layout.addWidget(self.btn_set_sel_key)

        self.btn_toggle_sel_status = QPushButton("✓/✗ (S/B)")
        self.btn_toggle_sel_status.setFixedHeight(24)
        self.btn_toggle_sel_status.setStyleSheet(disabled_btn_style)
        self.btn_toggle_sel_status.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_toggle_sel_status.setToolTip("Status des ausgewählten Punkts zwischen SCORE und BUST umschalten (Taste 'S' oder 'B')")
        self.btn_toggle_sel_status.clicked.connect(self._toggle_selected_point_status)
        self.btn_toggle_sel_status.setEnabled(False)
        sel_btns_layout.addWidget(self.btn_toggle_sel_status)

        self.btn_clear_selection = QPushButton("✕ Esc")
        self.btn_clear_selection.setFixedHeight(24)
        self.btn_clear_selection.setStyleSheet(disabled_btn_style)
        self.btn_clear_selection.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_clear_selection.setToolTip("Auswahl aufheben und zurück zu 'Neuer Punkt' (Taste 'Esc')")
        self.btn_clear_selection.clicked.connect(self._clear_point_selection)
        self.btn_clear_selection.setEnabled(False)
        sel_btns_layout.addWidget(self.btn_clear_selection)

        sel_layout.addLayout(sel_btns_layout)
        table_card_layout.addWidget(self.selection_bar)

        self.points_table = QTableWidget(self)
        self.points_table.setColumnCount(8)
        self.points_table.setHorizontalHeaderLabels([
            "#", "Form.", "Status", "Fertig", "Key", "Hold (s)", "Trans (s)", "Notiz"
        ])
        header = self.points_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self.points_table.setColumnWidth(0, 32)
        self.points_table.setColumnWidth(1, 60)
        self.points_table.setColumnWidth(2, 115)
        self.points_table.setColumnWidth(3, 68)
        self.points_table.setColumnWidth(4, 68)
        self.points_table.setColumnWidth(5, 68)
        self.points_table.setColumnWidth(6, 68)

        self.points_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.points_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.points_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.points_table.customContextMenuRequested.connect(self._show_table_context_menu)
        self.points_table.cellDoubleClicked.connect(self._on_table_cell_double_clicked)
        self.points_table.itemClicked.connect(self._on_table_row_clicked)
        self.points_table.itemChanged.connect(self._on_table_item_changed)
        table_card_layout.addWidget(self.points_table)

        right_layout.addWidget(card_table, stretch=1)

        # Card 4: Performance Statistics Summary (Hold Time, Transition Time, Pace)
        card_stats = QFrame(right_container)
        card_stats.setObjectName("DebriefCard")
        stats_layout = QVBoxLayout(card_stats)
        stats_layout.setContentsMargins(10, 8, 10, 8)
        stats_layout.setSpacing(4)

        stats_layout.addWidget(QLabel("<b>Debriefing Analyse:</b>"))
        stats_grid = QHBoxLayout()

        self.lbl_stat_hold = QLabel("Avg Hold: <b>-- s</b>")
        self.lbl_stat_trans = QLabel("Avg Trans: <b>-- s</b>")
        self.lbl_stat_pace = QLabel("Pace: <b>-- s/pt</b>")

        stats_grid.addWidget(self.lbl_stat_hold)
        stats_grid.addWidget(self.lbl_stat_trans)
        stats_grid.addWidget(self.lbl_stat_pace)
        stats_layout.addLayout(stats_grid)

        right_layout.addWidget(card_stats)

        # Splitter Anfangsgrößen
        self.splitter.setSizes([1080, 520])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        # Fokus-Richtlinien optimieren: Buttons und Steuerelemente sollen keinen Tastaturfokus
        # festhalten, damit Shortcuts wie Leertaste, Pfeile, S, B, F, K jederzeit global funktionieren.
        for btn in self.findChildren(QPushButton):
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for rb in self.findChildren(QRadioButton):
            rb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for cb in self.findChildren(QComboBox):
            cb.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.timeline_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.container1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.container1.mpv_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.container1.overlay.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.container2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.container2.mpv_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.container2.overlay.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # QLineEdit: Return-Taste gibt Fokus frei, damit Steuerung sofort wieder global aktiv ist
        self.edit_jump_name.returnPressed.connect(self.edit_jump_name.clearFocus)
        self.edit_draw.returnPressed.connect(self.edit_draw.clearFocus)

        # Tabellennavigation: Zeilenwechsel mit Pfeiltasten springt automatisch zum Punkt im Video
        self.points_table.currentCellChanged.connect(self._on_table_current_changed)

    def _apply_dark_theme(self):
        style = """
        QMainWindow, QWidget {
            background-color: #18181b;
            color: #f4f4f5;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }
        QFrame#HeaderBar {
            background-color: #27272a;
            border-radius: 6px;
            border: 1px solid #3f3f46;
        }
        QFrame#SubToolbar {
            background-color: #27272a;
            border-radius: 6px;
            border: 1px solid #3f3f46;
        }
        QFrame#DebriefCard {
            background-color: #27272a;
            border-radius: 6px;
            border: 1px solid #3f3f46;
        }
        QFrame#TimerBanner {
            background-color: #18181b;
            border-radius: 4px;
            border: 1px solid #52525b;
        }
        QPushButton {
            background-color: #3f3f46;
            color: #f4f4f5;
            border: 1px solid #52525b;
            border-radius: 4px;
            padding: 4px 10px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #52525b;
        }
        QPushButton:pressed {
            background-color: #27272a;
        }
        QLineEdit, QComboBox, QSpinBox {
            background-color: #18181b;
            color: #f4f4f5;
            border: 1px solid #52525b;
            border-radius: 4px;
            padding: 4px;
        }
        QTableWidget {
            background-color: #18181b;
            color: #f4f4f5;
            border: 1px solid #3f3f46;
            gridline-color: #27272a;
            selection-background-color: #38bdf8;
            selection-color: black;
        }
        QHeaderView::section {
            background-color: #27272a;
            color: #d4d4d8;
            padding: 4px;
            border: 1px solid #3f3f46;
            font-weight: bold;
        }
        QProgressBar {
            background-color: #3f3f46;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #22c55e;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(style)

    # -----------------------------------------------------------------
    # Timer & Polling Loop
    # -----------------------------------------------------------------
    def _init_timer(self):
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)  # ~30 fps UI update
        self.ui_timer.timeout.connect(self._on_ui_tick)
        self.ui_timer.start()

    def _on_ui_tick(self):
        player = self.container1.mpv_widget
        cur_time = player.get_time()
        duration = player.get_duration()

        if duration and duration > 0:
            self.timeline_widget.set_duration(duration)
            self.fps = player.get_fps()

        if cur_time is not None:
            self.timeline_widget.set_current_time(cur_time)

            # Timecode Label
            total_dur = duration if duration else 0.0
            frame_num = int(cur_time * self.fps)
            self.lbl_timecode.setText(f"{format_seconds(cur_time)} / {format_seconds(total_dur)} (Fr {frame_num})")

            # Update Play/Pause Button Text
            is_paused = player.is_paused()
            self.btn_play_pause.setText("▶ Play" if is_paused else "⏸ Pause")

            # Working Time Countdown / Elapsed Update
            if self.session.exit_time is not None:
                elapsed_wt = cur_time - self.session.exit_time
                wt_limit = self.session.working_time_duration

                if elapsed_wt < 0:
                    diff = abs(elapsed_wt)
                    self.lbl_timer_status.setText(f"Pre-Exit (-{diff:.1f}s)")
                    self.lbl_timer_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #a1a1aa;")
                    self.timer_progress.setValue(0)
                elif elapsed_wt <= wt_limit:
                    remaining = wt_limit - elapsed_wt
                    pct = int((elapsed_wt / wt_limit) * 1000)
                    self.lbl_timer_status.setText(f"⏱️ {elapsed_wt:04.1f}s / {wt_limit:04.1f}s (Rest: {remaining:04.1f}s)")
                    self.lbl_timer_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #22c55e;")
                    self.timer_progress.setValue(pct)
                else:
                    over = elapsed_wt - wt_limit
                    self.lbl_timer_status.setText(f"⚠️ ZEIT ABGELAUFEN (+{over:.1f}s über {int(wt_limit)}s)")
                    self.lbl_timer_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #ef4444;")
                    self.timer_progress.setValue(1000)

    # -----------------------------------------------------------------
    # Synchronisation des Overlays & Vollbildmodus
    # -----------------------------------------------------------------
    def toggle_fullscreen(self):
        """Schaltet zwischen echtem Fullscreen und maximiertem Fenstermodus um."""
        if self.isFullScreen():
            self.showMaximized()
            if hasattr(self, 'btn_fullscreen'):
                self.btn_fullscreen.setText("⛶ Vollbild [F11]")
        else:
            self.showFullScreen()
            if hasattr(self, 'btn_fullscreen'):
                self.btn_fullscreen.setText("🗗 Fenster [F11]")
        self.sync_overlays()

    def sync_overlays(self):
        if hasattr(self, 'container1'):
            self.container1.sync_overlay()
        if hasattr(self, 'container2') and self.container2.isVisible():
            self.container2.sync_overlay()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.sync_overlays()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_overlays()

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, 'container1'):
            if self.isMinimized() or not self.isVisible():
                self.container1.overlay.hide()
                if hasattr(self, 'container2'):
                    self.container2.overlay.hide()
            else:
                self.sync_overlays()

    # -----------------------------------------------------------------
    # Programmglobale Tastaturkürzel
    # -----------------------------------------------------------------
    def keyPressEvent(self, event):
        if self.handle_global_key(event, self):
            event.accept()
            return
        super().keyPressEvent(event)

    def handle_global_key(self, event, watched=None) -> bool:
        """
        Zentraler Handler für programmglobale Tastaturkürzel im Debriefing & Scoring System.
        Funktioniert unabhängig davon, welches Widget fokusiert ist.
        Gibt True zurück, wenn das Tastaturereignis verarbeitet und konsumiert wurde.
        """
        focused = QApplication.focusWidget()
        is_text_editor = (
            isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit)) or
            isinstance(watched, (QLineEdit, QTextEdit, QPlainTextEdit))
        )

        key = event.key()
        modifiers = event.modifiers()
        has_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        has_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        has_alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)

        # -------------------------------------------------------------
        # A. Verhalten in aktiven Texteingabefeldern (z.B. Draw, Jump Name, Tabellennotiz)
        # -------------------------------------------------------------
        if is_text_editor:
            # Escape: Eingabefeld verlassen und Fokus freigeben
            if key == Qt.Key.Key_Escape:
                if isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit)):
                    focused.clearFocus()
                if isinstance(watched, (QLineEdit, QTextEdit, QPlainTextEdit)):
                    watched.clearFocus()
                self.setFocus()
                return True
            # Alle normalen Tasten dem Eingabefeld überlassen
            return False

        # -------------------------------------------------------------
        # B. Tastenkombinationen mit Strg
        # -------------------------------------------------------------
        if has_ctrl and not has_alt:
            if key == Qt.Key.Key_Z:
                self._undo_drawing()
                return True
            elif key == Qt.Key.Key_S:
                self._save_session_file()
                return True
            elif key == Qt.Key.Key_O:
                self._load_session_file()
                return True
            elif key == Qt.Key.Key_E:
                self._export_debrief_report()
                return True

        # Wenn Alt oder Strg gedrückt sind, keine Single-Key-Aktionen auslösen
        if has_ctrl or has_alt:
            return False

        # -------------------------------------------------------------
        # C. Navigation & Playback Controls
        # -------------------------------------------------------------
        # 1. Play / Pause
        if key == Qt.Key.Key_Space:
            self._toggle_play_pause()
            return True

        # 2. Einzelbild vor / zurück oder 1s Zeitsprung
        elif key == Qt.Key.Key_Right:
            if has_shift:
                self._jump_time(1.0)
            else:
                self._step_frame(True)
            return True

        elif key == Qt.Key.Key_Left:
            if has_shift:
                self._jump_time(-1.0)
            else:
                self._step_frame(False)
            return True

        # -------------------------------------------------------------
        # D. Timer & Event Tracking
        # -------------------------------------------------------------
        # 3. Exit Timer setzen
        elif key == Qt.Key.Key_T:
            self._set_exit_timer_now()
            return True

        # 4. Formation Finished (Griffe geschlossen)
        elif key == Qt.Key.Key_F:
            self._mark_formation_complete()
            return True

        # 5. Key Given (Schlüssel gegeben / Bruch)
        elif key == Qt.Key.Key_K:
            self._mark_key_given()
            return True

        # -------------------------------------------------------------
        # E. Point Judging (Score vs Bust)
        # -------------------------------------------------------------
        # 6. Punkt Werten (Score +1): Taste S oder 1 (inkl. Ziffernblock)
        elif key in (Qt.Key.Key_S, Qt.Key.Key_1):
            self._judge_point("APPROVED")
            return True

        # 7. Fehler Werten (Bust 0): Taste B oder 0 (inkl. Ziffernblock)
        elif key in (Qt.Key.Key_B, Qt.Key.Key_0):
            self._judge_point("BUST")
            return True

        # -------------------------------------------------------------
        # F. Trimming In/Out
        # -------------------------------------------------------------
        # 8. Start Frame (In): Taste [ oder I
        elif key in (Qt.Key.Key_BracketLeft, Qt.Key.Key_I):
            self._mark_in_point()
            return True

        # 9. End Frame (Out): Taste ] oder O
        elif key in (Qt.Key.Key_BracketRight, Qt.Key.Key_O):
            self._mark_out_point()
            return True

        # -------------------------------------------------------------
        # G. Telestration & Bearbeitung
        # -------------------------------------------------------------
        # 10. Escape: Telestration abbrechen / Cursor-Modus aktivieren
        # 10. Escape: Telestration abbrechen / Punkt-Auswahl aufheben
        elif key == Qt.Key.Key_Escape:
            is_overlay_active = (hasattr(self, 'container1') and self.container1.overlay.mode != "NONE")
            if not self.btn_tool_none.isChecked() or is_overlay_active:
                self.btn_tool_none.setChecked(True)
                self._set_draw_mode("NONE")
            elif self.selected_point_index is not None:
                self._clear_point_selection()
            else:
                if self.pending_complete_time is not None or self.pending_key_time is not None:
                    self.pending_complete_time = None
                    self.pending_key_time = None
                    self.lbl_pending_event.setText("Bereit für Wertung")
                    self.lbl_pending_event.setStyleSheet("color: #a1a1aa; font-size: 11px;")
                self.points_table.clearSelection()
            self.setFocus()
            return True

        # 11. Punkt löschen: Entf oder Backspace
        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.points_table.currentRow() >= 0:
                self._delete_selected_point()
                return True

        # 12. Hilfe anzeigen: F1 oder ?
        elif key in (Qt.Key.Key_F1, Qt.Key.Key_Question):
            self._show_shortcuts_help()
            return True

        # 13. Vollbild umschalten: F11
        elif key == Qt.Key.Key_F11:
            self.toggle_fullscreen()
            return True

        return False

    def _show_shortcuts_help(self):
        """Öffnet ein ausführliches Hilfe- und Dokumentationsfenster zu Wertung, Zeitmessung und Shortcuts."""
        dlg = QDialog(self)
        dlg.setWindowTitle("❓ Hilfe: Wertung, Zeitmessung & Tastaturkürzel")
        dlg.resize(680, 640)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(14, 12, 14, 12)
        dlg_layout.setSpacing(10)

        tabs = QTabWidget(dlg)

        # -------------------------------------------------------------
        # TAB 1: Wertungs- & Zeitlogik (Debriefing Guide)
        # -------------------------------------------------------------
        tab_guide = QWidget()
        l_guide = QVBoxLayout(tab_guide)
        l_guide.setContentsMargins(10, 10, 10, 10)

        txt_guide = QTextEdit()
        txt_guide.setReadOnly(True)
        txt_guide.setHtml("""
        <h3 style="color: #38bdf8; margin-top: 0;">⏱️ Wie Zählen, Fertig und Key zusammenarbeiten</h3>
        <p>In 4-Way Formation Skydiving basiert jedes Debriefing auf drei aufeinander aufbauenden Ereignissen pro Punkt:</p>

        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; border-color: #3f3f46; width: 100%;">
            <tr style="background-color: #27272a;">
                <th>Ereignis / Taste</th>
                <th>Bedeutung (FAI Definition)</th>
                <th>Wirkung im System</th>
            </tr>
            <tr>
                <td><b style="color: #38bdf8;">🏁 Formation Fertig [F]</b><br>(Completion)</td>
                <td>Der exakte Video-Zeitpunkt, an dem <b>alle 4 Springer alle erforderlichen Griffe</b> der Formation geschlossen haben.</td>
                <td>Setzt den Griffschluss-Zeitpunkt (<code>Fertig-Zeit</code>). Beendet die Übergangszeit (Transition) der Formation.</td>
            </tr>
            <tr>
                <td><b style="color: #f59e0b;">🔑 Key Gegeben [K]</b><br>(Break / Key)</td>
                <td>Der Zeitpunkt, an dem der Keyer (z.B. Inside Center oder Point) das <b>Signal zum Bruch</b> der Formation gibt (z.B. Kopfnicken, Griff-Flash).</td>
                <td>Setzt den <code>Key-Zeitpunkt</code>. Beendet die Haltezeit (Hold Time) dieser Formation und startet die Übergangszeit (Transition) zur nächsten Formation.</td>
            </tr>
            <tr>
                <td><b style="color: #22c55e;">✅ Score (+1) [S]</b><br><b style="color: #ef4444;">❌ Bust (0) [B]</b></td>
                <td>Die <b>Wertungsentscheidung</b>: Formation war korrekt geflogen und gehalten (+1) oder fehlerhaft / unvollständig / Bust (0).</td>
                <td>Erstellt und speichert den gewerteten Punkt mit den erfassten Zeiten in der Tabelle und auf der Zeitleiste.</td>
            </tr>
        </table>

        <h4 style="color: #e4e4e7; margin-top: 14px;">📐 Berechnung der Zeiten in der Wertungstabelle</h4>
        <ul>
            <li><b>Hold Time (Haltezeit):</b>
                <code>Hold = Key-Zeit - Fertig-Zeit</code><br>
                Gibt an, wie viele Sekunden die Formation ruhig und sichtbar für den Videographer gehalten wurde. <i>(Ein negativer Wert signalisiert, dass der Key vor dem Griffschluss gesetzt wurde).</i>
            </li>
            <li><b>Transition Time (Übergangszeit):</b>
                <br>• <b>Für Punkt #1:</b> <code>Transition = Fertig-Zeit(1) - Exit-Zeit</code> (Zeit vom Flugzeug-Exit bis zum ersten Griffschluss).
                <br>• <b>Für Punkt i > 1:</b> <code>Transition = Fertig-Zeit(i) - Key-Zeit(i-1)</code> (Zeit vom Key der Vorformation bis zum Griffschluss der neuen Formation).
                <br><i>(Wurde beim vorherigen Punkt kein Key markiert, wird ersatzweise die Fertig-Zeit der Vorformation als Referenz herangezogen).</i>
            </li>
            <li><b>Working Time (Arbeitszeit):</b>
                Die offizielle Arbeitszeit beginnt bei <b>Exit [T]</b> (meist 35s im Wettbewerb). Punkte, deren Griffschluss nach Ablauf der Arbeitszeit liegt, werden mit <code>(Out of WT)</code> gekennzeichnet.
            </li>
        </ul>

        <h4 style="color: #e4e4e7; margin-top: 14px;">🧩 FAI Blöcke (1-22) = 2 separate Punkte</h4>
        <p>Ein FAI Block besteht aus zwei eigenständigen Formationen (Initial & Close) mit einer Zwischenbewegung (Inter).
        Beim Eingeben eines Blocks (z.B. <code>12</code>) erzeugt das System automatisch <b>zwei getrennte Wertungspunkte</b> in der Sequenz:
        <br>• <b>12-1</b> (Teil 1: Initial-Formation, z.B. Bundy)
        <br>• <b>12-2</b> (Teil 2: Close-Formation nach dem Inter, z.B. Bundy)</p>

        <h4 style="color: #e4e4e7; margin-top: 14px;">✏️ Nachträgliches Bearbeiten & Draw-Änderung</h4>
        <ul>
            <li><b>Punkt korrigieren:</b> Klicke einen Punkt in der Tabelle oder auf der Zeitleiste an. Mit <b>[F]</b> kannst du die Fertig-Zeit und mit <b>[K]</b> die Key-Zeit auf die aktuelle Videoposition korrigieren! Mit <b>[S] / [B]</b> änderst du den Status. Mit <b>Escape</b> hebst du die Auswahl auf.</li>
            <li><b>Draw nachträglich anpassen:</b> Du hast das Draw falsch eingegeben? Korrigiere einfach das Textfeld und klicke auf <b>[🔄 Draw anwenden]</b>. Alle bereits gewerteten Punkte erhalten die neuen Formationsbezeichnungen, während alle Zeiten und Notizen erhalten bleiben!</li>
        </ul>
        """)
        l_guide.addWidget(txt_guide)
        tabs.addTab(tab_guide, "⏱️ Wertungs- & Zeitlogik")

        # -------------------------------------------------------------
        # TAB 2: Tastaturkürzel
        # -------------------------------------------------------------
        tab_shortcuts = QWidget()
        l_shortcuts = QVBoxLayout(tab_shortcuts)
        l_shortcuts.setContentsMargins(10, 10, 10, 10)

        lbl_sc_info = QLabel(
            "Alle Tastaturkürzel funktionieren im gesamten Programm zuverlässig.<br>"
            "<i>(Bei aktiver Texteingabe tippen Tasten normal. Mit <b>Escape</b> oder <b>Enter</b> verlässt du Textfelder).</i>"
        )
        lbl_sc_info.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        l_shortcuts.addWidget(lbl_sc_info)

        shortcuts_table = QTableWidget(dlg)
        shortcuts_table.setColumnCount(2)
        shortcuts_table.setHorizontalHeaderLabels(["Taste / Kürzel", "Aktion"])
        shortcuts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        shortcuts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        shortcuts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        shortcuts_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        items = [
            ("Leertaste", "Video abspielen / pausieren (Play / Pause)"),
            ("Pfeil Rechts (➔)", "1 Einzelbild vor (Frame-Step Vor)"),
            ("Pfeil Links (⬅)", "1 Einzelbild zurück (Frame-Step Zurück)"),
            ("Shift + Pfeil Rechts", "1 Sekunde vorwärts springen"),
            ("Shift + Pfeil Links", "1 Sekunde rückwärts springen"),
            ("T", "Exit-Zeitpunkt / Working Time Timer Start setzen"),
            ("F", "Formation Fertig markieren (bei Auswahl: Fertig-Zeit des Punkts korrigieren)"),
            ("K", "Key markieren (bei Auswahl: Key-Zeit des Punkts korrigieren)"),
            ("S  oder  1", "Punkt anerkennen & werten (+1 SCORE / Status ändern)"),
            ("B  oder  0", "Fehler / Bust werten (0 BUST / Status ändern)"),
            ("[  oder  I", "Start Frame für Videoschnitt setzen (In-Point)"),
            ("]  oder  O", "End Frame für Videoschnitt setzen (Out-Point)"),
            ("Entf / Backspace", "Ausgewählten Punkt aus Wertung löschen"),
            ("Pfeil Oben / Unten", "In Wertungstabelle navigieren (springt zum Punkt im Video)"),
            ("Strg + Z", "Letzte Telestration-Zeichnung rückgängig"),
            ("Escape", "Telestration zurücksetzen / Punkt-Auswahl aufheben"),
            ("Strg + S", "Session speichern (.json)"),
            ("Strg + O", "Session laden (.json)"),
            ("Strg + E", "Debriefing Report exportieren (.md)"),
            ("F1", "Diese Hilfe & Dokumentation anzeigen"),
            ("F11", "Vollbildmodus (Fullscreen) ein- / ausschalten"),
        ]

        shortcuts_table.setRowCount(len(items))
        for row, (key_txt, desc_txt) in enumerate(items):
            item_k = QTableWidgetItem(key_txt)
            item_k.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            item_k.setForeground(QColor(56, 189, 248))
            shortcuts_table.setItem(row, 0, item_k)

            item_d = QTableWidgetItem(desc_txt)
            shortcuts_table.setItem(row, 1, item_d)

        l_shortcuts.addWidget(shortcuts_table)
        tabs.addTab(tab_shortcuts, "⌨️ Tastaturkürzel")

        dlg_layout.addWidget(tabs)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Schließen", dlg)
        btn_close.clicked.connect(dlg.accept)
        btn_box.addWidget(btn_close)
        dlg_layout.addLayout(btn_box)

        dlg.exec()

    # -----------------------------------------------------------------
    # Playback & Navigation Controls
    # -----------------------------------------------------------------
    def _toggle_play_pause(self):
        p1 = self.container1.mpv_widget
        new_state = not p1.is_paused()
        p1.set_pause(new_state)
        if self.container2.isVisible():
            self.container2.mpv_widget.set_pause(new_state)

    def _step_frame(self, forward: bool):
        self.container1.mpv_widget.step_frame(forward)
        if self.container2.isVisible():
            self.container2.mpv_widget.step_frame(forward)

    def _jump_time(self, delta_sec: float):
        t = self.container1.mpv_widget.get_time()
        if t is not None:
            self._seek_to_time(t + delta_sec)

    def _seek_to_time(self, seconds: float):
        self.container1.mpv_widget.seek(seconds)
        if self.container2.isVisible():
            self.container2.mpv_widget.seek(seconds)

    def _on_speed_changed(self, text: str):
        try:
            val = float(text.replace("x", ""))
            self.container1.mpv_widget.set_speed(val)
            if self.container2.isVisible():
                self.container2.mpv_widget.set_speed(val)
        except ValueError:
            pass

    def _toggle_dual_cam(self, checked: bool):
        if checked:
            if hasattr(self, 'cam2_box'):
                self.cam2_box.show()
            else:
                self.container2.show()
            if hasattr(self, 'lbl_cam1_title'):
                self.lbl_cam1_title.show()
            if hasattr(self, 'btn_load_cam2'):
                self.btn_load_cam2.show()
            self.btn_toggle_dual.setText("👤 Single Cam Ansicht")
        else:
            if hasattr(self, 'cam2_box'):
                self.cam2_box.hide()
            else:
                self.container2.hide()
            if hasattr(self, 'lbl_cam1_title'):
                self.lbl_cam1_title.hide()
            if hasattr(self, 'btn_load_cam2'):
                self.btn_load_cam2.hide()
            self.btn_toggle_dual.setText("👥 Dual Cam Ansicht")
        self.sync_overlays()

    # -----------------------------------------------------------------
    # Drawing Overlay Controls
    # -----------------------------------------------------------------
    def _set_draw_mode(self, mode: str):
        self.container1.overlay.set_mode(mode)
        self.container2.overlay.set_mode(mode)

    def _undo_drawing(self):
        self.container1.overlay.undo_last()
        self.container2.overlay.undo_last()

    def _clear_drawings(self):
        self.container1.overlay.clear_drawings()
        self.container2.overlay.clear_drawings()

    # -----------------------------------------------------------------
    # Video-Pfade, Standard-Ordner & Quick Links
    # -----------------------------------------------------------------
    def get_default_video_dir(self) -> str:
        d = self.settings.value("paths/default_video_dir", "")
        if d and os.path.isdir(str(d)):
            return str(d)
        vid_dir = os.path.expanduser("~/Videos")
        if os.path.isdir(vid_dir):
            return vid_dir
        return os.path.expanduser("~")

    def set_default_video_dir(self, directory: str):
        if directory and os.path.isdir(directory):
            self.settings.setValue("paths/default_video_dir", directory)
            self.settings.sync()

    def get_quick_link_dirs(self) -> List[str]:
        raw = self.settings.value("paths/quick_links", [])
        if isinstance(raw, str):
            res = [p.strip() for p in raw.split(";") if p.strip()]
        elif isinstance(raw, list):
            res = [str(p) for p in raw if p]
        else:
            res = []
        return [p for p in res if os.path.isdir(p)]

    def set_quick_link_dirs(self, dirs: List[str]):
        clean = [p for p in dirs if p and os.path.isdir(p)]
        self.settings.setValue("paths/quick_links", clean)
        self.settings.sync()

    def get_recent_videos(self) -> List[str]:
        raw = self.settings.value("paths/recent_videos", [])
        if isinstance(raw, str):
            res = [p.strip() for p in raw.split(";") if p.strip()]
        elif isinstance(raw, list):
            res = [str(p) for p in raw if p]
        else:
            res = []
        return [p for p in res if os.path.isfile(p)]

    def add_recent_video(self, file_path: str):
        if not file_path or not os.path.isfile(file_path):
            return
        recents = self.get_recent_videos()
        if file_path in recents:
            recents.remove(file_path)
        recents.insert(0, file_path)
        recents = recents[:12]
        self.settings.setValue("paths/recent_videos", recents)
        self.settings.sync()

    def _open_video_paths_dialog(self):
        dlg = VideoPathsDialog(self)
        dlg.exec()

    def _choose_video_file(self, title: str) -> Optional[str]:
        """Öffnet Dateidialog mit konfiguriertem Default-Ordner und Quick Links in der Seitenleiste."""
        start_dir = self.get_default_video_dir()
        dlg = QFileDialog(self, title, start_dir, "Video Files (*.mp4 *.MP4 *.mov *.MOV *.mkv *.avi)")
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)

        # Quick Links als Sidebar URLs in den Dateidialog einhängen
        quick_urls = [QUrl.fromLocalFile(p) for p in self.get_quick_link_dirs()]
        existing = dlg.sidebarUrls()
        dlg.setSidebarUrls(quick_urls + [u for u in existing if u not in quick_urls])

        if dlg.exec():
            selected = dlg.selectedFiles()
            if selected:
                chosen = selected[0]
                self.add_recent_video(chosen)
                return chosen
        return None

    def _show_quick_links_menu(self):
        """Dropdown-Menü für schnellen Ordner- & Video-Zugriff."""
        menu = QMenu(self)

        links = self.get_quick_link_dirs()
        if links:
            menu.addSection("⭐ Quick-Link Ordner")
            for path in links:
                act = menu.addAction(f"📂 {os.path.basename(path)}  ({path})")
                def _open_in_dir(p=path):
                    dlg = QFileDialog(self, f"Video wählen in {p}", p, "Video Files (*.mp4 *.MP4 *.mov *.MOV *.mkv *.avi)")
                    dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
                    quick_urls = [QUrl.fromLocalFile(q) for q in self.get_quick_link_dirs()]
                    existing = dlg.sidebarUrls()
                    dlg.setSidebarUrls(quick_urls + [u for u in existing if u not in quick_urls])
                    if dlg.exec():
                        sel = dlg.selectedFiles()
                        if sel:
                            self._load_selected_video1(sel[0])
                act.triggered.connect(_open_in_dir)

        recents = self.get_recent_videos()
        if recents:
            menu.addSection("🕒 Zuletzt geöffnete Videos")
            for r in recents[:8]:
                act = menu.addAction(f"🎬 {os.path.basename(r)}")
                act.setToolTip(r)
                act.triggered.connect(lambda checked=False, p=r: self._load_selected_video1(p))

        menu.addSeparator()
        act_scan = menu.addAction("🔍 Nach GoPro / SD-Karte suchen...")
        def _scan_and_show():
            found = find_connected_camera_folders()
            if found:
                curr = self.get_quick_link_dirs()
                added = 0
                for f in found:
                    if f not in curr:
                        curr.append(f)
                        added += 1
                if added > 0:
                    self.set_quick_link_dirs(curr)
                    QMessageBox.information(self, "Kamera gefunden", f"{added} Kamera-/SD-Karten-Ordner zu Quick Links hinzugefügt!")
                else:
                    QMessageBox.information(self, "Kamera gefunden", "Gefundene Kamera-Ordner sind bereits in den Quick Links.")
            else:
                QMessageBox.information(self, "Kamera-Suche", "Keine GoPro / SD-Karte unter /media oder /run/media gefunden.")
        act_scan.triggered.connect(_scan_and_show)

        act_settings = menu.addAction("⚙️ Pfade & Quick Links konfigurieren...")
        act_settings.triggered.connect(self._open_video_paths_dialog)

        menu.exec(self.btn_quick_links.mapToGlobal(QPoint(0, self.btn_quick_links.height())))

    # -----------------------------------------------------------------
    # Video Loading & Trimming (GoPro Cutter)
    # -----------------------------------------------------------------
    def _open_raw_video(self):
        path = self._choose_video_file("Cam 1 Video (Hauptkamera) wählen")
        if path:
            self._load_selected_video1(path)

    def _load_selected_video1(self, path: str):
        if not path or not os.path.exists(path):
            return
        self.session.video_path = path
        self.container1.mpv_widget.load_video(path)
        self.session.in_point = None
        self.session.out_point = None
        self._update_in_out_labels()
        self.timeline_widget.set_in_out(None, None)
        fname = os.path.basename(path)
        if hasattr(self, 'btn_load_raw'):
            self.btn_load_raw.setText(f"📹 Cam 1: {fname[:12]}...")
        if hasattr(self, 'lbl_cam1_title'):
            self.lbl_cam1_title.setText(f"📹 <b>Cam 1:</b> {fname}")
        self.add_recent_video(path)

    def _open_cam2_video(self):
        path = self._choose_video_file("Cam 2 Video (Zweitkamera) wählen")
        if path:
            self.session.video_path_cam2 = path
            self.container2.mpv_widget.load_video(path)

            # Auf die aktuelle Zeitposition von Cam 1 synchronisieren
            t1 = self.container1.mpv_widget.get_time()
            if t1 is None:
                t1 = getattr(self.timeline_widget, 'current_time', 0.0)
            if t1 is not None:
                self.container2.mpv_widget.seek(t1)

            # Pause-Status von Cam 1 übernehmen
            is_paused = self.container1.mpv_widget.is_paused()
            self.container2.mpv_widget.set_pause(is_paused)

            fname = os.path.basename(path)
            if hasattr(self, 'btn_load_cam2'):
                self.btn_load_cam2.setText(f"📹 Cam 2: {fname[:12]}...")
            if hasattr(self, 'lbl_cam2_title'):
                self.lbl_cam2_title.setText(f"📹 <b>Cam 2:</b> {fname}")
            self.sync_overlays()
            self.add_recent_video(path)

    def _mark_in_point(self):
        t = self.container1.mpv_widget.get_time()
        if t is None:
            t = getattr(self.timeline_widget, 'current_time', 0.0)
        self.session.in_point = t
        self._update_in_out_labels()
        self.timeline_widget.set_in_out(self.session.in_point, self.session.out_point)

    def _mark_out_point(self):
        t = self.container1.mpv_widget.get_time()
        if t is None:
            t = getattr(self.timeline_widget, 'current_time', 0.0)
        self.session.out_point = t
        self._update_in_out_labels()
        self.timeline_widget.set_in_out(self.session.in_point, self.session.out_point)

    def _update_in_out_labels(self):
        in_str = format_seconds(self.session.in_point) if self.session.in_point is not None else "--:--"
        out_str = format_seconds(self.session.out_point) if self.session.out_point is not None else "--:--"
        self.lbl_in_point.setText(f"In: {in_str}")
        self.lbl_out_point.setText(f"Out: {out_str}")

        if self.session.in_point is not None and self.session.out_point is not None:
            dur = max(0.0, self.session.out_point - self.session.in_point)
            self.lbl_cut_duration.setText(f"(Dauer: {dur:.2f}s)")
        else:
            self.lbl_cut_duration.setText("(Dauer: --:--)")

    def _cut_video_ffmpeg(self):
        if not self.session.video_path or not os.path.exists(self.session.video_path):
            QMessageBox.warning(self, "Kein Video geladen", "Bitte lade zuerst ein GoPro Video.")
            return

        if self.session.in_point is None or self.session.out_point is None:
            QMessageBox.warning(self, "Schnittpunkte fehlen",
                                "Bitte setze sowohl Start Frame (In) als auch End Frame (Out).")
            return

        if self.session.in_point >= self.session.out_point:
            QMessageBox.warning(self, "Ungültiger Bereich", "Der Start Frame muss vor dem End Frame liegen.")
            return

        # Vorschlag für Ausgabedatei generieren
        base, ext = os.path.splitext(self.session.video_path)
        default_out = f"{base}_cut.mp4"

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Geschnittenes Debrief-Video speichern (Kein Ton)", default_out, "MP4 Video (*.mp4)"
        )
        if not out_path:
            return

        # Schnitt-Dialog öffnen & ffmpeg ausführen
        dialog = VideoCutterDialog(
            input_path=self.session.video_path,
            start_sec=self.session.in_point,
            end_sec=self.session.out_point,
            output_path=out_path,
            parent=self
        )
        dialog.cut_completed.connect(self._on_video_cut_success)
        dialog.start_cut()
        dialog.exec()

    def _on_video_cut_success(self, output_path: str):
        # Das geschnittene Video direkt in den Player laden!
        self.session.video_path = output_path
        self.container1.mpv_widget.load_video(output_path)
        self.session.in_point = None
        self.session.out_point = None
        self._update_in_out_labels()
        self.timeline_widget.set_in_out(None, None)
        fname = os.path.basename(output_path)
        if hasattr(self, 'btn_load_raw'):
            self.btn_load_raw.setText(f"📹 Cam 1: {fname[:12]}...")
        if hasattr(self, 'lbl_cam1_title'):
            self.lbl_cam1_title.setText(f"📹 <b>Cam 1:</b> {fname}")
        self.add_recent_video(output_path)
        QMessageBox.information(
            self, "Schnitt Erfolgreich",
            f"Das geschnittene Sprungvideo wurde erfolgreich erstellt und für das Debriefing geladen:\n{os.path.basename(output_path)}"
        )

    # -----------------------------------------------------------------
    # Formations & Jump Draw Management
    # -----------------------------------------------------------------
    def _on_jump_name_changed(self, text: str):
        self.session.jump_name = text

    def _on_draw_changed(self, text: str):
        self.session.draw_string = text
        self._update_sequence_chips()
        self._update_next_formation_indicator()

    def _open_dive_pool_helper(self):
        dlg = DivePoolDialog(self)
        dlg.formation_selected.connect(self._append_formation_to_draw)
        dlg.exec()

    def _open_draw_generator_dialog(self, initial_tab: int = 0):
        """Öffnet den interaktiven Draw Generator, die Trainings-Datenbank und die Rhythm XP Karten."""
        try:
            from draw_dialog import DrawGeneratorDialog
            dlg = DrawGeneratorDialog(self)
            if initial_tab > 0 and initial_tab < dlg.tabs.count():
                dlg.tabs.setCurrentIndex(initial_tab)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte Draw Generator nicht öffnen:\n{e}")

    def _show_single_card_dialog(self, code: str):
        """Zeigt ein Pop-up-Fenster mit der originalen Rhythm XP Bildkarte für eine Formation."""
        try:
            import card_manager
            pix = card_manager.get_card_pixmap(code, max_width=380, max_height=420)
            if not pix:
                QMessageBox.information(self, "Info", f"Keine Rhythm XP Bildkarte für '{code}' gefunden.")
                return
            dlg = QDialog(self)
            dlg.setWindowTitle(f"🖼️ Rhythm XP Karte: {code}")
            l = QVBoxLayout(dlg)
            lbl = QLabel()
            lbl.setPixmap(pix)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte Bild nicht laden:\n{e}")

    def _append_formation_to_draw(self, code: str):
        cur = self.session.draw_string.strip()
        if cur:
            self.session.draw_string = f"{cur} - {code}"
        else:
            self.session.draw_string = code
        self.edit_draw.setText(self.session.draw_string)
        self._update_sequence_chips()
        self._update_next_formation_indicator()

    def _apply_draw_to_existing_points(self):
        """Passt die Formationsbezeichnungen aller bestehenden Punkte an die aktuelle Draw-Sequenz an."""
        if not self.session.points:
            QMessageBox.information(self, "Keine Punkte", "Es sind noch keine Punkte zum Anpassen vorhanden.")
            return

        seq = self.session.draw_sequence
        if not seq:
            QMessageBox.warning(self, "Ungültiges Draw", "Bitte gib eine gültige Draw-Sequenz ein (z.B. A - 12 - 7 - B).")
            return

        reply = QMessageBox.question(
            self, "Draw auf Punkte anwenden?",
            f"Möchtest du die Formationen aller {len(self.session.points)} gewerteten Punkte an die Sequenz:\n"
            f"'{self.session.draw_string}' anpassen?\n\n"
            f"Alle gemessenen Zeiten, Keys, Status (Score/Bust) und Notizen bleiben unverändert erhalten!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for i, pt in enumerate(self.session.points):
                info = self.session.expected_formation_for_point(i)
                pt.formation = info['code']
            self._update_sequence_chips()
            self._update_next_formation_indicator()
            self._update_table_and_stats()
            self._update_selection_controls()
            QMessageBox.information(self, "Erfolgreich", "Formationen der Punkte wurden erfolgreich an das neue Draw angepasst.")

    def _update_sequence_chips(self):
        # Vorherige Widgets im Chip Layout leeren
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        seq = self.session.draw_sequence
        if not seq:
            lbl = QLabel("<i>Keine Formationen eingegeben (z.B. A - 12 - 7 - B)</i>")
            lbl.setStyleSheet("color: #71717a;")
            self.chips_layout.addWidget(lbl)
            self.chips_layout.addStretch()
            return

        next_idx = len(self.session.points) % len(seq)

        for i, info in enumerate(seq):
            code = info['code']
            base = info['base']
            part = info['part']
            name = info['name']

            chip = QPushButton(f"<b>{code}</b>")
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setFixedHeight(28)
            chip.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            part_tip = f" (Block {base} Teil {part})" if info['is_block'] else ""
            chip.setToolTip(f"{code}{part_tip}: {name}\n• Linksklick: 3D Visualisierung\n• Rechtsklick: Rhythm XP Bildkarte anzeigen")
            chip.clicked.connect(lambda checked=False, b=base, p=part: self._open_3d_explorer_for_formation(b, p))
            chip.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            chip.customContextMenuRequested.connect(lambda pos, c=code: self._show_single_card_dialog(c))

            if i == next_idx:
                chip.setStyleSheet(
                    "background-color: #38bdf8; color: black; font-weight: bold; border-radius: 4px; padding: 2px 10px;"
                )
            else:
                chip.setStyleSheet(
                    "background-color: #3f3f46; color: #f4f4f5; border-radius: 4px; padding: 2px 8px;"
                )

            self.chips_layout.addWidget(chip)

            if i < len(seq) - 1:
                arrow = QLabel("➔")
                arrow.setStyleSheet("color: #71717a; font-weight: bold;")
                self.chips_layout.addWidget(arrow)

        self.chips_layout.addSpacing(12)
        btn_view_cards = QPushButton("🖼️ Rhythm XP Karten")
        btn_view_cards.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_view_cards.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view_cards.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; border: 1px solid #0284c7; border-radius: 4px; padding: 2px 8px; font-size: 11px;"
        )
        btn_view_cards.setToolTip("Zeigt die offiziellen Rhythm XP Bildkarten für das aktuelle Draw an")
        btn_view_cards.clicked.connect(lambda: self._open_draw_generator_dialog(0))
        self.chips_layout.addWidget(btn_view_cards)

        self.chips_layout.addStretch()

    def _open_3d_explorer_for_current(self):
        info = self._get_next_expected_formation_info()
        self._open_3d_explorer_for_formation(info['base'], info['part'])

    def _open_3d_explorer_for_formation(self, base_code: str, part: int = 0):
        try:
            import formation_tool
            clean_base = re.sub(r'[-._].*$', '', base_code.strip()) or "A"

            # Check if existing window is still alive and valid
            win_alive = False
            if hasattr(self, "_formation_explorer_window") and self._formation_explorer_window is not None:
                try:
                    # Accessing a Qt property will fail if C++ object was destroyed
                    _ = self._formation_explorer_window.windowTitle()
                    win_alive = True
                except RuntimeError:
                    win_alive = False

            if not win_alive:
                self._formation_explorer_window = formation_tool.FormationExplorerWindow(clean_base)

            self._formation_explorer_window.select_formation(clean_base, part)
            self._formation_explorer_window.show()
            self._formation_explorer_window.raise_()
            self._formation_explorer_window.activateWindow()
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"3D Explorer konnte nicht geöffnet werden: {e}")

    def _open_3d_explorer_for_code(self, code: str):
        self._open_3d_explorer_for_formation(code, 0)

    def _get_next_expected_formation_info(self) -> Dict[str, Any]:
        return self.session.expected_formation_for_point(len(self.session.points))

    def _get_next_expected_formation(self) -> str:
        return self._get_next_expected_formation_info()['code']

    def _update_next_formation_indicator(self):
        info = self._get_next_expected_formation_info()
        next_form = info['code']
        pt_num = len(self.session.points) + 1
        seq_len = self.session.points_per_cycle()
        cycle = (len(self.session.points) // seq_len + 1) if seq_len else 1

        detail = f" ({info['name']})" if info.get('name') else ""
        if info.get('is_block'):
            p_desc = "Initial" if info.get('part') == 1 else "Close"
            detail = f" (Block {info['base']} Teil {info['part']}: {p_desc} &ndash; {info['name']})"

        self.lbl_next_formation.setText(
            f"Nächste Formation: <b>{next_form}</b>{detail} &nbsp;|&nbsp; <b>Punkt #{pt_num}</b> (Zyklus {cycle})"
        )

    # -----------------------------------------------------------------
    # Working Time & Timer Events
    # -----------------------------------------------------------------
    def _on_wt_preset_changed(self, text: str):
        if "35s" in text:
            self.session.working_time_duration = 35.0
        elif "20s" in text:
            self.session.working_time_duration = 20.0
        elif "60s" in text:
            self.session.working_time_duration = 60.0
        self.timeline_widget.set_working_time(self.session.exit_time, self.session.working_time_duration)
        self._update_table_and_stats()

    def _set_exit_timer_now(self):
        t = self.container1.mpv_widget.get_time()
        if t is None:
            t = getattr(self.timeline_widget, 'current_time', 0.0)
        self.session.exit_time = t
        self.timeline_widget.set_working_time(self.session.exit_time, self.session.working_time_duration)
        self._update_table_and_stats()

    def _reset_exit_timer(self):
        self.session.exit_time = None
        self.timeline_widget.set_working_time(None, self.session.working_time_duration)
        self.lbl_timer_status.setText("Timer nicht gestartet")
        self.timer_progress.setValue(0)
        self._update_table_and_stats()

    # -----------------------------------------------------------------
    # Formation Finished, Key Given & Point Judging
    # -----------------------------------------------------------------
    def _update_selection_controls(self):
        """Aktualisiert die Aktionsleiste für den ausgewählten Punkt (ohne Geometrie-Sprünge)."""
        has_sel = (self.selected_point_index is not None and 0 <= self.selected_point_index < len(self.session.points))
        if hasattr(self, 'btn_set_sel_complete'):
            self.btn_set_sel_complete.setEnabled(has_sel)
            self.btn_set_sel_key.setEnabled(has_sel)
            self.btn_toggle_sel_status.setEnabled(has_sel)
            self.btn_clear_selection.setEnabled(has_sel)

            if has_sel:
                pt = self.session.points[self.selected_point_index]
                self.selection_bar.setStyleSheet(
                    "background-color: #1e293b; border: 1px solid #38bdf8; border-radius: 4px; padding: 2px;"
                )
                self.lbl_selected_point_info.setText(
                    f"🎯 <b>Punkt #{pt.point_num} ({pt.formation}) ausgewählt</b> | Status: <b>{pt.status}</b> | "
                    f"Fertig: {format_seconds(pt.time_complete)} | Key: {format_seconds(pt.time_key)}"
                )
                self.lbl_selected_point_info.setStyleSheet("color: #38bdf8; font-size: 11px;")
                self.btn_set_sel_complete.setStyleSheet(
                    "background-color: #0284c7; color: white; font-size: 11px; padding: 2px 6px; font-weight: bold; border-radius: 3px;"
                )
                self.btn_set_sel_key.setStyleSheet(
                    "background-color: #d97706; color: white; font-size: 11px; padding: 2px 6px; font-weight: bold; border-radius: 3px;"
                )
                self.btn_toggle_sel_status.setStyleSheet(
                    "background-color: #4b5563; color: white; font-size: 11px; padding: 2px 6px; font-weight: bold; border-radius: 3px;"
                )
                self.btn_clear_selection.setStyleSheet(
                    "background-color: #27272a; color: #f43f5e; font-size: 11px; padding: 2px 6px; border: 1px solid #475569; border-radius: 3px;"
                )
            else:
                self.selection_bar.setStyleSheet(
                    "background-color: #27272a; border: 1px solid #3f3f46; border-radius: 4px; padding: 2px;"
                )
                pt_num = len(self.session.points) + 1
                next_f = self._get_next_expected_formation()
                self.lbl_selected_point_info.setText(
                    f"<i>Kein Punkt ausgewählt &ndash; Nächster Punkt #{pt_num} ({next_f}) wird bei S/B gewertet</i>"
                )
                self.lbl_selected_point_info.setStyleSheet("color: #a1a1aa; font-size: 11px;")
                disabled_style = "background-color: #1f2937; color: #4b5563; font-size: 11px; padding: 2px 6px; border: 1px solid #374151; border-radius: 3px;"
                self.btn_set_sel_complete.setStyleSheet(disabled_style)
                self.btn_set_sel_key.setStyleSheet(disabled_style)
                self.btn_toggle_sel_status.setStyleSheet(disabled_style)
                self.btn_clear_selection.setStyleSheet(disabled_style)

    def _set_selected_point_complete_to_current(self, t: Optional[float] = None):
        if self.selected_point_index is None or not (0 <= self.selected_point_index < len(self.session.points)):
            return
        if t is None:
            t = self.container1.mpv_widget.get_time()
            if t is None:
                t = getattr(self.timeline_widget, 'current_time', 0.0)
        pt = self.session.points[self.selected_point_index]
        pt.time_complete = t

        # Falls Punkte zeitlich aus der Reihenfolge geraten sind, sortieren
        if len(self.session.points) > 1:
            self.session.points.sort(key=lambda p: p.time_complete)
            for i, p in enumerate(self.session.points):
                p.point_num = i + 1
            self.selected_point_index = self.session.points.index(pt)
            self.points_table.selectRow(self.selected_point_index)

        self._update_table_and_stats()
        self._update_selection_controls()
        self.lbl_pending_event.setText(f"⏱️ Punkt #{pt.point_num} ({pt.formation}) Fertig-Zeit auf {format_seconds(t)} gesetzt")
        self.lbl_pending_event.setStyleSheet("color: #38bdf8; font-weight: bold;")

    def _set_selected_point_key_to_current(self, t: Optional[float] = None):
        if self.selected_point_index is None or not (0 <= self.selected_point_index < len(self.session.points)):
            return
        if t is None:
            t = self.container1.mpv_widget.get_time()
            if t is None:
                t = getattr(self.timeline_widget, 'current_time', 0.0)
        pt = self.session.points[self.selected_point_index]
        pt.time_key = t
        hold = pt.hold_time()
        hold_str = f" (Hold: {hold:.2f}s)" if hold is not None else ""
        self._update_table_and_stats()
        self._update_selection_controls()
        self.lbl_pending_event.setText(f"🔑 Punkt #{pt.point_num} ({pt.formation}) Key-Zeit auf {format_seconds(t)}{hold_str} gesetzt")
        self.lbl_pending_event.setStyleSheet("color: #f59e0b; font-weight: bold;")

    def _clear_selected_point_key(self):
        if self.selected_point_index is None or not (0 <= self.selected_point_index < len(self.session.points)):
            return
        pt = self.session.points[self.selected_point_index]
        pt.time_key = None
        self._update_table_and_stats()
        self._update_selection_controls()
        self.lbl_pending_event.setText(f"Key-Zeit für Punkt #{pt.point_num} entfernt")
        self.lbl_pending_event.setStyleSheet("color: #a1a1aa;")

    def _set_selected_point_status(self, status: str):
        if self.selected_point_index is None or not (0 <= self.selected_point_index < len(self.session.points)):
            return
        pt = self.session.points[self.selected_point_index]
        pt.status = status
        self._update_table_and_stats()
        self._update_selection_controls()
        self.lbl_pending_event.setText(f"Punkt #{pt.point_num} ({pt.formation}) Status auf {status} geändert")
        self.lbl_pending_event.setStyleSheet("color: #22c55e;" if status == "APPROVED" else "color: #ef4444;")

    def _toggle_selected_point_status(self):
        if self.selected_point_index is None or not (0 <= self.selected_point_index < len(self.session.points)):
            return
        pt = self.session.points[self.selected_point_index]
        new_status = "BUST" if pt.status == "APPROVED" else "APPROVED"
        self._set_selected_point_status(new_status)

    def _clear_point_selection(self):
        self.selected_point_index = None
        self.points_table.clearSelection()
        self.timeline_widget.set_points(self.session.points, selected_idx=None)
        self._update_selection_controls()
        self.lbl_pending_event.setText("Auswahl aufgehoben &ndash; Bereit für Wertung")
        self.lbl_pending_event.setStyleSheet("color: #a1a1aa; font-size: 11px;")

    def _show_table_context_menu(self, pos: QPoint):
        item = self.points_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        if not (0 <= row < len(self.session.points)):
            return

        self.selected_point_index = row
        self.points_table.selectRow(row)
        self._update_selection_controls()
        pt = self.session.points[row]

        cur_t = self.container1.mpv_widget.get_time()
        if cur_t is None:
            cur_t = getattr(self.timeline_widget, 'current_time', 0.0)

        menu = QMenu(self)
        menu.addSection(f"Punkt #{pt.point_num} ({pt.formation})")

        act_f = menu.addAction(f"⏱️ Fertig-Zeit = aktuelle Videoposition ({format_seconds(cur_t)}) [F]")
        act_f.triggered.connect(lambda: self._set_selected_point_complete_to_current(cur_t))

        act_k = menu.addAction(f"🔑 Key-Zeit = aktuelle Videoposition ({format_seconds(cur_t)}) [K]")
        act_k.triggered.connect(lambda: self._set_selected_point_key_to_current(cur_t))

        if pt.time_key is not None:
            act_k_clear = menu.addAction("🗑️ Key-Zeit entfernen")
            act_k_clear.triggered.connect(self._clear_selected_point_key)

        menu.addSeparator()
        if pt.status == "APPROVED":
            act_st = menu.addAction("❌ Als BUST (0) werten [B]")
            act_st.triggered.connect(lambda: self._set_selected_point_status("BUST"))
        else:
            act_st = menu.addAction("✅ Als SCORE (+1) werten [S]")
            act_st.triggered.connect(lambda: self._set_selected_point_status("APPROVED"))

        act_seek = menu.addAction(f"▶ Zum Punkt im Video springen ({format_seconds(pt.time_complete)})")
        act_seek.triggered.connect(lambda: self._seek_to_time(pt.time_complete))

        act_card = menu.addAction(f"🖼️ Rhythm XP Bildkarte für {pt.formation} anzeigen")
        act_card.triggered.connect(lambda: self._show_single_card_dialog(pt.formation))

        menu.addSeparator()
        act_del = menu.addAction("🗑️ Diesen Punkt löschen [Entf]")
        act_del.triggered.connect(self._delete_selected_point)

        menu.exec(self.points_table.viewport().mapToGlobal(pos))

    def _on_table_cell_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.session.points):
            pt = self.session.points[row]
            if col == 2:  # Status column: toggle on double click
                new_status = "BUST" if pt.status == "APPROVED" else "APPROVED"
                pt.status = new_status
                self._update_table_and_stats()
                self._update_selection_controls()

    def _mark_formation_complete(self):
        t = self.container1.mpv_widget.get_time()
        if t is None:
            t = getattr(self.timeline_widget, 'current_time', 0.0)

        # Wenn ein Punkt ausgewählt ist: Fertig-Zeit des ausgewählten Punkts aktualisieren!
        if self.selected_point_index is not None and 0 <= self.selected_point_index < len(self.session.points):
            self._set_selected_point_complete_to_current(t)
            return

        self.pending_complete_time = t
        diff_exit = (t - self.session.exit_time) if self.session.exit_time is not None else None
        exit_str = f" (+{diff_exit:.2f}s nach Exit)" if diff_exit is not None else ""
        self.lbl_pending_event.setText(f"🏁 Formation Fertig markiert bei {format_seconds(t)}{exit_str}")
        self.lbl_pending_event.setStyleSheet("color: #38bdf8; font-weight: bold;")

    def _mark_key_given(self):
        t = self.container1.mpv_widget.get_time()
        if t is None:
            t = getattr(self.timeline_widget, 'current_time', 0.0)

        # Wenn ein Punkt ausgewählt ist: Key-Zeit des ausgewählten Punkts aktualisieren!
        if self.selected_point_index is not None and 0 <= self.selected_point_index < len(self.session.points):
            self._set_selected_point_key_to_current(t)
            return

        self.pending_key_time = t
        hold_str = ""
        if self.pending_complete_time is not None:
            hold = t - self.pending_complete_time
            hold_str = f" (Hold: {hold:.2f}s)"
        elif self.session.points:
            # Falls Key nach dem Werten gedrückt wurde: letztem Punkt zuweisen!
            last_pt = self.session.points[-1]
            if last_pt.time_key is None:
                last_pt.time_key = t
                self._update_table_and_stats()
                self._update_selection_controls()
                self.lbl_pending_event.setText(f"🔑 Key zu Punkt #{last_pt.point_num} hinzugefügt ({format_seconds(t)})")
                self.lbl_pending_event.setStyleSheet("color: #f59e0b; font-weight: bold;")
                return

        self.lbl_pending_event.setText(f"🔑 Key markiert bei {format_seconds(t)}{hold_str}")
        self.lbl_pending_event.setStyleSheet("color: #f59e0b; font-weight: bold;")

    def _judge_point(self, status: str):
        # Wenn ein Punkt ausgewählt ist: Status des ausgewählten Punkts umschalten/setzen!
        if self.selected_point_index is not None and 0 <= self.selected_point_index < len(self.session.points):
            self._set_selected_point_status(status)
            return

        cur_t = self.container1.mpv_widget.get_time()
        if cur_t is None:
            cur_t = getattr(self.timeline_widget, 'current_time', 0.0)

        comp_time = self.pending_complete_time if self.pending_complete_time is not None else cur_t
        key_time = self.pending_key_time

        point_num = len(self.session.points) + 1
        formation = self._get_next_expected_formation()

        new_point = ScoringPoint(
            point_num=point_num,
            formation=formation,
            status=status,
            time_complete=comp_time,
            time_key=key_time
        )
        self.session.points.append(new_point)

        # Chronologisch sortieren, falls Zeit vor dem vorherigen Punkt lag
        if len(self.session.points) > 1 and new_point.time_complete < self.session.points[-2].time_complete:
            self.session.points.sort(key=lambda p: p.time_complete)
            for i, p in enumerate(self.session.points):
                p.point_num = i + 1

        # Reset pending events
        self.pending_complete_time = None
        self.pending_key_time = None
        self.lbl_pending_event.setText(f"Punkt #{new_point.point_num} ({new_point.formation}) als {status} gewertet")
        self.lbl_pending_event.setStyleSheet("color: #22c55e;" if status == "APPROVED" else "color: #ef4444;")

        self._update_sequence_chips()
        self._update_next_formation_indicator()
        self._update_table_and_stats()
        self._update_selection_controls()

    # -----------------------------------------------------------------
    # Table & Statistics Update
    # -----------------------------------------------------------------
    def _update_table_and_stats(self):
        self.points_table.blockSignals(True)
        self.points_table.setRowCount(len(self.session.points))

        for i, pt in enumerate(self.session.points):
            pt.point_num = i + 1  # Durchnummerierung absichern

            # # Spalte
            item_num = QTableWidgetItem(str(pt.point_num))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.points_table.setItem(i, 0, item_num)

            # Formation
            item_form = QTableWidgetItem(pt.formation)
            item_form.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            base = re.sub(r'[-._].*$', '', pt.formation)
            if base in FAI_BLOCKS:
                m = re.search(r'[-._]([12])$', pt.formation)
                part = int(m.group(1)) if m else 1
                n1, n2 = get_block_names(base)
                f_name = n1 if part == 1 else n2
                item_form.setToolTip(f"Block {base} (Teil {part}/2): {f_name}\nDoppelklick zum Ändern")
            elif base in FAI_RANDOMS:
                item_form.setToolTip(f"Random {base}: {FAI_RANDOMS[base]}\nDoppelklick zum Ändern")
            self.points_table.setItem(i, 1, item_form)

            # Status
            is_approved = (pt.status == "APPROVED")
            in_wt = pt.is_in_working_time(self.session.exit_time, self.session.working_time_duration)
            if not in_wt and self.session.exit_time is not None:
                status_text = "✓ SCORE (Out of WT)" if is_approved else "✗ BUST (Out of WT)"
                item_status = QTableWidgetItem(status_text)
                item_status.setForeground(QColor(234, 179, 8))
                item_status.setToolTip("Dieser Punkt wurde nach Ablauf der Working Time gewertet!\nDoppelklick zum Umschalten")
            else:
                status_text = "✓ SCORE (+1)" if is_approved else "✗ BUST (0)"
                item_status = QTableWidgetItem(status_text)
                item_status.setForeground(QColor(34, 197, 94) if is_approved else QColor(239, 68, 68))
                item_status.setToolTip("Doppelklick zum Umschalten zwischen SCORE und BUST")
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.points_table.setItem(i, 2, item_status)

            # Fertig Zeit
            wt_offset = (pt.time_complete - self.session.exit_time) if self.session.exit_time is not None else None
            comp_tip = f"Videozeit: {format_seconds(pt.time_complete)}"
            if wt_offset is not None:
                comp_tip += f"\nArbeitszeit: +{wt_offset:.2f}s nach Exit"
            item_comp = QTableWidgetItem(format_seconds(pt.time_complete))
            item_comp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_comp.setToolTip(f"{comp_tip}\nDoppelklick zum Bearbeiten der Zeit")
            self.points_table.setItem(i, 3, item_comp)

            # Key Zeit
            key_str = format_seconds(pt.time_key) if pt.time_key is not None else "-"
            item_key = QTableWidgetItem(key_str)
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if pt.time_key is not None and self.session.exit_time is not None:
                key_wt = pt.time_key - self.session.exit_time
                item_key.setToolTip(f"Videozeit: {format_seconds(pt.time_key)}\nArbeitszeit: +{key_wt:.2f}s nach Exit\nDoppelklick zum Bearbeiten")
            else:
                item_key.setToolTip("Doppelklick zum Eingeben der Key-Zeit")
            self.points_table.setItem(i, 4, item_key)

            # Hold Time
            hold = pt.hold_time()
            if hold is not None:
                if hold < 0:
                    hold_str = f"⚠️ {hold:.2f}s"
                    item_hold = QTableWidgetItem(hold_str)
                    item_hold.setForeground(QColor(239, 68, 68))
                    item_hold.setToolTip(f"Achtung: Key ({format_seconds(pt.time_key)}) liegt VOR Fertig-Zeit ({format_seconds(pt.time_complete)})!")
                else:
                    hold_str = f"{hold:.2f}s"
                    item_hold = QTableWidgetItem(hold_str)
                    item_hold.setForeground(QColor(251, 191, 36))
                    item_hold.setToolTip(f"Haltezeit: {hold:.2f}s (von Griffschluss bis Key)")
            else:
                item_hold = QTableWidgetItem("-")
                item_hold.setToolTip("Keine Key-Zeit gesetzt (Taste 'K' drücken)")
            item_hold.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.points_table.setItem(i, 5, item_hold)

            # Transition Time
            prev = self.session.points[i - 1] if i > 0 else None
            trans = pt.transition_time(prev, self.session.exit_time)
            if trans is not None:
                if trans < 0:
                    trans_str = f"⚠️ {trans:.2f}s"
                    item_trans = QTableWidgetItem(trans_str)
                    item_trans.setForeground(QColor(239, 68, 68))
                    item_trans.setToolTip("Achtung: Fertig-Zeit liegt vor dem vorherigen Key/Exit!")
                else:
                    trans_str = f"{trans:.2f}s"
                    item_trans = QTableWidgetItem(trans_str)
                    item_trans.setForeground(QColor(56, 189, 248))
                    if i == 0:
                        item_trans.setToolTip(f"Übergangszeit vom Exit ({format_seconds(self.session.exit_time)}) bis Punkt #1")
                    else:
                        ref_txt = f"Key #{prev.point_num}" if prev.time_key is not None else f"Fertig #{prev.point_num}"
                        item_trans.setToolTip(f"Übergangszeit von {ref_txt} bis Griffschluss #{pt.point_num}")
            else:
                item_trans = QTableWidgetItem("-")
                if i == 0:
                    item_trans.setToolTip("Exit-Zeitpunkt nicht gesetzt (Taste 'T' drücken)")
                else:
                    item_trans.setToolTip("Vorheriger Referenzzeitpunkt fehlt")
            item_trans.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.points_table.setItem(i, 6, item_trans)

            # Notiz
            item_notes = QTableWidgetItem(pt.notes)
            item_notes.setToolTip("Doppelklick zum Bearbeiten der Debrief-Notiz")
            self.points_table.setItem(i, 7, item_notes)

        self.points_table.blockSignals(False)

        # Timeline aktualisieren
        self.timeline_widget.set_points(self.session.points, selected_idx=self.selected_point_index)

        # Scoreboard aktualisieren
        score = self.session.total_score()
        score_wt = self.session.points_in_working_time()
        busts = self.session.total_busts()
        total = len(self.session.points)

        score_text = f"PUNKTE: {score}"
        if score != score_wt and self.session.exit_time is not None:
            score_text += f" ({score_wt} in WT)"

        self.lbl_score_display.setText(score_text)
        self.lbl_bust_display.setText(f"BUSTS: {busts}")
        self.lbl_total_attempted.setText(f"GESAMT: {total}")

        # Debriefing Statistik Kennzahlen
        avg_hold = self.session.average_hold_time()
        avg_trans = self.session.average_transition_time()

        hold_disp = f"{avg_hold:.2f} s" if avg_hold is not None else "-- s"
        trans_disp = f"{avg_trans:.2f} s" if avg_trans is not None else "-- s"

        pace_str = "-- s/pt"
        if total > 0 and self.session.exit_time is not None:
            last_t = self.session.points[-1].time_complete
            total_time = max(0.1, last_t - self.session.exit_time)
            pace = total_time / total
            pace_str = f"{pace:.2f} s/pt"

        self.lbl_stat_hold.setText(f"Avg Hold: <b>{hold_disp}</b>")
        self.lbl_stat_trans.setText(f"Avg Trans: <b>{trans_disp}</b>")
        self.lbl_stat_pace.setText(f"Pace: <b>{pace_str}</b>")

    def _on_table_row_clicked(self, item: QTableWidgetItem):
        row = item.row()
        if 0 <= row < len(self.session.points):
            self.selected_point_index = row
            pt = self.session.points[row]
            self.timeline_widget.set_points(self.session.points, selected_idx=row)
            self._seek_to_time(pt.time_complete)
            self._update_selection_controls()

    def _on_table_current_changed(self, current_row: int, current_col: int, prev_row: int, prev_col: int):
        if self.points_table.signalsBlocked():
            return
        if 0 <= current_row < len(self.session.points):
            self.selected_point_index = current_row
            pt = self.session.points[current_row]
            self.timeline_widget.set_points(self.session.points, selected_idx=current_row)
            self._seek_to_time(pt.time_complete)
            self._update_selection_controls()

    def _on_table_item_changed(self, item: QTableWidgetItem):
        if self.points_table.signalsBlocked():
            return
        row = item.row()
        col = item.column()
        if not (0 <= row < len(self.session.points)):
            return

        pt = self.session.points[row]
        if col == 1:  # Formation geändert
            val = item.text().strip().upper()
            if val:
                pt.formation = val
                self._update_sequence_chips()
                self._update_next_formation_indicator()
                self._update_table_and_stats()
                self._update_selection_controls()
        elif col == 2:  # Status geändert
            val = item.text().strip().upper()
            if "BUST" in val or "0" in val or "✗" in val:
                pt.status = "BUST"
            else:
                pt.status = "APPROVED"
            self._update_table_and_stats()
            self._update_selection_controls()
        elif col == 3:  # Fertig-Zeit geändert
            parsed = parse_time_string(item.text())
            if parsed is not None:
                pt.time_complete = parsed
                if len(self.session.points) > 1:
                    self.session.points.sort(key=lambda p: p.time_complete)
                    for i, p in enumerate(self.session.points):
                        p.point_num = i + 1
                    self.selected_point_index = self.session.points.index(pt)
                self._update_table_and_stats()
                self._update_selection_controls()
            else:
                self._update_table_and_stats()
        elif col == 4:  # Key-Zeit geändert
            parsed = parse_time_string(item.text())
            pt.time_key = parsed
            self._update_table_and_stats()
            self._update_selection_controls()
        elif col == 7:  # Notiz geändert
            pt.notes = item.text()

    def _on_timeline_point_clicked(self, idx: int):
        if 0 <= idx < len(self.session.points):
            self.selected_point_index = idx
            self.points_table.selectRow(idx)
            self._update_selection_controls()

    def _delete_selected_point(self):
        row = self.points_table.currentRow()
        if not (0 <= row < len(self.session.points)):
            row = self.selected_point_index if self.selected_point_index is not None else -1
        if 0 <= row < len(self.session.points):
            del self.session.points[row]
            for i, p in enumerate(self.session.points):
                p.point_num = i + 1
            self.selected_point_index = None
            self._update_sequence_chips()
            self._update_next_formation_indicator()
            self._update_table_and_stats()
            self._update_selection_controls()

    def _clear_all_points(self):
        if not self.session.points:
            return
        reply = QMessageBox.question(
            self, "Alle Punkte löschen?",
            "Möchtest du wirklich alle gewerteten Punkte für diesen Sprung löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.session.points.clear()
            self.selected_point_index = None
            self._update_sequence_chips()
            self._update_next_formation_indicator()
            self._update_table_and_stats()
            self._update_selection_controls()

    # -----------------------------------------------------------------
    # Session Persistence & Debrief Report Export
    # -----------------------------------------------------------------
    def _get_debriefs_dir(self) -> str:
        """Liefert den Pfad zum debriefs/-Ordner, falls vorhanden."""
        curr = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(curr)
        candidate = os.path.join(root, "debriefs")
        if os.path.isdir(candidate):
            return candidate
        candidate_curr = os.path.join(curr, "debriefs")
        if os.path.isdir(candidate_curr):
            return candidate_curr
        return ""

    def _save_session_file(self):
        default_name = f"{self.session.jump_name.replace(' ', '_')}_debrief.json"
        deb_dir = self._get_debriefs_dir()
        init_path = os.path.join(deb_dir, default_name) if deb_dir else default_name
        path, _ = QFileDialog.getSaveFileName(self, "Debriefing Session speichern", init_path, "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.session.to_dict(), f, indent=2, ensure_ascii=False)
                try:
                    from training_db import TrainingDatabase
                    TrainingDatabase().record_session(self.session.to_dict(), file_path=path)
                except Exception:
                    pass
                QMessageBox.information(self, "Gespeichert", f"Session gespeichert:\n{os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Konnte Datei nicht speichern:\n{e}")

    def _load_session_file(self):
        deb_dir = self._get_debriefs_dir()
        path, _ = QFileDialog.getOpenFileName(self, "Debriefing Session laden", deb_dir, "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.session = JumpSession.from_dict(data)
                try:
                    from training_db import TrainingDatabase
                    TrainingDatabase().record_session(self.session.to_dict(), file_path=path)
                except Exception:
                    pass

                self.edit_jump_name.setText(self.session.jump_name)
                self.edit_draw.setText(self.session.draw_string)
                self._update_in_out_labels()
                self.timeline_widget.set_in_out(self.session.in_point, self.session.out_point)
                self.timeline_widget.set_working_time(self.session.exit_time, self.session.working_time_duration)

                if self.session.video_path and os.path.exists(self.session.video_path):
                    self.container1.mpv_widget.load_video(self.session.video_path)
                    fname1 = os.path.basename(self.session.video_path)
                    if hasattr(self, 'btn_load_raw'):
                        self.btn_load_raw.setText(f"📹 Cam 1: {fname1[:12]}...")
                    if hasattr(self, 'lbl_cam1_title'):
                        self.lbl_cam1_title.setText(f"📹 <b>Cam 1:</b> {fname1}")

                if self.session.video_path_cam2 and os.path.exists(self.session.video_path_cam2):
                    self.btn_toggle_dual.setChecked(True)
                    self.container2.mpv_widget.load_video(self.session.video_path_cam2)
                    fname2 = os.path.basename(self.session.video_path_cam2)
                    if hasattr(self, 'btn_load_cam2'):
                        self.btn_load_cam2.setText(f"📹 Cam 2: {fname2[:12]}...")
                    if hasattr(self, 'lbl_cam2_title'):
                        self.lbl_cam2_title.setText(f"📹 <b>Cam 2:</b> {fname2}")

                self._update_sequence_chips()
                self._update_next_formation_indicator()
                self._update_table_and_stats()
                QMessageBox.information(self, "Geladen", f"Session erfolgreich geladen:\n{os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Konnte Session nicht laden:\n{e}")

    def _export_debrief_report(self):
        score = self.session.total_score()
        busts = self.session.total_busts()
        total = len(self.session.points)
        avg_hold = self.session.average_hold_time()
        avg_trans = self.session.average_transition_time()

        report_lines = [
            f"# 4-Way Debriefing Report: {self.session.jump_name}",
            f"- **Draw / Sequenz:** {self.session.draw_string}",
            f"- **Video:** {os.path.basename(self.session.video_path) if self.session.video_path else 'Kein Video'}",
            f"- **Working Time:** {int(self.session.working_time_duration)}s | Exit: {format_seconds(self.session.exit_time)}",
            "",
            "## 🏆 Ergebnis",
            f"- **Punkte gewertet (Score):** {score}",
            f"- **Busts (Fehler):** {busts}",
            f"- **Punkte gesamt versucht:** {total}",
            f"- **Durchschnittliche Haltezeit (Hold):** {avg_hold:.2f}s" if avg_hold is not None else "- **Hold:** -",
            f"- **Durchschnittliche Übergangszeit (Transition):** {avg_trans:.2f}s" if avg_trans is not None else "- **Transition:** -",
            "",
            "## 📋 Punkte & Zeiten Aufschlüsselung",
            "| # | Formation | Status | Fertig | Key | Hold | Trans | Notizen |",
            "|---|---|---|---|---|---|---|---|"
        ]

        for i, pt in enumerate(self.session.points):
            prev = self.session.points[i - 1] if i > 0 else None
            h_str = f"{pt.hold_time():.2f}s" if pt.hold_time() is not None else "-"
            t_str = f"{pt.transition_time(prev, self.session.exit_time):.2f}s" if pt.transition_time(prev, self.session.exit_time) is not None else "-"
            k_str = format_seconds(pt.time_key) if pt.time_key is not None else "-"
            report_lines.append(
                f"| {pt.point_num} | {pt.formation} | {pt.status} | {format_seconds(pt.time_complete)} | {k_str} | {h_str} | {t_str} | {pt.notes} |"
            )

        report_text = "\n".join(report_lines)

        # Dialog zur Anzeige & Kopieren
        dlg = QDialog(self)
        dlg.setWindowTitle("📊 Debriefing Report")
        dlg.resize(750, 500)
        d_layout = QVBoxLayout(dlg)

        txt = QTextEdit(dlg)
        txt.setReadOnly(True)
        txt.setPlainText(report_text)
        d_layout.addWidget(txt)

        btn_box = QHBoxLayout()
        btn_copy = QPushButton("📋 In Zwischenablage kopieren")
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(report_text))

        btn_save_txt = QPushButton("💾 Als Datei speichern (.md)...")
        btn_save_txt.clicked.connect(lambda: self._save_report_to_file(report_text))

        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(dlg.accept)

        btn_box.addWidget(btn_copy)
        btn_box.addWidget(btn_save_txt)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        d_layout.addLayout(btn_box)

        dlg.exec()

    def _save_report_to_file(self, text: str):
        default_name = f"{self.session.jump_name}_report.md"
        deb_dir = self._get_debriefs_dir()
        init_path = os.path.join(deb_dir, default_name) if deb_dir else default_name
        path, _ = QFileDialog.getSaveFileName(self, "Report speichern", init_path, "Markdown (*.md);;Text (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                QMessageBox.information(self, "Gespeichert", f"Report gespeichert:\n{os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Konnte Report nicht speichern:\n{e}")

    def closeEvent(self, event):
        if hasattr(self, 'shortcut_filter'):
            app = QApplication.instance()
            if app:
                try:
                    app.removeEventFilter(self.shortcut_filter)
                except Exception:
                    pass
        if hasattr(self, 'ui_timer'):
            self.ui_timer.stop()
        if hasattr(self, 'container1'):
            self.container1.close()
        if hasattr(self, 'container2'):
            self.container2.close()
        super().closeEvent(event)


# =====================================================================
# Application Entry Point
# =====================================================================

def main():
    app = QApplication(sys.argv)
    try:
        locale.setlocale(locale.LC_NUMERIC, 'C')
    except Exception:
        pass
    window = DebriefMainWindow()
    window.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()