import html
import math
import re
from dataclasses import dataclass
from typing import Callable


CANVAS_W = 1024
CANVAS_H = 1024
INK = "#1c2648"
PAPER = "#f8fafc"
PANEL = "#ffffff"
ACCENT = "#eef2f8"
FONT = "Verdana, Arial, sans-serif"


@dataclass(frozen=True)
class Layout:
    frame_x: int = 48
    frame_y: int = 48
    frame_w: int = 928
    frame_h: int = 928
    title_x: int = 108
    title_y: int = 102
    title_w: int = 286
    title_h: int = 58
    badge_x: int = 428
    badge_y: int = 102
    badge_w: int = 476
    badge_h: int = 58
    art_x: int = 110
    art_y: int = 190
    art_w: int = 804
    art_h: int = 450
    caption_x: int = 110
    caption_y: int = 700
    caption_w: int = 804
    caption_h: int = 220


LAYOUT = Layout()


def _escape(text: str) -> str:
    return html.escape(text or "")


def _clean_caption(scene_prompt: str) -> str:
    text = (scene_prompt or "").strip()
    if not text:
        return "Let us explore this idea step by step."
    text = re.sub(r"(?i)^black and white pencil sketch of\s+", "", text).strip()
    text = re.sub(r"(?i)^black and white pencil sketch\s+", "", text).strip()
    text = re.sub(r"(?i)\b(simple|clean)\s+labels?\b", "", text)
    text = re.sub(r"(?i)\bworksheet style\b", "", text)
    text = re.sub(r"(?i)\bsimple educational diagram for kids\b", "", text)
    text = re.sub(r"(?i)\bclean lines\b", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" ,.")
    if len(text) > 130:
        text = text[:130].rstrip(" ,.") + "..."
    return text or "Let us explore this idea step by step."


def _wrap(text: str, width: int = 42) -> list[str]:
    words = text.split()
    if not words:
        return ["Learning is fun!"]
    lines: list[str] = []
    line: list[str] = []
    current_len = 0
    for word in words:
        token = len(word) + (1 if line else 0)
        if line and current_len + token > width:
            lines.append(" ".join(line))
            line = [word]
            current_len = len(word)
        else:
            line.append(word)
            current_len += token
    if line:
        lines.append(" ".join(line))
    return lines[:4]


def _hand_line(x1: float, y1: float, x2: float, y2: float, width: int = 6) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{INK}" stroke-width="{width}" stroke-linecap="round"/>'
        f'<line x1="{x1 + 1.5}" y1="{y1 + 1.0}" x2="{x2 + 1.5}" y2="{y2 + 1.0}" '
        f'stroke="{INK}" stroke-width="{max(2, width - 2)}" stroke-linecap="round" opacity="0.55"/>'
    )


def component_label(text: str, x: int, y: int, anchor: str = "start", size: int = 26) -> str:
    safe = _escape(text)
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" '
        f'font-size="{size}" font-weight="600" fill="{INK}">{safe}</text>'
    )


def component_arrow(x1: int, y1: int, x2: int, y2: int) -> str:
    angle = math.atan2(y2 - y1, x2 - x1)
    wing = 16
    a1 = angle + math.radians(160)
    a2 = angle - math.radians(160)
    w1x = x2 + wing * math.cos(a1)
    w1y = y2 + wing * math.sin(a1)
    w2x = x2 + wing * math.cos(a2)
    w2y = y2 + wing * math.sin(a2)
    return (
        _hand_line(x1, y1, x2, y2, 6)
        + _hand_line(x2, y2, w1x, w1y, 5)
        + _hand_line(x2, y2, w2x, w2y, 5)
    )


def component_cloud(cx: int, cy: int, scale: float = 1.0) -> str:
    r = int(44 * scale)
    r2 = int(34 * scale)
    dx = int(34 * scale)
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="6"/>'
        f'<circle cx="{cx - dx}" cy="{cy + 6}" r="{r2}" fill="none" stroke="{INK}" stroke-width="6"/>'
        f'<circle cx="{cx + dx}" cy="{cy + 6}" r="{r2}" fill="none" stroke="{INK}" stroke-width="6"/>'
    )


def component_sun(cx: int, cy: int, r: int = 50) -> str:
    rays = []
    for angle in (0, 45, 90, 135):
        rad = math.radians(angle)
        x1 = cx + (r + 12) * math.cos(rad)
        y1 = cy + (r + 12) * math.sin(rad)
        x2 = cx + (r + 34) * math.cos(rad)
        y2 = cy + (r + 34) * math.sin(rad)
        rays.append(_hand_line(x1, y1, x2, y2, 5))
        rays.append(_hand_line(cx - (x1 - cx), cy - (y1 - cy), cx - (x2 - cx), cy - (y2 - cy), 5))
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="7"/>' + "".join(rays)


def component_raindrops(x: int, y: int, count: int = 5, spacing: int = 32) -> str:
    parts = []
    for idx in range(count):
        xx = x + idx * spacing
        parts.append(_hand_line(xx, y, xx - 8, y + 36, 5))
    return "".join(parts)


def component_rocket(x: int, y: int, scale: float = 1.0) -> str:
    w = int(70 * scale)
    h = int(170 * scale)
    nose_x = x + w // 2
    return (
        f'<path d="M{x + w//2} {y} L{x + w} {y + h//3} L{x + w//2} {y + h} L{x} {y + h//3} Z" '
        f'fill="none" stroke="{INK}" stroke-width="6"/>'
        f'<circle cx="{nose_x}" cy="{y + h//2}" r="{int(14 * scale)}" fill="none" stroke="{INK}" stroke-width="5"/>'
        f'<path d="M{x} {y + h//3} L{x - int(22*scale)} {y + h//2} L{x} {y + int(h*0.62)} Z" fill="none" stroke="{INK}" stroke-width="5"/>'
        f'<path d="M{x + w} {y + h//3} L{x + w + int(22*scale)} {y + h//2} L{x + w} {y + int(h*0.62)} Z" fill="none" stroke="{INK}" stroke-width="5"/>'
    )


def component_plant(x: int, y: int, scale: float = 1.0) -> str:
    stem_h = int(160 * scale)
    return (
        _hand_line(x, y, x, y - stem_h, 7)
        + f'<path d="M{x} {y-95} C{x+48} {y-128} {x+74} {y-126} {x+96} {y-92} C{x+60} {y-84} {x+28} {y-78} {x} {y-95}" '
        f'fill="none" stroke="{INK}" stroke-width="6"/>'
        + f'<path d="M{x} {y-62} C{x-48} {y-95} {x-74} {y-93} {x-96} {y-59} C{x-60} {y-51} {x-28} {y-45} {x} {y-62}" '
        f'fill="none" stroke="{INK}" stroke-width="6"/>'
    )


def component_waterline(y: int) -> str:
    return f'<path d="M150 {y} C320 {y-55} 540 {y-55} 840 {y}" fill="none" stroke="{INK}" stroke-width="8"/>'


def _layout_shell(scene_number: int, badge: str) -> str:
    return f"""
<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{PAPER}"/>
<rect x="{LAYOUT.frame_x}" y="{LAYOUT.frame_y}" width="{LAYOUT.frame_w}" height="{LAYOUT.frame_h}" rx="36" fill="{PANEL}" stroke="{INK}" stroke-width="8"/>
<rect x="{LAYOUT.title_x}" y="{LAYOUT.title_y}" width="{LAYOUT.title_w}" height="{LAYOUT.title_h}" rx="24" fill="{ACCENT}" stroke="{INK}" stroke-width="5"/>
{component_label(f"Scene {scene_number}", LAYOUT.title_x + 24, LAYOUT.title_y + 39, size=30)}
<rect x="{LAYOUT.badge_x}" y="{LAYOUT.badge_y}" width="{LAYOUT.badge_w}" height="{LAYOUT.badge_h}" rx="24" fill="{ACCENT}" stroke="{INK}" stroke-width="5"/>
{component_label(badge, LAYOUT.badge_x + 24, LAYOUT.badge_y + 39, size=30)}
"""


def _caption_panel(text: str) -> str:
    lines = _wrap(text, width=46)
    text_nodes = []
    for idx, line in enumerate(lines):
        text_nodes.append(component_label(line, LAYOUT.caption_x + 26, LAYOUT.caption_y + 56 + idx * 40, size=28))
    return (
        f'<rect x="{LAYOUT.caption_x}" y="{LAYOUT.caption_y}" width="{LAYOUT.caption_w}" height="{LAYOUT.caption_h}" '
        f'rx="24" fill="{ACCENT}" stroke="{INK}" stroke-width="4"/>'
        + "".join(text_nodes)
    )


def template_process_flow(scene_number: int, badge: str, caption: str, drawing: str) -> str:
    return (
        _layout_shell(scene_number, badge)
        + drawing
        + _caption_panel(caption)
    )


def template_cycle(scene_number: int, badge: str, caption: str, drawing: str) -> str:
    cycle_ring = (
        f'<path d="M300 575 C360 500 470 468 575 475 C665 482 746 525 790 595" fill="none" stroke="{INK}" stroke-width="8"/>'
        + component_arrow(790, 595, 790, 594)
        + f'<path d="M260 595 C285 645 355 690 440 710 C535 732 640 714 720 668" fill="none" stroke="{INK}" stroke-width="8"/>'
        + component_arrow(260, 595, 259, 594)
    )
    return _layout_shell(scene_number, badge) + cycle_ring + drawing + _caption_panel(caption)


def template_comparison(scene_number: int, badge: str, caption: str, drawing: str) -> str:
    divider = _hand_line(512, 212, 512, 650, 4)
    return _layout_shell(scene_number, badge) + divider + drawing + _caption_panel(caption)


def template_labeled_diagram(scene_number: int, badge: str, caption: str, drawing: str) -> str:
    return _layout_shell(scene_number, badge) + drawing + _caption_panel(caption)


def _badge_from_topic(topic_hint: str, prompt: str) -> str:
    text = f"{topic_hint} {prompt}".lower()
    if any(w in text for w in ("rain", "water", "cloud", "evaporation")):
        return "WATER CYCLE"
    if any(w in text for w in ("rocket", "space", "planet")):
        return "ROCKET SCIENCE"
    if any(w in text for w in ("plant", "leaf", "root")):
        return "PLANT LAB"
    if any(w in text for w in ("compare", "difference", "vs")):
        return "COMPARE & LEARN"
    return "HOW IT WORKS"


def _pick_template(topic_hint: str, prompt: str, scene_number: int) -> str:
    text = f"{topic_hint} {prompt}".lower()
    if any(w in text for w in ("rain", "water", "cloud", "evaporation", "condensation")):
        cycle_map = {1: "process_flow", 2: "cycle", 3: "process_flow", 4: "comparison", 5: "cycle"}
        return cycle_map.get(scene_number, "labeled_diagram")
    if scene_number == 1:
        return "labeled_diagram"
    if scene_number == 2:
        return "process_flow"
    if scene_number == 3:
        return "comparison"
    if scene_number == 5:
        return "cycle"
    return "process_flow"


def _water_cycle_drawing(scene_number: int) -> str:
    if scene_number == 1:
        return (
            component_sun(220, 300, 56)
            + component_waterline(545)
            + component_arrow(610, 540, 610, 390)
            + component_label("Sun warms water", 495, 355, size=24)
            + component_label("Vapor rises", 630, 445, size=24)
        )
    if scene_number == 2:
        return (
            component_cloud(620, 300, 1.2)
            + component_waterline(545)
            + component_arrow(450, 540, 560, 390)
            + component_label("Vapor cools in the sky", 520, 390, size=24)
        )
    if scene_number == 3:
        return (
            component_cloud(620, 280, 1.2)
            + component_raindrops(540, 350, 5, 28)
            + component_waterline(560)
            + component_label("Rain falls", 560, 430, size=24)
        )
    if scene_number == 4:
        return (
            f'<path d="M300 525 L390 345 L480 525 Z" fill="none" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M560 525 L650 345 L740 525 Z" fill="none" stroke="{INK}" stroke-width="6"/>'
            + component_arrow(390, 525, 315, 590)
            + component_arrow(650, 525, 730, 590)
            + component_waterline(600)
            + component_label("Water runs downhill", 430, 360, size=24)
        )
    return (
        component_cloud(650, 290, 1.1)
        + component_raindrops(590, 352, 4, 28)
        + f'<ellipse cx="300" cy="550" rx="170" ry="70" fill="none" stroke="{INK}" stroke-width="7"/>'
        + component_arrow(460, 520, 620, 380)
        + component_label("Collection", 235, 545, size=24)
        + component_label("Cycle repeats", 654, 380, size=24)
    )


def _generic_drawing(topic_hint: str, prompt: str, scene_number: int, template_name: str) -> str:
    text = f"{topic_hint} {prompt}".lower()
    if "rocket" in text or "space" in text:
        icon = component_rocket(205, 275, 1.15)
        icon_label = component_label("Rocket", 220, 495, size=24)
    elif "plant" in text or "leaf" in text:
        icon = component_plant(260, 540, 1.0)
        icon_label = component_label("Plant", 210, 495, size=24)
    elif "rain" in text or "water" in text:
        icon = component_cloud(270, 310, 1.1) + component_raindrops(205, 360, 4, 26)
        icon_label = component_label("Cloud", 214, 495, size=24)
    else:
        icon = component_sun(250, 320, 58)
        icon_label = component_label("Main idea", 190, 495, size=24)

    if template_name == "comparison":
        right = component_cloud(740, 305, 1.0) + component_label("Part B", 695, 495, size=24)
        left = icon + icon_label + component_label("Part A", 215, 530, size=24)
        return left + right
    if template_name == "cycle":
        return icon + component_arrow(360, 520, 640, 350) + component_cloud(700, 310, 1.0) + icon_label
    if template_name == "process_flow":
        return icon + component_arrow(390, 405, 640, 405) + component_label("Next step", 520, 376, size=24)
    return icon + icon_label + component_label("Label each part", 500, 370, size=24)


def render_scene_svg(scene_number: int, scene_prompt: str, topic_hint: str = "") -> bytes:
    caption = _clean_caption(scene_prompt)
    badge = _badge_from_topic(topic_hint, scene_prompt)
    template_name = _pick_template(topic_hint, scene_prompt, scene_number)
    text = f"{topic_hint} {scene_prompt}".lower()

    if any(w in text for w in ("rain", "water", "cloud", "evaporation", "condensation")):
        drawing = _water_cycle_drawing(scene_number)
    else:
        drawing = _generic_drawing(topic_hint, scene_prompt, scene_number, template_name)

    template_map: dict[str, Callable[[int, str, str, str], str]] = {
        "process_flow": template_process_flow,
        "cycle": template_cycle,
        "comparison": template_comparison,
        "labeled_diagram": template_labeled_diagram,
    }
    render_fn = template_map.get(template_name, template_labeled_diagram)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}">'
        + render_fn(scene_number, badge, caption, drawing)
        + "</svg>"
    )
    return svg.encode("utf-8")
