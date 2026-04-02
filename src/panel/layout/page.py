"""Page layout: build panel positions and assemble final page."""
from PIL import Image, ImageDraw
from typing import List

from src.utils.schemas import Layout


def build_three_panel_layout(
    page_w: int = 1024,
    page_h: int = 1536,
    margin: int = 40,
    gutter: int = 30,
) -> Layout:
    """Returns fixed 3-panel vertical layout rectangles."""
    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin - 2 * gutter
    panel_h = usable_h // 3

    boxes = []
    for i in range(3):
        x1 = margin
        y1 = margin + i * (panel_h + gutter)
        x2 = margin + usable_w
        y2 = y1 + panel_h
        boxes.append((x1, y1, x2, y2))

    return Layout(page_w, page_h, margin, gutter, boxes)


def assemble_page(panels: List[Image.Image], layout: Layout) -> Image.Image:
    """Assembles individual panels into a single page layout."""
    page = Image.new("RGB", (layout.page_w, layout.page_h), "white")
    for i, panel in enumerate(panels):
        x1, y1, x2, y2 = layout.panel_boxes[i]
        target_w = x2 - x1
        target_h = y2 - y1

        panel_resized = panel.resize((target_w, target_h), Image.Resampling.LANCZOS)
        page.paste(panel_resized, (x1, y1))

    d = ImageDraw.Draw(page)
    for (x1, y1, x2, y2) in layout.panel_boxes:
        d.rectangle((x1, y1, x2, y2), outline="black", width=6)

    return page
