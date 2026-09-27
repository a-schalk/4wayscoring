"""
Training Database for FAI 4-Way Formation Skydiving.
Stores briefing and debriefing history, formation frequencies, accuracy, and timing performance.
"""

import os
import json
import glob
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DEFAULT_DEBRIEFS_DIR = os.path.join(PROJECT_ROOT, "debriefs")
DB_FILE_PATH = os.path.join(DEFAULT_DEBRIEFS_DIR, "training_database.json")

# Standard FAI Dive Pool
ALL_RANDOMS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]
ALL_BLOCKS = [str(i) for i in range(1, 23)]


@dataclass
class FormationTrainingStats:
    code: str
    name: str = ""
    is_block: bool = False
    jump_count: int = 0
    score_count: int = 0
    bust_count: int = 0
    hold_times: List[float] = field(default_factory=list)
    transition_times: List[float] = field(default_factory=list)
    last_trained: str = ""
    last_jump_name: str = ""

    @property
    def accuracy(self) -> float:
        total = self.score_count + self.bust_count
        if total == 0:
            return 0.0
        return round((self.score_count / total) * 100.0, 1)

    @property
    def average_hold(self) -> Optional[float]:
        valid = [h for h in self.hold_times if h >= 0]
        if not valid:
            return None
        return round(sum(valid) / len(valid), 2)

    @property
    def average_transition(self) -> Optional[float]:
        valid = [t for t in self.transition_times if t >= 0]
        if not valid:
            return None
        return round(sum(valid) / len(valid), 2)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "is_block": self.is_block,
            "jump_count": self.jump_count,
            "score_count": self.score_count,
            "bust_count": self.bust_count,
            "hold_times": self.hold_times,
            "transition_times": self.transition_times,
            "last_trained": self.last_trained,
            "last_jump_name": self.last_jump_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FormationTrainingStats':
        return cls(
            code=data["code"],
            name=data.get("name", ""),
            is_block=data.get("is_block", False),
            jump_count=data.get("jump_count", 0),
            score_count=data.get("score_count", 0),
            bust_count=data.get("bust_count", 0),
            hold_times=data.get("hold_times", []),
            transition_times=data.get("transition_times", []),
            last_trained=data.get("last_trained", ""),
            last_jump_name=data.get("last_jump_name", ""),
        )


class TrainingDatabase:
    """Manages persistent training history across sessions and formation metrics."""

    def __init__(self, db_path: str = DB_FILE_PATH):
        self.db_path = db_path
        self.sessions_history: List[Dict[str, Any]] = []
        self.formation_stats: Dict[str, FormationTrainingStats] = {}
        self._init_empty_stats()
        self.load()

    def _init_empty_stats(self):
        try:
            import formation_db
            all_defs = {f.code: f.name for f in formation_db.get_all_formations()}
        except Exception:
            all_defs = {}

        for code in ALL_RANDOMS:
            name = all_defs.get(code, code)
            self.formation_stats[code] = FormationTrainingStats(code=code, name=name, is_block=False)

        for code in ALL_BLOCKS:
            name = all_defs.get(code, f"Block {code}")
            self.formation_stats[code] = FormationTrainingStats(code=code, name=name, is_block=True)

    def load(self):
        if not os.path.isfile(self.db_path):
            return
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sessions_history = data.get("sessions_history", [])
            raw_stats = data.get("formation_stats", {})
            for code, sdata in raw_stats.items():
                if code in self.formation_stats:
                    self.formation_stats[code] = FormationTrainingStats.from_dict(sdata)
        except Exception as e:
            print(f"Warning: Failed to load training DB: {e}")

    def save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            payload = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "sessions_history": self.sessions_history,
                "formation_stats": {
                    code: stat.to_dict() for code, stat in self.formation_stats.items()
                }
            }
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save training DB: {e}")

    def record_session(self, session_data: dict, file_path: str = "") -> bool:
        """Records points, timing, and draw from a JumpSession dictionary."""
        jump_name = session_data.get("jump_name", "Unbenannt")
        draw_string = session_data.get("draw_string", "")
        points = session_data.get("points", [])
        exit_time = session_data.get("exit_time")

        # Check if this file or jump is already recorded to avoid double counting
        file_key = os.path.basename(file_path) if file_path else ""
        existing = [s for s in self.sessions_history if s.get("file_key") == file_key and file_key]
        if existing:
            return False  # Already indexed

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        scores = sum(1 for p in points if p.get("status") == "APPROVED")
        busts = sum(1 for p in points if p.get("status") == "BUST")

        session_entry = {
            "file_key": file_key,
            "jump_name": jump_name,
            "draw_string": draw_string,
            "date": now_str,
            "points_count": len(points),
            "score": scores,
            "busts": busts,
            "file_path": file_path
        }
        self.sessions_history.append(session_entry)

        # Update stats for each point
        for i, pt in enumerate(points):
            raw_code = pt.get("formation", "").strip().upper()
            # Clean base code (e.g. '12-1' -> '12', 'A' -> 'A')
            base_code = raw_code.split("-")[0].split(".")[0].split("_")[0]
            if base_code not in self.formation_stats:
                continue

            stat = self.formation_stats[base_code]
            stat.jump_count += 1
            if pt.get("status") == "APPROVED":
                stat.score_count += 1
            else:
                stat.bust_count += 1

            stat.last_trained = now_str
            stat.last_jump_name = jump_name

            # Timing
            t_comp = pt.get("time_complete")
            t_key = pt.get("time_key")
            if t_comp is not None and t_key is not None:
                hold = round(t_key - t_comp, 3)
                stat.hold_times.append(hold)

            if i == 0 and t_comp is not None and exit_time is not None:
                trans = round(t_comp - exit_time, 3)
                stat.transition_times.append(trans)
            elif i > 0 and t_comp is not None:
                prev = points[i - 1]
                prev_ref = prev.get("time_key") if prev.get("time_key") is not None else prev.get("time_complete")
                if prev_ref is not None:
                    trans = round(t_comp - prev_ref, 3)
                    stat.transition_times.append(trans)

        self.save()
        return True

    def scan_debriefs_folder(self, folder: str = DEFAULT_DEBRIEFS_DIR) -> int:
        """Scans all *.json files in debriefs/ and updates stats."""
        if not os.path.isdir(folder):
            return 0

        # Reset session history and stats for a clean re-index
        self.sessions_history.clear()
        self._init_empty_stats()

        count = 0
        json_files = sorted(glob.glob(os.path.join(folder, "*_debrief.json")) + glob.glob(os.path.join(folder, "*.json")))
        for f in json_files:
            if os.path.basename(f) == "training_database.json":
                continue
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                if "draw_string" in data or "points" in data:
                    if self.record_session(data, file_path=f):
                        count += 1
            except Exception:
                pass
        self.save()
        return count

    def get_least_trained_formations(self, pool_type: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Returns list of (code, jump_count) sorted by jump_count ascending (least trained first).
        pool_type: 'randoms', 'blocks', or None (both).
        """
        items = []
        for code, stat in self.formation_stats.items():
            if pool_type == "randoms" and stat.is_block:
                continue
            if pool_type == "blocks" and not stat.is_block:
                continue
            items.append((code, stat.jump_count))
        # Sort by jump count ascending, then by code
        items.sort(key=lambda x: (x[1], x[0]))
        return items

    def get_summary_table_data(self) -> List[Dict[str, Any]]:
        """Returns structured data for GUI tables."""
        rows = []
        all_codes = sorted(ALL_RANDOMS) + sorted(ALL_BLOCKS, key=lambda x: int(x))
        for code in all_codes:
            stat = self.formation_stats.get(code)
            if not stat:
                continue
            rows.append({
                "code": stat.code,
                "name": stat.name,
                "type": "Block" if stat.is_block else "Random",
                "jump_count": stat.jump_count,
                "score_count": stat.score_count,
                "bust_count": stat.bust_count,
                "accuracy": stat.accuracy,
                "avg_hold": stat.average_hold,
                "avg_trans": stat.average_transition,
                "last_trained": stat.last_trained,
                "last_jump": stat.last_jump_name
            })
        return rows
