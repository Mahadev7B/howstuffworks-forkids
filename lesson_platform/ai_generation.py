import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import List, Optional

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

from .config import Settings


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You create simple, friendly learning answers for kids ages 6 to 10.

Rules:
- Keep everything simple, friendly, cheerful, and safe.
- Use short sentences and easy words.
- Return exactly 5 narration lines.
- Return exactly 5 scene descriptions.
- Return exactly 5 scene durations.
- Each narration line must match the scene with the same number.
- Scene durations must total close to 30 seconds.
- Each scene description must be suitable for a black and white pencil sketch educational worksheet.
"""


class AnimationLesson(BaseModel):
    title: str = Field(description="A short friendly title for the lesson.")
    narration_lines: List[str] = Field(min_length=5, max_length=5)
    scene_descriptions: List[str] = Field(min_length=5, max_length=5)
    scene_durations: List[int] = Field(min_length=5, max_length=5)
    big_idea: str = Field(description="One short sentence with the main idea.")


@dataclass
class GeneratedMedia:
    content: bytes
    ext: str
    media_type: str
    message: Optional[str] = None


def create_openai_client(settings: Settings) -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def add_whiteboard_style(prompt: str) -> str:
    prompt_lower = prompt.lower()
    required_terms = [
        "black and white",
        "pencil sketch",
        "educational",
        "clean lines",
        "worksheet",
    ]
    if all(term in prompt_lower for term in required_terms):
        return prompt
    return (
        f"{prompt}, black and white pencil sketch, simple educational diagram for kids, "
        "clean lines, worksheet style"
    )


def fallback_lesson_plan(question: str) -> dict:
    topic = question.strip() or "this idea"
    return {
        "title": "How It Works",
        "narration_lines": [
            f"Let us learn about {topic} one step at a time.",
            "First, something starts the process.",
            "Next, the parts begin to work together.",
            "Then we watch the main change happen clearly.",
            "Now we can see the result and big idea.",
        ],
        "scene_descriptions": [
            f"black and white pencil sketch of a child looking at {topic}, simple labels, worksheet style",
            "black and white pencil sketch of a starting point with one arrow, simple educational diagram",
            "black and white pencil sketch of small parts working together, clean lines, simple labels",
            "black and white pencil sketch of the key change in action, arrows and simple labels",
            "black and white pencil sketch of final result and big idea, worksheet style diagram",
        ],
        "scene_durations": [6, 6, 6, 6, 6],
        "big_idea": "Small steps help us understand how things work.",
    }


def validate_lesson_plan(lesson: AnimationLesson) -> dict:
    data = lesson.model_dump()
    data["narration_lines"] = [line.strip() for line in data["narration_lines"]]
    data["scene_descriptions"] = [add_whiteboard_style(desc) for desc in data["scene_descriptions"]]
    data["scene_durations"] = [max(3, int(duration)) for duration in data["scene_durations"]]
    if not 25 <= sum(data["scene_durations"]) <= 35:
        data["scene_durations"] = [6, 6, 6, 6, 6]
    return data


def generate_lesson_plan(
    question: str,
    settings: Settings,
    client: Optional[OpenAI],
    improvement_notes: Optional[List[str]] = None,
) -> tuple[dict, str, int, float]:
    started = time.perf_counter()
    if client is None:
        lesson = fallback_lesson_plan(question)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return lesson, "Add your OpenAI API key to generate a live lesson.", elapsed_ms, 0.0

    try:
        quality_notes = ""
        if improvement_notes:
            notes = [f"- {note}" for note in improvement_notes[:12]]
            quality_notes = (
                "\nQuality guidance from user feedback:\n"
                + "\n".join(notes)
                + "\nApply spelling corrections and avoid repeated mistakes."
            )

        response = client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}{quality_notes}"},
            ],
            text_format=AnimationLesson,
        )
        if response.output_parsed is None:
            raise ValueError("The model did not return a structured lesson.")
        lesson = validate_lesson_plan(response.output_parsed)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return lesson, "", elapsed_ms, 0.004
    except (OpenAIError, ValueError, AttributeError, TypeError):
        logger.exception("Lesson generation failed; using fallback lesson.")
        lesson = fallback_lesson_plan(question)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return (
            lesson,
            "We could not generate a fresh lesson right now, so here is a simple example.",
            elapsed_ms,
            0.0,
        )


def _extract_image_base64(response) -> str:
    if not response.data:
        raise ValueError("Image API response had no data items.")
    first_image = response.data[0]
    image_base64 = getattr(first_image, "b64_json", None)
    if not image_base64:
        raise ValueError("Image API response did not include b64_json.")
    return image_base64


def _placeholder_svg_bytes() -> bytes:
    svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <rect width="1024" height="1024" fill="#fffafd"/>
  <rect x="96" y="96" width="832" height="832" rx="28" fill="none" stroke="#283044" stroke-width="10" stroke-dasharray="22 22"/>
  <circle cx="300" cy="300" r="74" fill="none" stroke="#283044" stroke-width="12"/>
  <path d="M430 300 H710" fill="none" stroke="#283044" stroke-width="12" stroke-linecap="round"/>
  <path d="M660 250 L720 300 L660 350" fill="none" stroke="#283044" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M250 560 C350 470 470 660 580 560 C650 500 720 540 780 610" fill="none" stroke="#283044" stroke-width="12" stroke-linecap="round"/>
  <text x="512" y="780" text-anchor="middle" font-family="Arial, sans-serif" font-size="44" fill="#283044">Sketch coming soon</text>
  <text x="512" y="840" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" fill="#5d4b9a">The answer is ready to read.</text>
</svg>
""".strip()
    return svg.encode("utf-8")


def _wrap_text(text: str, width: int = 38) -> List[str]:
    words = (text or "").strip().split()
    if not words:
        return ["Let's learn together!"]
    lines: List[str] = []
    current: List[str] = []
    current_len = 0
    for word in words:
        token_len = len(word) + (1 if current else 0)
        if current and current_len + token_len > width:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += token_len
    if current:
        lines.append(" ".join(current))
    return lines[:4]


def _pick_scene_badge(prompt: str) -> str:
    text = (prompt or "").lower()
    if any(word in text for word in ("rain", "cloud", "water", "evaporation")):
        return "WATER CYCLE"
    if any(word in text for word in ("plant", "leaf", "sunlight", "photosynthesis")):
        return "PLANT POWER"
    if any(word in text for word in ("rocket", "space", "planet", "moon")):
        return "SPACE SCIENCE"
    if any(word in text for word in ("pizza", "fraction", "slice", "divide")):
        return "PIZZA MATH"
    if any(word in text for word in ("force", "push", "pull", "motion")):
        return "MOTION LAB"
    return "LEARNING LAB"


def _scene_icon_svg(prompt: str) -> str:
    text = (prompt or "").lower()
    if any(word in text for word in ("rain", "cloud", "water", "evaporation")):
        return """
  <ellipse cx="280" cy="280" rx="85" ry="48" fill="none" stroke="#2b3b6a" stroke-width="10"/>
  <ellipse cx="220" cy="286" rx="46" ry="32" fill="none" stroke="#2b3b6a" stroke-width="10"/>
  <ellipse cx="340" cy="286" rx="46" ry="32" fill="none" stroke="#2b3b6a" stroke-width="10"/>
  <path d="M240 360 L230 390 M280 360 L270 398 M320 360 L310 390" stroke="#2b3b6a" stroke-width="9" stroke-linecap="round"/>
"""
    if any(word in text for word in ("plant", "leaf", "sunlight", "photosynthesis")):
        return """
  <circle cx="280" cy="250" r="42" fill="none" stroke="#2b3b6a" stroke-width="10"/>
  <line x1="280" y1="185" x2="280" y2="150" stroke="#2b3b6a" stroke-width="9"/>
  <path d="M280 430 L280 290" stroke="#2b3b6a" stroke-width="10" />
  <path d="M280 350 C330 320 355 320 390 355 C340 365 310 372 280 350" fill="none" stroke="#2b3b6a" stroke-width="9"/>
  <path d="M280 385 C230 355 205 355 170 390 C220 398 250 405 280 385" fill="none" stroke="#2b3b6a" stroke-width="9"/>
"""
    if any(word in text for word in ("rocket", "space", "planet", "moon")):
        return """
  <path d="M250 380 L330 300 L390 360 L310 440 Z" fill="none" stroke="#2b3b6a" stroke-width="10"/>
  <circle cx="333" cy="362" r="22" fill="none" stroke="#2b3b6a" stroke-width="8"/>
  <path d="M390 360 L430 350 L410 390 Z" fill="none" stroke="#2b3b6a" stroke-width="8"/>
  <path d="M250 380 L220 400 L250 410 Z" fill="none" stroke="#2b3b6a" stroke-width="8"/>
"""
    if any(word in text for word in ("pizza", "fraction", "slice", "divide")):
        return """
  <circle cx="290" cy="320" r="115" fill="none" stroke="#2b3b6a" stroke-width="10"/>
  <line x1="290" y1="205" x2="290" y2="435" stroke="#2b3b6a" stroke-width="8"/>
  <line x1="175" y1="320" x2="405" y2="320" stroke="#2b3b6a" stroke-width="8"/>
  <line x1="210" y1="240" x2="370" y2="400" stroke="#2b3b6a" stroke-width="8"/>
"""
    return """
  <rect x="195" y="220" width="190" height="190" rx="22" fill="none" stroke="#2b3b6a" stroke-width="10"/>
  <circle cx="250" cy="280" r="14" fill="none" stroke="#2b3b6a" stroke-width="7"/>
  <circle cx="330" cy="280" r="14" fill="none" stroke="#2b3b6a" stroke-width="7"/>
  <path d="M245 345 C272 370 308 370 335 345" fill="none" stroke="#2b3b6a" stroke-width="8" stroke-linecap="round"/>
"""


def _local_scene_svg_bytes(prompt: str, scene_number: int) -> bytes:
    label = _pick_scene_badge(prompt)
    lines = _wrap_text(prompt, width=42)
    escaped_lines = [html.escape(line) for line in lines]
    text_y = 640
    text_svg = "\n".join(
        f'  <text x="130" y="{text_y + idx * 54}" font-family="Arial, sans-serif" font-size="40" fill="#1f2f5d">{line}</text>'
        for idx, line in enumerate(escaped_lines)
    )
    scene_title = html.escape(f"Scene {scene_number}")
    badge = html.escape(label)
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <rect width="1024" height="1024" fill="#f9fbff"/>
  <rect x="58" y="58" width="908" height="908" rx="34" fill="none" stroke="#1f2f5d" stroke-width="10" stroke-dasharray="24 16"/>
  <rect x="120" y="110" width="300" height="58" rx="24" fill="#ffe68b" stroke="#1f2f5d" stroke-width="5"/>
  <text x="145" y="149" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#1f2f5d">{scene_title}</text>
  <rect x="470" y="110" width="420" height="58" rx="24" fill="#d9e7ff" stroke="#1f2f5d" stroke-width="5"/>
  <text x="490" y="149" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#1f2f5d">{badge}</text>
  {_scene_icon_svg(prompt)}
{text_svg}
</svg>
""".strip()
    return svg.encode("utf-8")


def _generate_local_tts_audio(narration_lines: List[str]) -> tuple[Optional[GeneratedMedia], str]:
    try:
        import pyttsx3  # type: ignore

        narration = " ".join(narration_lines).strip()
        if not narration:
            return None, "Local Python TTS skipped because narration text is empty."
        tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()
        audio_bytes = b""
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 162)
            engine.save_to_file(narration, tmp_path)
            engine.runAndWait()
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        if not audio_bytes:
            return None, "Local Python TTS produced no audio bytes."
        return GeneratedMedia(content=audio_bytes, ext="wav", media_type="audio"), ""
    except Exception:
        logger.exception("Local Python TTS failed.")
        return None, "Local Python TTS is not available on this server yet (install/configure pyttsx3 + speech engine)."


def _image_attempt_sizes(settings: Settings) -> List[str]:
    supported_sizes = {"1024x1024", "1024x1536", "1536x1024", "auto"}
    configured_size = str(getattr(settings, "image_size", "auto") or "auto").strip().lower()
    attempts: List[str] = []
    if configured_size in supported_sizes:
        attempts.append(configured_size)
    attempts.extend(size for size in ["auto", "1024x1024"] if size not in attempts)
    return attempts


def generate_scene_images(
    scene_prompts: List[str],
    settings: Settings,
    client: Optional[OpenAI],
) -> tuple[List[GeneratedMedia], List[str], int, float]:
    started = time.perf_counter()
    images: List[GeneratedMedia] = []
    messages: List[str] = []
    estimated_cost = 0.0

    local_media_only = bool(getattr(settings, "local_media_only", False))
    if local_media_only:
        for index, scene_prompt in enumerate(scene_prompts, start=1):
            images.append(
                GeneratedMedia(
                    content=_local_scene_svg_bytes(scene_prompt, index),
                    ext="svg",
                    media_type="image",
                    message="Local Python sketch mode is on: scenes are generated without image API calls.",
                )
            )
    elif client is None:
        for _ in scene_prompts:
            images.append(
                GeneratedMedia(
                    content=_placeholder_svg_bytes(),
                    ext="svg",
                    media_type="image",
                    message="Add your OpenAI API key to generate sketch images.",
                )
            )
    else:
        max_generated_images = max(1, int(getattr(settings, "max_generated_images", 4)))

        def _generate_one(prompt: str) -> GeneratedMedia:
            image_prompt = (
                "Draw a black and white pencil sketch educational diagram for kids ages 6 to 10. "
                "Keep it simple, friendly, clear, and safe. Use simple labels. "
                f"Diagram idea: {add_whiteboard_style(prompt)}"
            )
            image_model = getattr(settings, "openai_image_model", "gpt-image-1")
            attempt_kwargs = [{"size": size} for size in _image_attempt_sizes(settings)]

            last_error: Optional[Exception] = None
            for extra in attempt_kwargs:
                try:
                    response = client.images.generate(
                        model=image_model,
                        prompt=image_prompt,
                        n=1,
                        **extra,
                    )
                    image_base64 = _extract_image_base64(response)
                    return GeneratedMedia(
                        content=base64.b64decode(image_base64),
                        ext="png",
                        media_type="image",
                    )
                except (OpenAIError, ValueError, AttributeError, TypeError) as exc:
                    last_error = exc

            error_hint = ""
            if last_error is not None:
                error_text = str(last_error).strip().splitlines()[0][:180]
                if error_text:
                    error_hint = f" ({error_text})"
            logger.exception("Image generation failed for one scene after retries; using placeholder.")
            return GeneratedMedia(
                content=_placeholder_svg_bytes(),
                ext="svg",
                media_type="image",
                message=f"The sketch could not be generated right now, so a placeholder is used.{error_hint}",
            )

        ordered_results: list[Optional[GeneratedMedia]] = [None] * len(scene_prompts)
        image_parallelism = max(1, int(getattr(settings, "image_parallelism", 3)))
        payable_count = min(len(scene_prompts), max_generated_images)
        with ThreadPoolExecutor(max_workers=min(image_parallelism, payable_count)) as executor:
            future_map = {
                executor.submit(_generate_one, scene_prompt): index
                for index, scene_prompt in enumerate(scene_prompts[:payable_count])
            }
            for future in as_completed(future_map):
                index = future_map[future]
                ordered_results[index] = future.result()

        if len(scene_prompts) > payable_count:
            budget_message = (
                "Using low-cost sketch mode: some scenes reuse a simple placeholder to keep total API cost under budget."
            )
            messages.append(budget_message)
            for index in range(payable_count, len(scene_prompts)):
                ordered_results[index] = GeneratedMedia(
                    content=_placeholder_svg_bytes(),
                    ext="svg",
                    media_type="image",
                    message=budget_message,
                )

        for result in ordered_results:
            if result is None:
                result = GeneratedMedia(
                    content=_placeholder_svg_bytes(),
                    ext="svg",
                    media_type="image",
                    message="Image generation timed out; using placeholder.",
                )
            images.append(result)
            if result.ext == "png":
                estimated_cost += 0.02

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    seen_messages: set[str] = set()
    for image in images:
        if image.message and image.message not in seen_messages:
            seen_messages.add(image.message)
            messages.append(image.message)
    return images, messages, elapsed_ms, estimated_cost


def generate_audio(
    narration_lines: List[str],
    settings: Settings,
    client: Optional[OpenAI],
) -> tuple[Optional[GeneratedMedia], str, int, float]:
    started = time.perf_counter()
    if not getattr(settings, "audio_enabled", True):
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return None, "Audio generation is disabled for faster responses.", elapsed_ms, 0.0

    local_tts_enabled = bool(getattr(settings, "local_tts_enabled", False))
    local_media_only = bool(getattr(settings, "local_media_only", False))

    if local_media_only or local_tts_enabled:
        media, local_message = _generate_local_tts_audio(narration_lines)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if media is not None:
            return media, "", elapsed_ms, 0.0
        return None, local_message, elapsed_ms, 0.0

    if client is None:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return None, "Add your OpenAI API key to generate narration audio.", elapsed_ms, 0.0

    try:
        response = client.audio.speech.create(
            model=settings.openai_tts_model,
            voice=settings.openai_tts_voice,
            input=" ".join(narration_lines),
            instructions=(
                "Speak in a warm, friendly teacher voice for kids. "
                "Use a calm pace and cheerful tone."
            ),
            response_format="mp3",
        )
        audio_bytes = getattr(response, "content", None)
        if audio_bytes is None and hasattr(response, "read"):
            audio_bytes = response.read()
        if not audio_bytes:
            raise ValueError("TTS response did not include audio bytes.")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return GeneratedMedia(content=audio_bytes, ext="mp3", media_type="audio"), "", elapsed_ms, 0.003
    except (OpenAIError, AttributeError, ValueError, TypeError):
        logger.exception("Audio generation failed; lesson will run with captions only.")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return None, "Audio could not be generated right now, so captions will guide the lesson.", elapsed_ms, 0.0
