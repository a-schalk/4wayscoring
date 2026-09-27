#!/usr/bin/env python3
"""
FAI 4-Way Formation Skydiving 3D Visualizer & Technique Explorer
Interactive 3D tool featuring all 16 Randoms (A-Q) and 22 Blocks (1-22).
Provides 3D spatial visualization, slot-specific instructions (Point, OC, IC, Tail),
head switch gaze vectors, key responsibilities, and coach notes.
"""

import sys
import math
import os
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import (
    Qt, QPointF, QRectF, QTimer, pyqtSignal, QObject, QSize
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush, QPolygonF, QPainterPath,
    QLinearGradient, QRadialGradient, QAction, QIcon, QKeySequence
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QLineEdit, QListWidget,
    QListWidgetItem, QTabWidget, QTextBrowser, QSplitter, QFrame,
    QCheckBox, QRadioButton, QButtonGroup, QScrollArea, QToolBar,
    QMessageBox, QFileDialog, QSizePolicy
)

# Import comprehensive formation database
try:
    import formation_db
    from formation_db import (
        FormationDefinition, Flyer3DState, SlotDetail,
        DIVE_POOL, get_formation, get_all_formations,
        COLOR_POINT, COLOR_OC, COLOR_IC, COLOR_TAIL, COLOR_VIDEO
    )
except ImportError:
    # Fallback to local path if run from elsewhere
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import formation_db
    from formation_db import (
        FormationDefinition, Flyer3DState, SlotDetail,
        DIVE_POOL, get_formation, get_all_formations,
        COLOR_POINT, COLOR_OC, COLOR_IC, COLOR_TAIL, COLOR_VIDEO
    )


# =============================================================================
# 3D Math & Projection Utilities
# =============================================================================

def project_3d_point(
    x: float, y: float, z: float,
    yaw: float, pitch: float, zoom: float,
    pan_x: float, pan_y: float,
    cx: float, cy: float, fov: float = 650.0
) -> Tuple[float, float, float]:
    """Projects 3D world coordinate (inches) into screen 2D space."""
    # Rotate around World Z (Yaw)
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    x1 = x * cos_y - y * sin_y
    y1 = x * sin_y + y * cos_y
    z1 = z

    # Rotate around Camera X (Pitch)
    cos_p, sin_p = math.cos(pitch), math.sin(pitch)
    y2 = y1 * cos_p - z1 * sin_p
    z2 = y1 * sin_p + z1 * cos_p

    # Perspective projection
    cam_dist = 850.0 / zoom + z2
    if cam_dist < 40.0:
        cam_dist = 40.0
    scale = fov / cam_dist

    sx = cx + (x1 + pan_x) * scale
    sy = cy - (y2 + pan_y) * scale
    return sx, sy, z2


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def lerp_angle_deg(a: float, b: float, t: float) -> float:
    """Interpolates angles along the shortest circular arc."""
    diff = (b - a + 180.0) % 360.0 - 180.0
    return (a + diff * t) % 360.0


def interpolate_flyer_states(
    s1: Flyer3DState, s2: Flyer3DState, t: float
) -> Flyer3DState:
    """Smoothly blends two flyer 3D states."""
    x = lerp(s1.x, s2.x, t)
    y = lerp(s1.y, s2.y, t)
    z = lerp(s1.z, s2.z, t)
    heading = lerp_angle_deg(s1.heading_deg, s2.heading_deg, t)
    head_turn = lerp(s1.head_turn_deg, s2.head_turn_deg, t)
    
    # Head switch is active if either state has it active or midway
    hs_active = (s1.head_switch_active if t < 0.5 else s2.head_switch_active)
    hs_desc = s2.head_switch_desc if t >= 0.5 else s1.head_switch_desc
    gaze_tgt = s2.gaze_target if t >= 0.5 else s1.gaze_target
    
    return Flyer3DState(
        x=x, y=y, z=z, heading_deg=heading, head_turn_deg=head_turn,
        head_switch_active=hs_active, head_switch_desc=hs_desc, gaze_target=gaze_tgt,
        left_grip=s2.left_grip if t >= 0.8 else (s1.left_grip if t <= 0.2 else None),
        right_grip=s2.right_grip if t >= 0.8 else (s1.right_grip if t <= 0.2 else None),
        grippers_presented=s2.grippers_presented if t >= 0.5 else s1.grippers_presented
    )


# =============================================================================
# Interactive 3D Viewport Widget
# =============================================================================

class Formation3DWidget(QWidget):
    """
    High-performance 3D vector graphics canvas rendering 4-way formations.
    Supports 3D orbiting, zoom, pan, animation, gaze vectors, grip links,
    and interactive flyer selection.
    """
    flyer_clicked = pyqtSignal(str)  # Emits slot name ("Point", "OC", "IC", "Tail")
    phase_changed = pyqtSignal(float) # Emits current phase (0.0 to 2.0)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(450, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Camera parameters
        self.yaw: float = 0.0          # Horizontal orbit angle in radians
        self.pitch: float = 0.85       # Vertical pitch angle (0 = side, ~1.57 = top down)
        self.zoom: float = 1.05        # Camera zoom factor
        self.pan_x: float = 0.0        # Camera pan X offset
        self.pan_y: float = 0.0        # Camera pan Y offset

        # Interaction state
        self.last_mouse_pos: Optional[QPointF] = None
        self.mouse_button_down: Optional[Qt.MouseButton] = None
        self.selected_slot: Optional[str] = None
        self.hovered_slot: Optional[str] = None

        # Data & Animation
        self.current_formation: Optional[FormationDefinition] = None
        self.use_vertical_technique: bool = False
        self.current_phase: float = 0.0  # 0.0 = Initial, 1.0 = Inter, 2.0 = Close
        self.target_phase: float = 0.0
        self.is_animating: bool = False
        self.anim_speed: float = 1.0
        self.anim_direction: float = 1.0

        # View Toggles
        self.show_gaze_rays: bool = True
        self.show_grip_links: bool = True
        self.show_point_tail_axis: bool = True
        self.show_compass_grid: bool = True
        self.show_slot_labels: bool = True
        self.show_key_badge: bool = True

        # Animation Timer (60 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(16)
        self.anim_timer.timeout.connect(self._on_anim_step)

        # Pulsing effect for Keys and Head Switches
        self.pulse_phase: float = 0.0

    def set_formation(self, formation: FormationDefinition):
        """Sets active formation and resets phase."""
        self.current_formation = formation
        self.current_phase = 0.0
        self.target_phase = 0.0
        self.is_animating = False
        self.update()

    def set_phase(self, phase: float):
        """Sets block phase (0.0=Initial, 1.0=Inter, 2.0=Close)."""
        self.current_phase = max(0.0, min(2.0, phase))
        self.update()

    def set_vertical_technique(self, enable: bool):
        """Switches between Vertical and On-Level technique."""
        self.use_vertical_technique = enable
        self.update()

    def play_pause_animation(self):
        """Toggles animation playback."""
        if not self.current_formation or not self.current_formation.is_block:
            return
        if self.is_animating:
            self.anim_timer.stop()
            self.is_animating = False
        else:
            self.is_animating = True
            self.anim_timer.start()

    def reset_camera(self, top_down: bool = False):
        """Resets camera view to standard top-down or 3D perspective."""
        if top_down:
            self.yaw = 0.0
            self.pitch = 1.55  # Near 90° straight down
            self.zoom = 1.05
        else:
            self.yaw = 0.25
            self.pitch = 0.75  # ~43° perspective
            self.zoom = 1.05
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def _on_anim_step(self):
        """Timer callback for smooth interpolation."""
        self.pulse_phase = (self.pulse_phase + 0.08) % (2.0 * math.pi)
        
        if not self.is_animating:
            self.update()
            return

        # Advance phase
        delta = 0.015 * self.anim_speed * self.anim_direction
        self.current_phase += delta

        # Loop or ping-pong between 0.0 and 2.0
        if self.current_phase >= 2.0:
            self.current_phase = 2.0
            self.anim_direction = -1.0  # Reverse
        elif self.current_phase <= 0.0:
            self.current_phase = 0.0
            self.anim_direction = 1.0   # Forward

        self.phase_changed.emit(self.current_phase)
        self.update()

    # -------------------------------------------------------------------------
    # Mouse & Gesture Events
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event):
        self.last_mouse_pos = event.position()
        self.mouse_button_down = event.button()

        # Check if a flyer was clicked in 2D projection
        clicked_slot = self._find_flyer_at_screen_pos(event.position().x(), event.position().y())
        if clicked_slot:
            self.selected_slot = clicked_slot
            self.flyer_clicked.emit(clicked_slot)
            self.update()

    def mouseMoveEvent(self, event):
        if not self.last_mouse_pos or not self.mouse_button_down:
            # Hover check
            hover = self._find_flyer_at_screen_pos(event.position().x(), event.position().y())
            if hover != self.hovered_slot:
                self.hovered_slot = hover
                self.update()
            return

        dx = event.position().x() - self.last_mouse_pos.x()
        dy = event.position().y() - self.last_mouse_pos.y()
        self.last_mouse_pos = event.position()

        if self.mouse_button_down == Qt.MouseButton.LeftButton:
            # Orbit Camera
            self.yaw += dx * 0.008
            self.pitch += dy * 0.008
            # Constrain pitch to avoid flipping over
            self.pitch = max(0.05, min(math.pi * 0.49, self.pitch))
            self.update()

        elif self.mouse_button_down == Qt.MouseButton.RightButton:
            # Zoom Camera
            self.zoom += dy * 0.005
            self.zoom = max(0.3, min(3.0, self.zoom))
            self.update()

        elif self.mouse_button_down == Qt.MouseButton.MiddleButton:
            # Pan Camera
            self.pan_x += dx * 0.5 / self.zoom
            self.pan_y -= dy * 0.5 / self.zoom
            self.update()

    def mouseReleaseEvent(self, event):
        self.mouse_button_down = None
        self.last_mouse_pos = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        self.zoom = max(0.3, min(3.0, self.zoom * zoom_factor))
        self.update()

    # -------------------------------------------------------------------------
    # Spatial Calculation & Flyer State Interpolation
    # -------------------------------------------------------------------------
    def _get_current_flyer_states(self) -> Dict[str, Flyer3DState]:
        """Calculates interpolated 3D states for all 4 flyers based on phase."""
        if not self.current_formation:
            return {}

        form = self.current_formation
        if not form.is_block or not form.state_inter or not form.state_close:
            return form.state_initial

        # Choose between Vertical and On-Level states
        s_inter = (form.state_inter_vertical if (self.use_vertical_technique and form.state_inter_vertical)
                   else form.state_inter)
        s_close = (form.state_close_vertical if (self.use_vertical_technique and form.state_close_vertical)
                   else form.state_close)

        states: Dict[str, Flyer3DState] = {}
        for slot in ["Point", "OC", "IC", "Tail"]:
            s0 = form.state_initial.get(slot)
            s1 = s_inter.get(slot)
            s2 = s_close.get(slot)

            if not s0 or not s1 or not s2:
                continue

            if self.current_phase <= 1.0:
                # Interpolate between Initial (0.0) and Inter (1.0)
                t = self.current_phase
                states[slot] = interpolate_flyer_states(s0, s1, t)
            else:
                # Interpolate between Inter (1.0) and Close (2.0)
                t = self.current_phase - 1.0
                states[slot] = interpolate_flyer_states(s1, s2, t)

        return states

    def _find_flyer_at_screen_pos(self, sx: float, sy: float) -> Optional[str]:
        """Returns slot name if click/hover is within bounding radius of flyer."""
        states = self._get_current_flyer_states()
        cx = self.width() / 2.0
        cy = self.height() / 2.0

        for slot, state in states.items():
            px, py, _ = project_3d_point(
                state.x, state.y, state.z,
                self.yaw, self.pitch, self.zoom,
                self.pan_x, self.pan_y, cx, cy
            )
            dist = math.hypot(sx - px, sy - py)
            if dist < 35.0:  # 35 px radius
                return slot
        return None

    # -------------------------------------------------------------------------
    # 3D Painting & Rendering Engine
    # -------------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # 1. Background Sky Atmosphere Gradient
        bg_grad = QLinearGradient(0, 0, 0, h)
        bg_grad.setColorAt(0.0, QColor("#091428"))  # Deep stratosphere blue
        bg_grad.setColorAt(0.5, QColor("#0e2038"))  # Altitude navy
        bg_grad.setColorAt(1.0, QColor("#142a4a"))  # Horizon blue
        painter.fillRect(self.rect(), bg_grad)

        # 2. Render 3D Ground / Horizon Compass Plane
        if self.show_compass_grid:
            self._draw_compass_grid(painter, cx, cy)

        # Collect states
        states = self._get_current_flyer_states()
        if not states:
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Keine Formation ausgewählt")
            return

        # 3. Magic Point-Tail Axis Line
        if self.show_point_tail_axis and "Point" in states and "Tail" in states:
            self._draw_point_tail_axis(painter, states["Point"], states["Tail"], cx, cy)

        # 4. Grip Connection Vectors
        if self.show_grip_links:
            self._draw_grip_links(painter, states, cx, cy)

        # 5. Draw Shadows on Horizontal Base Plane (Z=0)
        self._draw_flyer_shadows(painter, states, cx, cy)

        # 6. Sort 3D Flyers by Depth (Painter's Algorithm)
        sorted_flyers = []
        for slot, state in states.items():
            px, py, depth = project_3d_point(
                state.x, state.y, state.z,
                self.yaw, self.pitch, self.zoom,
                self.pan_x, self.pan_y, cx, cy
            )
            sorted_flyers.append((depth, slot, state, px, py))
        
        # Draw from furthest (largest depth) to closest (smallest depth)
        sorted_flyers.sort(key=lambda item: item[0], reverse=True)

        # 7. Draw 3D Flyers (Body, Rig, Mantis Arms/Legs, Head, Gaze)
        for depth, slot, state, px, py in sorted_flyers:
            self._draw_skydiver_3d(painter, slot, state, px, py, cx, cy)

        # 8. Viewport Overlay HUD (Phase indicator, Key indicator, Slot Badges)
        self._draw_viewport_hud(painter)

    def _draw_compass_grid(self, painter: QPainter, cx: float, cy: float):
        """Draws a 3D circular compass plane with quadrants and degree marks."""
        painter.save()
        radius = 110.0  # inches

        # Draw concentric range circles
        for r in [40.0, 75.0, 110.0]:
            poly = QPolygonF()
            segments = 48
            for i in range(segments):
                ang = 2.0 * math.pi * i / segments
                gx = r * math.cos(ang)
                gy = r * math.sin(ang)
                sx, sy, _ = project_3d_point(gx, gy, -1.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
                poly.append(QPointF(sx, sy))

            pen = QPen(QColor(56, 189, 248, 40 if r < 110 else 70))
            pen.setStyle(Qt.PenStyle.DashLine if r < 110 else Qt.PenStyle.SolidLine)
            pen.setWidthF(1.2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(poly)

        # Draw Quadrant Crosshairs (X and Y axis)
        pen_axis = QPen(QColor(148, 163, 184, 50), 1.0, Qt.PenStyle.DashLine)
        painter.setPen(pen_axis)
        for (x1, y1), (x2, y2) in [((-radius, 0), (radius, 0)), ((0, -radius), (0, radius))]:
            sx1, sy1, _ = project_3d_point(x1, y1, -1.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            sx2, sy2, _ = project_3d_point(x2, y2, -1.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

        # Centerpoint Marker (0,0)
        cpx, cpy, _ = project_3d_point(0, 0, -1.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
        painter.setPen(QColor(56, 189, 248, 180))
        painter.setBrush(QColor(56, 189, 248, 120))
        painter.drawEllipse(QPointF(cpx, cpy), 3.5, 3.5)

        # Cardinal directions (North, South, East, West)
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor(148, 163, 184, 150))
        for label, (lx, ly) in [("N (Line of Flight)", (0, radius + 12)), ("S", (0, -radius - 12)), ("E", (radius + 12, 0)), ("W", (-radius - 12, 0))]:
            lsx, lsy, _ = project_3d_point(lx, ly, -1.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            painter.drawText(QRectF(lsx - 40, lsy - 10, 80, 20), Qt.AlignmentFlag.AlignCenter, label)

        painter.restore()

    def _draw_point_tail_axis(self, painter: QPainter, pt: Flyer3DState, tl: Flyer3DState, cx: float, cy: float):
        """Draws the famous Magic Point-Tail Axis Line in 3D."""
        painter.save()
        sx1, sy1, _ = project_3d_point(pt.x, pt.y, pt.z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
        sx2, sy2, _ = project_3d_point(tl.x, tl.y, tl.z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)

        pen = QPen(QColor(236, 72, 153, 160), 2.0, Qt.PenStyle.DashDotLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

        # Axis label
        mx = (sx1 + sx2) / 2.0
        my = (sy1 + sy2) / 2.0
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        painter.setPen(QColor(244, 114, 182, 200))
        painter.drawText(QRectF(mx - 60, my - 16, 120, 16), Qt.AlignmentFlag.AlignCenter, "Point-Tail Axis")
        painter.restore()

    def _draw_grip_links(self, painter: QPainter, states: Dict[str, Flyer3DState], cx: float, cy: float):
        """Renders glowing magnetic grip vectors between touching teammates."""
        if not self.current_formation:
            return

        painter.save()
        # Draw links based on proximity (< 38 inches)
        slots = list(states.keys())
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                s_a = states[slots[i]]
                s_b = states[slots[j]]
                dist = math.hypot(s_a.x - s_b.x, s_a.y - s_b.y)
                
                # Check vertical distance too
                v_dist = abs(s_a.z - s_b.z)
                if dist < 42.0 and v_dist < 15.0:
                    # Valid grip proximity
                    sx1, sy1, _ = project_3d_point(s_a.x, s_a.y, s_a.z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
                    sx2, sy2, _ = project_3d_point(s_b.x, s_b.y, s_b.z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)

                    # Glow effect
                    painter.setPen(QPen(QColor(56, 189, 248, 80), 5.0))
                    painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
                    # Core solid connection
                    painter.setPen(QPen(QColor(224, 242, 254, 220), 2.0))
                    painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

        painter.restore()

    def _draw_flyer_shadows(self, painter: QPainter, states: Dict[str, Flyer3DState], cx: float, cy: float):
        """Renders ground shadows to provide vertical level perception."""
        painter.save()
        painter.setBrush(QColor(0, 0, 0, 60))
        painter.setPen(Qt.PenStyle.NoPen)

        for slot, s in states.items():
            # Shadow projected onto plane Z=0
            px, py, _ = project_3d_point(s.x, s.y, -1.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            
            # Shadow scale shrinks if flyer is high
            shadow_radius = max(8.0, 22.0 - s.z * 0.4)
            painter.drawEllipse(QPointF(px, py), shadow_radius * 1.3, shadow_radius * 0.8)

            # If flyer has vertical offset (over/under), draw vertical tether line
            if abs(s.z) > 4.0:
                flyer_px, flyer_py, _ = project_3d_point(s.x, s.y, s.z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
                pen_tether = QPen(QColor(255, 255, 255, 60), 1.0, Qt.PenStyle.DotLine)
                painter.setPen(pen_tether)
                painter.drawLine(QPointF(px, py), QPointF(flyer_px, flyer_py))
                painter.setPen(Qt.PenStyle.NoPen)

        painter.restore()

    def _draw_skydiver_3d(
        self, painter: QPainter, slot: str, state: Flyer3DState,
        px: float, py: float, cx: float, cy: float
    ):
        """Renders an anatomically accurate 4-Way Mantis Skydiver in 3D perspective."""
        painter.save()

        # Slot Color Scheme
        color_map = {
            "Point": QColor(COLOR_POINT),
            "OC": QColor(COLOR_OC),
            "IC": QColor(COLOR_IC),
            "Tail": QColor(COLOR_TAIL)
        }
        base_color = color_map.get(slot, QColor("#ffffff"))

        # Highlight if hovered or selected
        is_selected = (slot == self.selected_slot)
        is_hovered = (slot == self.hovered_slot)

        # Body orientation vectors
        rad_body = math.radians(state.heading_deg)
        fx, fy = math.sin(rad_body), math.cos(rad_body)  # Forward direction
        rx, ry = math.cos(rad_body), -math.sin(rad_body) # Right direction

        # Dimensions (inches)
        torso_len = 16.0
        torso_wid = 9.0

        # ---------------------------------------------------------------------
        # A. Mantis Legs (Thighs spread outward + lower legs bent up)
        # ---------------------------------------------------------------------
        for side, sign in [("Left", -1.0), ("Right", 1.0)]:
            hip_x = state.x + rx * (torso_wid * 0.8 * sign) - fx * (torso_len * 0.8)
            hip_y = state.y + ry * (torso_wid * 0.8 * sign) - fy * (torso_len * 0.8)
            hip_z = state.z

            # Knee spread outward
            knee_x = hip_x + rx * (14.0 * sign) - fx * 12.0
            knee_y = hip_y + ry * (14.0 * sign) - fy * 12.0
            knee_z = state.z + 1.5

            # Ankle/Bootie bent up into airflow
            ankle_x = knee_x + rx * (4.0 * sign) - fx * 10.0
            ankle_y = knee_y + ry * (4.0 * sign) - fy * 10.0
            ankle_z = state.z + 5.0

            # Project leg points
            sh_x, sh_y, _ = project_3d_point(hip_x, hip_y, hip_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            sk_x, sk_y, _ = project_3d_point(knee_x, knee_y, knee_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            sa_x, sa_y, _ = project_3d_point(ankle_x, ankle_y, ankle_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)

            # Draw thigh
            pen_thigh = QPen(base_color.darker(110), 6.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_thigh)
            painter.drawLine(QPointF(sh_x, sh_y), QPointF(sk_x, sk_y))

            # Draw shin & Bootie (high drag bootie in dark gray/accent)
            pen_shin = QPen(base_color.lighter(115), 5.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_shin)
            painter.drawLine(QPointF(sk_x, sk_y), QPointF(sa_x, sa_y))

            # Bootie scoop fin
            painter.setPen(QPen(QColor("#1e293b"), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPoint(QPointF(sa_x, sa_y))

        # ---------------------------------------------------------------------
        # B. Mantis Arms (Elbows forward/down + hands in front of face)
        # ---------------------------------------------------------------------
        for side, sign in [("Left", -1.0), ("Right", 1.0)]:
            sh_x = state.x + rx * (torso_wid * sign) + fx * (torso_len * 0.4)
            sh_y = state.y + ry * (torso_wid * sign) + fy * (torso_len * 0.4)
            sh_z = state.z

            # Elbow forward and slightly outward (Mantis box)
            el_x = sh_x + rx * (9.0 * sign) + fx * 11.0
            el_y = sh_y + ry * (9.0 * sign) + fy * 11.0
            el_z = state.z - 2.0

            # Hand cupped in front
            hd_x = el_x - rx * (4.0 * sign) + fx * 9.0
            hd_y = el_y - ry * (4.0 * sign) + fy * 9.0
            hd_z = state.z

            ssh_x, ssh_y, _ = project_3d_point(sh_x, sh_y, sh_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            sel_x, sel_y, _ = project_3d_point(el_x, el_y, el_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            shd_x, shd_y, _ = project_3d_point(hd_x, hd_y, hd_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)

            # Draw upper arm
            painter.setPen(QPen(base_color.darker(110), 5.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(ssh_x, ssh_y), QPointF(sel_x, sel_y))

            # Draw forearm
            painter.setPen(QPen(base_color.lighter(115), 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(sel_x, sel_y), QPointF(shd_x, shd_y))

            # Hand gripper marker
            painter.setPen(QPen(QColor("#f8fafc"), 4.0))
            painter.drawPoint(QPointF(shd_x, shd_y))

        # ---------------------------------------------------------------------
        # C. Torso & Jumpsuit
        # ---------------------------------------------------------------------
        t_pts = [
            (state.x - rx * torso_wid + fx * torso_len, state.y - ry * torso_wid + fy * torso_len, state.z),
            (state.x + rx * torso_wid + fx * torso_len, state.y + ry * torso_wid + fy * torso_len, state.z),
            (state.x + rx * (torso_wid * 0.8) - fx * torso_len, state.y + ry * (torso_wid * 0.8) - fy * torso_len, state.z),
            (state.x - rx * (torso_wid * 0.8) - fx * torso_len, state.y - ry * (torso_wid * 0.8) - fy * torso_len, state.z),
        ]
        torso_poly = QPolygonF()
        for tx, ty, tz in t_pts:
            tsx, tsy, _ = project_3d_point(tx, ty, tz, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            torso_poly.append(QPointF(tsx, tsy))

        # Fill Torso
        torso_brush = QBrush(base_color)
        pen_torso = QPen(QColor("#ffffff") if is_selected else (base_color.lighter(140) if is_hovered else base_color.darker(130)))
        pen_torso.setWidthF(2.5 if is_selected else 1.5)
        painter.setPen(pen_torso)
        painter.setBrush(torso_brush)
        painter.drawPolygon(torso_poly)

        # Parachute Container (Rig on back)
        rig_pts = [
            (state.x - rx * 6.5 + fx * 4.0, state.y - ry * 6.5 + fy * 4.0, state.z + 1.5),
            (state.x + rx * 6.5 + fx * 4.0, state.y + ry * 6.5 + fy * 4.0, state.z + 1.5),
            (state.x + rx * 6.0 - fx * 12.0, state.y + ry * 6.0 - fy * 12.0, state.z + 1.5),
            (state.x - rx * 6.0 - fx * 12.0, state.y - ry * 6.0 - fy * 12.0, state.z + 1.5),
        ]
        rig_poly = QPolygonF()
        for rx_i, ry_i, rz_i in rig_pts:
            rsx, rsy, _ = project_3d_point(rx_i, ry_i, rz_i, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            rig_poly.append(QPointF(rsx, rsy))

        painter.setPen(QPen(QColor("#0f172a"), 1.0))
        painter.setBrush(QColor("#1e293b"))  # Dark charcoal rig
        painter.drawPolygon(rig_poly)

        # ---------------------------------------------------------------------
        # D. Head, Helmet & Gaze Ray (HEAD SWITCH)
        # ---------------------------------------------------------------------
        head_x = state.x + fx * (torso_len + 5.5)
        head_y = state.y + fy * (torso_len + 5.5)
        head_z = state.z + 2.5
        hsx, hsy, _ = project_3d_point(head_x, head_y, head_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)

        # Gaze angle calculation: body heading + head_turn_deg
        total_gaze_deg = (state.heading_deg + state.head_turn_deg) % 360.0
        rad_gaze = math.radians(total_gaze_deg)
        gfx, gfy = math.sin(rad_gaze), math.cos(rad_gaze)

        # Draw Gaze Ray / Head Switch Beam
        if self.show_gaze_rays:
            gaze_len = 45.0
            gt_x = head_x + gfx * gaze_len
            gt_y = head_y + gfy * gaze_len
            gt_z = head_z
            gsx, gsy, _ = project_3d_point(gt_x, gt_y, gt_z, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)

            if state.head_switch_active:
                # Pulsing yellow/cyan beam for active head switch
                beam_alpha = int(180 + 75 * math.sin(self.pulse_phase * 2.0))
                pen_beam = QPen(QColor(250, 204, 21, beam_alpha), 2.0, Qt.PenStyle.DashLine)
                painter.setPen(pen_beam)
                painter.drawLine(QPointF(hsx, hsy), QPointF(gsx, gsy))

                # Sightline target crosshair
                painter.setPen(QColor(250, 204, 21, 220))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(gsx, gsy), 5.0, 5.0)
                painter.drawLine(QPointF(gsx - 8, gsy), QPointF(gsx + 8, gsy))
                painter.drawLine(QPointF(gsx, gsy - 8), QPointF(gsx, gsy + 8))

                # Gaze target tag
                if state.gaze_target:
                    painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    painter.setPen(QColor(254, 240, 138))
                    painter.drawText(QRectF(gsx + 8, gsy - 8, 80, 16), Qt.AlignmentFlag.AlignLeft, f"→ {state.gaze_target}")
            else:
                # Normal subtle forward sightline
                pen_beam = QPen(QColor(148, 163, 184, 90), 1.0, Qt.PenStyle.DotLine)
                painter.setPen(pen_beam)
                painter.drawLine(QPointF(hsx, hsy), QPointF(gsx, gsy))

        # Helmet shell
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.setBrush(QColor("#f8fafc"))
        helmet_radius = max(5.0, 8.5 * (self.zoom * 0.9))
        painter.drawEllipse(QPointF(hsx, hsy), helmet_radius, helmet_radius)

        # Helmet Visor (colored by gaze direction)
        vx = hsx + gfx * (helmet_radius * 0.7)
        vy = hsy - gfy * (helmet_radius * 0.7)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0284c7") if not state.head_switch_active else QColor("#eab308"))
        painter.drawEllipse(QPointF(vx, vy), helmet_radius * 0.45, helmet_radius * 0.45)

        # ---------------------------------------------------------------------
        # E. Slot Badges, Key Crown & Head Switch Icon
        # ---------------------------------------------------------------------
        if self.show_slot_labels:
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.setPen(QColor("#0f172a"))
            # Shadow label
            painter.drawText(QRectF(px - 39, py - 37, 80, 20), Qt.AlignmentFlag.AlignCenter, slot)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRectF(px - 40, py - 38, 80, 20), Qt.AlignmentFlag.AlignCenter, slot)

        # 3D KEY Crown Badge
        if self.show_key_badge and self.current_formation:
            is_keyer = False
            if self.current_formation.primary_key_slot.startswith(slot):
                is_keyer = True
            elif slot == "IC" and "Inside Center" in self.current_formation.primary_key_slot:
                is_keyer = True
            elif slot == "OC" and "Outside Center" in self.current_formation.primary_key_slot:
                is_keyer = True
            elif slot == "Point" and "Point" in self.current_formation.primary_key_slot:
                is_keyer = True
            elif slot == "Tail" and "Tail" in self.current_formation.primary_key_slot:
                is_keyer = True

            if is_keyer:
                kx, ky, _ = project_3d_point(state.x, state.y, state.z + 14.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
                pulse_scale = 1.0 + 0.15 * math.sin(self.pulse_phase)
                
                # Floating golden KEY pill
                painter.setPen(QPen(QColor(245, 158, 11), 1.5))
                painter.setBrush(QColor(251, 191, 36, 230))
                badge_w = 44 * pulse_scale
                badge_h = 18 * pulse_scale
                painter.drawRoundedRect(QRectF(kx - badge_w/2, ky - badge_h/2, badge_w, badge_h), 6.0, 6.0)
                
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Black))
                painter.setPen(QColor("#78350f"))
                painter.drawText(QRectF(kx - badge_w/2, ky - badge_h/2, badge_w, badge_h), Qt.AlignmentFlag.AlignCenter, "🔑 KEY")

        # Head Switch Alert Banner above flyer
        if state.head_switch_active:
            hs_lbl_x, hs_lbl_y, _ = project_3d_point(head_x, head_y, head_z + 10.0, self.yaw, self.pitch, self.zoom, self.pan_x, self.pan_y, cx, cy)
            painter.setPen(QPen(QColor(234, 179, 8), 1.2))
            painter.setBrush(QColor(30, 41, 59, 210))
            painter.drawRoundedRect(QRectF(hs_lbl_x - 45, hs_lbl_y - 10, 90, 20), 4.0, 4.0)
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            painter.setPen(QColor(253, 224, 71))
            painter.drawText(QRectF(hs_lbl_x - 45, hs_lbl_y - 10, 90, 20), Qt.AlignmentFlag.AlignCenter, "👀 HEAD SWITCH")

        painter.restore()

    def _draw_viewport_hud(self, painter: QPainter):
        """Draws screen-space HUD overlay elements (Current Formation, Phase, Controls)."""
        painter.save()
        w = self.width()

        # Formation Name & Code Badge (Top Left)
        if self.current_formation:
            f = self.current_formation
            badge_rect = QRectF(15, 15, 260, 64)
            painter.setPen(QPen(QColor(56, 189, 248, 120), 1.0))
            painter.setBrush(QColor(15, 23, 42, 220))
            painter.drawRoundedRect(badge_rect, 8.0, 8.0)

            # Code Box
            code_rect = QRectF(25, 25, 42, 42)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#38bdf8") if not f.is_block else QColor("#f43f5e"))
            painter.drawRoundedRect(code_rect, 6.0, 6.0)

            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(code_rect, Qt.AlignmentFlag.AlignCenter, f.code)

            # Title & Subtitle
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.setPen(QColor("#f8fafc"))
            painter.drawText(QRectF(75, 23, 190, 22), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f.name)

            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
            painter.setPen(QColor("#94a3b8"))
            cat_str = f"BLOCK ({f.points} Pts) • {f.subgroup_split}" if f.is_block else f"RANDOM ({f.points} Pt)"
            painter.drawText(QRectF(75, 45, 190, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, cat_str)

        # 3D Navigation Guide (Bottom Left)
        nav_rect = QRectF(15, self.height() - 40, 280, 25)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(15, 23, 42, 180))
        painter.drawRoundedRect(nav_rect, 4.0, 4.0)
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(nav_rect, Qt.AlignmentFlag.AlignCenter, "🖱️ Links-Klick: 3D Orbit | Scroll/Rechts: Zoom | Rad-Klick: Pan")

        # Phase Badge for Blocks (Top Right)
        if self.current_formation and self.current_formation.is_block:
            phase_str = "1. INITIAL BUILD"
            if self.current_phase > 1.4:
                phase_str = "3. CLOSING BUILD"
            elif self.current_phase > 0.4:
                phase_str = "2. INTER PICTURE"

            p_rect = QRectF(w - 200, 15, 185, 34)
            painter.setPen(QPen(QColor(244, 63, 94, 140), 1.0))
            painter.setBrush(QColor(15, 23, 42, 220))
            painter.drawRoundedRect(p_rect, 6.0, 6.0)

            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.setPen(QColor("#fda4af"))
            painter.drawText(p_rect, Qt.AlignmentFlag.AlignCenter, f"Phase: {phase_str}")

        painter.restore()


# =============================================================================
# Detail & Slot Inspector Widget
# =============================================================================

class FormationDetailWidget(QWidget):
    """
    Inspector panel detailing the selected formation, who has the key,
    head switches, and slot-by-slot duties for Point, OC, IC, and Tail.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_formation: Optional[FormationDefinition] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 1. Master Key & Head Switch Banner Card
        self.card_master = QFrame()
        self.card_master.setObjectName("masterCard")
        self.card_master.setStyleSheet("""
            QFrame#masterCard {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        m_layout = QVBoxLayout(self.card_master)
        m_layout.setContentsMargins(10, 8, 10, 8)
        m_layout.setSpacing(6)

        # Row A: Key Info
        r1 = QHBoxLayout()
        lbl_key_icon = QLabel("🔑")
        lbl_key_icon.setFont(QFont("Segoe UI", 16))
        self.lbl_key_title = QLabel("<b>KEY:</b> Inside Center [IC]")
        self.lbl_key_title.setStyleSheet("color: #f59e0b; font-size: 13px;")
        r1.addWidget(lbl_key_icon)
        r1.addWidget(self.lbl_key_title)
        r1.addStretch()
        m_layout.addLayout(r1)

        self.lbl_key_desc = QLabel("Trigger: Grip completion on Point's wrists and rear close")
        self.lbl_key_desc.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        self.lbl_key_desc.setWordWrap(True)
        m_layout.addWidget(self.lbl_key_desc)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #334155;")
        m_layout.addWidget(sep)

        # Row B: Head Switch Info
        r2 = QHBoxLayout()
        lbl_hs_icon = QLabel("👀")
        lbl_hs_icon.setFont(QFont("Segoe UI", 16))
        self.lbl_hs_title = QLabel("<b>HEAD SWITCHES:</b> Point & IC")
        self.lbl_hs_title.setStyleSheet("color: #38bdf8; font-size: 13px;")
        r2.addWidget(lbl_hs_icon)
        r2.addWidget(self.lbl_hs_title)
        r2.addStretch()
        m_layout.addLayout(r2)

        self.lbl_hs_desc = QLabel("Point head switches right to spot IC; Centers keep shoulders level.")
        self.lbl_hs_desc.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        self.lbl_hs_desc.setWordWrap(True)
        m_layout.addWidget(self.lbl_hs_desc)

        layout.addWidget(self.card_master)

        # 2. Tab Widget for Slot Roles & Overview
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                background: #1e293b;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #0f172a;
                color: #94a3b8;
                padding: 6px 14px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-size: 11px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
        """)

        # Overview Tab
        self.txt_overview = QTextBrowser()
        self.txt_overview.setOpenExternalLinks(True)
        self.txt_overview.setStyleSheet("border: none; background: transparent; color: #f1f5f9; font-size: 11px;")
        self.tabs.addTab(self.txt_overview, "📋 Übersicht & Tipps")

        # Point Tab (Red)
        self.txt_point = QTextBrowser()
        self.txt_point.setStyleSheet("border: none; background: transparent; color: #f1f5f9; font-size: 11px;")
        self.tabs.addTab(self.txt_point, "🔴 Point")

        # OC Tab (Blue)
        self.txt_oc = QTextBrowser()
        self.txt_oc.setStyleSheet("border: none; background: transparent; color: #f1f5f9; font-size: 11px;")
        self.tabs.addTab(self.txt_oc, "🔵 Outside Center")

        # IC Tab (Yellow)
        self.txt_ic = QTextBrowser()
        self.txt_ic.setStyleSheet("border: none; background: transparent; color: #f1f5f9; font-size: 11px;")
        self.tabs.addTab(self.txt_ic, "🟡 Inside Center")

        # Tail Tab (Green)
        self.txt_tail = QTextBrowser()
        self.txt_tail.setStyleSheet("border: none; background: transparent; color: #f1f5f9; font-size: 11px;")
        self.tabs.addTab(self.txt_tail, "🟢 Tail")

        layout.addWidget(self.tabs)

    def set_formation(self, form: FormationDefinition):
        """Updates panel content with formation details."""
        self.current_formation = form

        # Update Master Card
        self.lbl_key_title.setText(f"<b>KEY PERSON:</b> {form.primary_key_slot}")
        self.lbl_key_desc.setText(
            f"<b>Auslöser:</b> {form.key_trigger}<br>"
            f"<b>Signal-Methode:</b> {form.key_method}<br>"
            f"<i>{form.shared_key_notes}</i>"
        )

        self.lbl_hs_title.setText("<b>HEAD SWITCHES & REFERENZEN:</b>")
        self.lbl_hs_desc.setText(form.head_switch_summary)

        # Overview Tab
        tips_html = "".join([f"<li>{tip}</li>" for tip in form.coach_tips])
        pitfalls_html = "".join([f"<li style='color: #fca5a5;'>{p}</li>" for p in form.pitfalls_and_busts])
        
        block_info = ""
        if form.is_block:
            block_info = f"""
            <div style='background: #0f172a; padding: 8px; border-radius: 6px; margin-bottom: 8px;'>
                <b style='color: #38bdf8;'>Block Details:</b><br>
                • <b>Start Formation:</b> {form.initial_name}<br>
                • <b>Ziel Formation:</b> {form.second_name}<br>
                • <b>Subgruppen:</b> {form.subgroup_split}<br>
                • <b>Drehgrade:</b> {form.inter_degrees}<br>
                • <b>Vertikal (Over/Under):</b> {'Verfügbar' if form.supports_vertical else 'Nur Flat/On-Level'}
            </div>
            """

        self.txt_overview.setHtml(f"""
        <div style='font-family: Segoe UI, sans-serif;'>
            <h3 style='color: #38bdf8; margin-top: 0;'>{form.code}: {form.name}</h3>
            {block_info}
            <b style='color: #4ade80;'>Profi Coach Tipps (Rhythm / Airspeed / Fury):</b>
            <ul>{tips_html}</ul>
            <b style='color: #ef4444;'>Häufige Fehler & Bust-Gefahren:</b>
            <ul>{pitfalls_html}</ul>
            <div style='background: #1e293b; border-left: 3px solid #38bdf8; padding: 6px; margin-top: 8px;'>
                <b style='color: #94a3b8;'>5-Schritte Block-Debrief Checklist:</b><br>
                1. <b>Build</b> (Aufbau, Achse, Centerpoint)<br>
                2. <b>Key</b> (Gleichzeitiger explosiver Release)<br>
                3. <b>Inter Picture</b> (Richtung, Distanz, Speed, Drehung)<br>
                4. <b>Levels</b> (Piece Partner & Pieces zueinander)<br>
                5. <b>Close</b> (Momentum stoppen, Griffe präsentieren)
            </div>
        </div>
        """)

        # Slot Tabs
        for slot_key, txt_widget in [
            ("Point", self.txt_point),
            ("OC", self.txt_oc),
            ("IC", self.txt_ic),
            ("Tail", self.txt_tail)
        ]:
            detail = form.slot_details.get(slot_key)
            if not detail:
                txt_widget.setHtml("<p>Keine Slot-Details hinterlegt.</p>")
                continue

            txt_widget.setHtml(f"""
            <div style='font-family: Segoe UI, sans-serif;'>
                <h3 style='color: {detail.color}; margin-top: 0;'>{detail.slot_name}</h3>
                <div style='background: #0f172a; padding: 8px; border-radius: 6px; margin-bottom: 8px;'>
                    <b style='color: #38bdf8;'>Rolle:</b> {detail.role_summary}<br>
                    <b style='color: #f59e0b;'>Drehung:</b> {detail.rotation_degrees}<br>
                    <b style='color: #4ade80;'>Key-Rolle:</b> {detail.key_role}
                </div>
                <b>Aufgaben & Flugmechanik:</b>
                <p>{detail.duties_description}</p>
                <b>Griffe (Nehmen & Präsentieren):</b>
                <p>{detail.grip_actions}</p>
                <div style='background: #0f172a; border-left: 3px solid #f59e0b; padding: 6px;'>
                    <b style='color: #f59e0b;'>Blickfeld & Head Switch:</b><br>
                    {detail.head_switch_notes}
                </div>
            </div>
            """)

    def select_slot_tab(self, slot_name: str):
        """Switches active tab to the specified slot."""
        tab_map = {"Point": 1, "OC": 2, "IC": 3, "Tail": 4}
        idx = tab_map.get(slot_name, 0)
        self.tabs.setCurrentIndex(idx)


# =============================================================================
# Main Application Window
# =============================================================================

class FormationExplorerWindow(QMainWindow):
    """Main window for the 4-Way Formation 3D Visualizer."""

    def __init__(self, initial_code: Optional[str] = "21"):
        super().__init__()
        self.setWindowTitle("FAI 4-Way Formation Skydiving 3D Visualizer & Coach")
        self.resize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background: #0b1329;
            }
            QWidget {
                color: #f1f5f9;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QListWidget {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #1e293b;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #2563eb;
                color: #ffffff;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background: #1e293b;
            }
            QLineEdit {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f8fafc;
            }
            QPushButton {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                color: #f8fafc;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #334155;
            }
            QPushButton:pressed {
                background: #0f172a;
            }
        """)

        self._init_ui()
        self._load_formations(initial_code)

    def _init_ui(self):
        # Central splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ---------------------------------------------------------------------
        # Left Panel: Dive Pool Browser & Filter
        # ---------------------------------------------------------------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(8)

        # Search box
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Suchen (z.B. 21, Molar, Star)...")
        self.txt_search.textChanged.connect(self._filter_formations)
        left_layout.addWidget(self.txt_search)

        # Category Filter Bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)
        self.btn_filter_all = QPushButton("Alle")
        self.btn_filter_randoms = QPushButton("Randoms")
        self.btn_filter_blocks = QPushButton("Blocks")
        self.btn_filter_vertical = QPushButton("Vertikal")

        for btn in [self.btn_filter_all, self.btn_filter_randoms, self.btn_filter_blocks, self.btn_filter_vertical]:
            btn.setCheckable(True)
            filter_layout.addWidget(btn)

        self.btn_filter_all.setChecked(True)
        self.filter_group = QButtonGroup(self)
        self.filter_group.addButton(self.btn_filter_all)
        self.filter_group.addButton(self.btn_filter_randoms)
        self.filter_group.addButton(self.btn_filter_blocks)
        self.filter_group.addButton(self.btn_filter_vertical)
        self.filter_group.buttonClicked.connect(self._filter_formations)
        left_layout.addLayout(filter_layout)

        # Formation List
        self.list_formations = QListWidget()
        self.list_formations.currentItemChanged.connect(self._on_formation_selected)
        left_layout.addWidget(self.list_formations)

        left_panel.setMinimumWidth(240)
        splitter.addWidget(left_panel)

        # ---------------------------------------------------------------------
        # Center Panel: 3D Viewport & Playback Controls
        # ---------------------------------------------------------------------
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(4, 4, 4, 4)
        center_layout.setSpacing(8)

        # 3D Canvas
        self.viewport_3d = Formation3DWidget()
        self.viewport_3d.flyer_clicked.connect(self._on_flyer_clicked)
        self.viewport_3d.phase_changed.connect(self._on_phase_changed)
        center_layout.addWidget(self.viewport_3d, 1)

        # Animation & Phase Controls Bar
        controls_frame = QFrame()
        controls_frame.setStyleSheet("background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 6px;")
        c_layout = QVBoxLayout(controls_frame)
        c_layout.setContentsMargins(8, 6, 8, 6)
        c_layout.setSpacing(6)

        # Row 1: Phase Slider & Steppers
        r1 = QHBoxLayout()
        self.btn_phase_initial = QPushButton("1. Initial Build")
        self.btn_phase_inter = QPushButton("2. Inter Picture")
        self.btn_phase_close = QPushButton("3. Closing Build")

        self.btn_phase_initial.clicked.connect(lambda: self._set_slider_phase(0.0))
        self.btn_phase_inter.clicked.connect(lambda: self._set_slider_phase(1.0))
        self.btn_phase_close.clicked.connect(lambda: self._set_slider_phase(2.0))

        self.slider_phase = QSlider(Qt.Orientation.Horizontal)
        self.slider_phase.setRange(0, 200)
        self.slider_phase.setValue(0)
        self.slider_phase.valueChanged.connect(self._on_slider_moved)

        r1.addWidget(self.btn_phase_initial)
        r1.addWidget(self.slider_phase)
        r1.addWidget(self.btn_phase_inter)
        r1.addWidget(self.btn_phase_close)
        c_layout.addLayout(r1)

        # Row 2: Playback & View Controls
        r2 = QHBoxLayout()
        self.btn_play = QPushButton("▶ Animation Abspielen")
        self.btn_play.setStyleSheet("background: #2563eb; color: #ffffff;")
        self.btn_play.clicked.connect(self._toggle_playback)

        self.chk_vertical = QCheckBox("Vertikal (Over/Under)")
        self.chk_vertical.toggled.connect(self.viewport_3d.set_vertical_technique)

        self.btn_view_top = QPushButton("Draufsicht (2D)")
        self.btn_view_top.clicked.connect(lambda: self.viewport_3d.reset_camera(top_down=True))

        self.btn_view_3d = QPushButton("3D Perspektive")
        self.btn_view_3d.clicked.connect(lambda: self.viewport_3d.reset_camera(top_down=False))

        r2.addWidget(self.btn_play)
        r2.addWidget(self.chk_vertical)
        r2.addStretch()
        r2.addWidget(self.btn_view_top)
        r2.addWidget(self.btn_view_3d)
        c_layout.addLayout(r2)

        center_layout.addWidget(controls_frame)
        center_panel.setMinimumWidth(480)
        splitter.addWidget(center_panel)

        # ---------------------------------------------------------------------
        # Right Panel: Slot Inspector & Master Key Card
        # ---------------------------------------------------------------------
        self.detail_widget = FormationDetailWidget()
        self.detail_widget.setMinimumWidth(320)
        splitter.addWidget(self.detail_widget)

        # Splitter initial sizes: 22% list, 48% 3D viewport, 30% detail panel
        splitter.setSizes([260, 560, 380])

        # Top Menu Bar
        self._init_menu_bar()

    def _init_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("background: #0f172a; color: #f8fafc;")

        # Ansicht Menu
        menu_view = menubar.addMenu("Ansicht")
        
        act_gaze = QAction("Blickstrahlen / Head Switches anzeigen", self, checkable=True)
        act_gaze.setChecked(True)
        act_gaze.toggled.connect(self._toggle_gaze_rays)
        menu_view.addAction(act_gaze)

        act_links = QAction("Griff-Verbindungen anzeigen", self, checkable=True)
        act_links.setChecked(True)
        act_links.toggled.connect(self._toggle_grip_links)
        menu_view.addAction(act_links)

        act_axis = QAction("Point-Tail Achse anzeigen", self, checkable=True)
        act_axis.setChecked(True)
        act_axis.toggled.connect(self._toggle_axis)
        menu_view.addAction(act_axis)

        act_compass = QAction("Kompass & Quadranten anzeigen", self, checkable=True)
        act_compass.setChecked(True)
        act_compass.toggled.connect(self._toggle_compass)
        menu_view.addAction(act_compass)

        # Scoring Tool Shortcut
        menu_tools = menubar.addMenu("Tools")
        act_scoring = QAction("Debriefing & Scoring Tool starten", self)
        act_scoring.triggered.connect(self._launch_scoring_tool)
        menu_tools.addAction(act_scoring)

    def _load_formations(self, default_code: Optional[str] = "21"):
        """Populates formation list from database."""
        self.list_formations.clear()
        all_forms = get_all_formations()

        selected_item = None
        for f in all_forms:
            type_tag = "Block" if f.is_block else "Random"
            vert_tag = " [Vert]" if f.supports_vertical else ""
            item_text = f"{f.code}: {f.name} ({type_tag}{vert_tag})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, f.code)
            self.list_formations.addItem(item)

            if default_code and f.code.upper() == default_code.upper():
                selected_item = item

        if selected_item:
            self.list_formations.setCurrentItem(selected_item)
        elif self.list_formations.count() > 0:
            self.list_formations.setCurrentRow(0)

    def _filter_formations(self):
        """Filters list by search query and category pill."""
        query = self.txt_search.text().strip().lower()
        show_randoms = self.btn_filter_randoms.isChecked()
        show_blocks = self.btn_filter_blocks.isChecked()
        show_vertical = self.btn_filter_vertical.isChecked()
        show_all = self.btn_filter_all.isChecked()

        for i in range(self.list_formations.count()):
            item = self.list_formations.item(i)
            code = item.data(Qt.ItemDataRole.UserRole)
            f = get_formation(code)
            if not f:
                continue

            # Category filter
            cat_match = True
            if show_randoms and f.is_block:
                cat_match = False
            elif show_blocks and not f.is_block:
                cat_match = False
            elif show_vertical and not f.supports_vertical:
                cat_match = False

            # Search text filter
            text_match = True
            if query:
                search_haystack = f"{f.code} {f.name} {f.primary_key_slot} {f.initial_name} {f.second_name or ''}".lower()
                text_match = (query in search_haystack)

            item.setHidden(not (cat_match and text_match))

    def _on_formation_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            return
        code = current.data(Qt.ItemDataRole.UserRole)
        f = get_formation(code)
        if not f:
            return

        self.viewport_3d.set_formation(f)
        self.detail_widget.set_formation(f)

        # Update block-specific controls
        self.btn_phase_initial.setEnabled(f.is_block)
        self.btn_phase_inter.setEnabled(f.is_block)
        self.btn_phase_close.setEnabled(f.is_block)
        self.slider_phase.setEnabled(f.is_block)
        self.btn_play.setEnabled(f.is_block)
        self.chk_vertical.setEnabled(f.supports_vertical)
        self.chk_vertical.setChecked(f.supports_vertical)

        self.slider_phase.setValue(0)
        self.btn_play.setText("▶ Animation Abspielen")

    def _on_flyer_clicked(self, slot_name: str):
        """When user clicks a flyer in 3D, switch to their slot tab."""
        self.detail_widget.select_slot_tab(slot_name)

    def _set_slider_phase(self, phase_val: float):
        """Sets slider to exact phase 0.0, 1.0, or 2.0."""
        self.slider_phase.setValue(int(phase_val * 100))

    def _on_slider_moved(self, value: int):
        phase = value / 100.0
        self.viewport_3d.set_phase(phase)

    def _on_phase_changed(self, phase: float):
        """Syncs slider when animation is running."""
        self.slider_phase.blockSignals(True)
        self.slider_phase.setValue(int(phase * 100))
        self.slider_phase.blockSignals(False)

    def _toggle_playback(self):
        self.viewport_3d.play_pause_animation()
        if self.viewport_3d.is_animating:
            self.btn_play.setText("⏸ Pause")
            self.btn_play.setStyleSheet("background: #e11d48; color: #ffffff;")
        else:
            self.btn_play.setText("▶ Animation Abspielen")
            self.btn_play.setStyleSheet("background: #2563eb; color: #ffffff;")

    def _toggle_gaze_rays(self, checked: bool):
        self.viewport_3d.show_gaze_rays = checked
        self.viewport_3d.update()

    def _toggle_grip_links(self, checked: bool):
        self.viewport_3d.show_grip_links = checked
        self.viewport_3d.update()

    def _toggle_axis(self, checked: bool):
        self.viewport_3d.show_point_tail_axis = checked
        self.viewport_3d.update()

    def _toggle_compass(self, checked: bool):
        self.viewport_3d.show_compass_grid = checked
        self.viewport_3d.update()

    def _launch_scoring_tool(self):
        """Launches scoring.py if present."""
        scoring_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scoring.py")
        if os.path.exists(scoring_path):
            import subprocess
            subprocess.Popen([sys.executable, scoring_path])
        else:
            QMessageBox.information(self, "Info", "scoring.py wurde im aktuellen Verzeichnis nicht gefunden.")


# =============================================================================
# Application Entry Point
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Check for optional command-line formation argument (e.g. `python3 formation_tool.py 21`)
    init_code = "21"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        init_code = sys.argv[1].strip().upper()

    window = FormationExplorerWindow(initial_code=init_code)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
