"""Computes bubble positions for comic panels. No YOLO — deterministic placement."""
from typing import List, Tuple

# Positions: (x_frac, y_frac, w_frac, h_frac) as fraction of panel size
# Order: top-right, bottom-left, top-left, bottom-right, center-top, center-bottom
_BUBBLE_SLOTS = [
    (0.55, 0.05, 0.40, 0.18),   # top-right
    (0.05, 0.72, 0.40, 0.18),   # bottom-left
    (0.05, 0.05, 0.40, 0.18),   # top-left
    (0.55, 0.72, 0.40, 0.18),   # bottom-right
    (0.30, 0.02, 0.40, 0.15),   # center-top
    (0.30, 0.78, 0.40, 0.15),   # center-bottom
]


def compute_bubble_positions(
    panel_w: int,
    panel_h: int,
    num_bubbles: int,
    padding: int = 20,
) -> List[Tuple[int, int, int, int]]:
    """
    Returns list of (x1, y1, x2, y2) bounding boxes for bubbles.
    Uses fixed positions — no model or YOLO dependency.
    """
    if num_bubbles <= 0:
        return []

    positions = []
    for i in range(min(num_bubbles, len(_BUBBLE_SLOTS))):
        xf, yf, wf, hf = _BUBBLE_SLOTS[i]
        x1 = int(panel_w * xf) + padding
        y1 = int(panel_h * yf) + padding
        x2 = int(panel_w * (xf + wf)) - padding
        y2 = int(panel_h * (yf + hf)) - padding
        if x2 > x1 and y2 > y1:
            positions.append((x1, y1, x2, y2))

    return positions
