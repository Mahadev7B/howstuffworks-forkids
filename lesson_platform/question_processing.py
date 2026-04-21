import re
from typing import Tuple


PUNCTUATION_RE = re.compile(r"[^\w\s]")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_question(raw_question: str) -> str:
    text = (raw_question or "").strip().lower()
    text = text.replace("what's", "what is").replace("how's", "how is")
    text = PUNCTUATION_RE.sub(" ", text)
    text = re.sub(r"\b(please|can you|could you|tell me|for kids)\b", " ", text)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def classify_question(raw_question: str) -> Tuple[str, str]:
    text = normalize_question(raw_question)

    safety_markers = {"safe", "healthy", "danger", "harm", "toxic", "poison"}
    comparison_markers = {"difference", "compare", "vs", "versus", "better", "than"}
    definition_markers = {"what is", "meaning", "define"}
    process_markers = {"how", "happen", "formed", "work", "process", "cycle", "why"}
    inside_markers = {"inside", "under", "body", "structure", "part"}

    if any(marker in text for marker in safety_markers):
        intent = "safety_health"
    elif any(marker in text for marker in comparison_markers):
        intent = "comparison"
    elif any(marker in text for marker in definition_markers):
        intent = "definition"
    elif any(marker in text for marker in process_markers):
        intent = "how_it_works"
    else:
        intent = "process_explanation"

    if intent == "comparison":
        visual_type = "comparison"
    elif "cycle" in text:
        visual_type = "cycle"
    elif any(marker in text for marker in inside_markers):
        visual_type = "inside_view"
    elif intent in {"how_it_works", "process_explanation"}:
        visual_type = "process_flow"
    else:
        visual_type = "labeled_diagram"

    return intent, visual_type
