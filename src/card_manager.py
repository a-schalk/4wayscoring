"""
Rhythm XP Formation Cards Manager.
Provides quick access to extracted Rhythm XP formation diagrams (Randoms A-Q, Blocks 1-22).
"""

import os
import re
from typing import Optional, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
ASSETS_CARDS_DIR = os.path.join(PROJECT_ROOT, "assets", "cards")
RANDOMS_DIR = os.path.join(ASSETS_CARDS_DIR, "randoms")
BLOCKS_DIR = os.path.join(ASSETS_CARDS_DIR, "blocks")


def get_card_path(code: str) -> Optional[str]:
    """
    Returns the absolute path to the card image for a formation token.
    Supports:
        - Randoms: 'A', 'B', ... 'Q'
        - Full Blocks: '1', '12', '22'
        - Block parts: '12-1', '12-2', '12.1', '12_2'
    """
    clean = code.strip().upper()
    if not clean:
        return None

    # Check Block with part (e.g. 12-1, 12-2)
    m = re.match(r'^(\d+)[-._]([12])$', clean)
    if m:
        base, part = m.group(1), m.group(2)
        p = os.path.join(BLOCKS_DIR, f"{base}-{part}.png")
        if os.path.isfile(p):
            return p
        # Fallback to full block
        p_full = os.path.join(BLOCKS_DIR, f"{base}.png")
        if os.path.isfile(p_full):
            return p_full

    # Check pure number block (e.g. 12)
    if clean.isdigit():
        p = os.path.join(BLOCKS_DIR, f"{clean}.png")
        if os.path.isfile(p):
            return p

    # Check Random letter
    p = os.path.join(RANDOMS_DIR, f"{clean}.png")
    if os.path.isfile(p):
        return p

    return None


def get_card_pixmap(code: str, max_width: int = 180, max_height: int = 180) -> Optional[QPixmap]:
    """Returns a scaled QPixmap for the given formation code."""
    path = get_card_path(code)
    if not path or not os.path.isfile(path):
        return None
    pix = QPixmap(path)
    if pix.isNull():
        return None
    return pix.scaled(
        max_width, max_height,
        aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
        transformMode=Qt.TransformationMode.SmoothTransformation
    )
