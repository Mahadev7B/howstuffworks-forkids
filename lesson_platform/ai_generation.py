import base64
import logging
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
            "Then, we can see a change happen.",
            "Now we know the big idea in a simple way.",
        ],
        "scene_descriptions": [
            f"black and white pencil sketch of a child looking at {topic}, simple labels, worksheet style",
            "black and white pencil sketch of a starting point with one arrow, simple educational diagram",
            "black and white pencil sketch of small parts working together, clean lines, simple labels",
            "black and white pencil sketch of a visible change with arrows, worksheet style diagram",
            "black and white pencil sketch of a happy child pointing to the big idea, simple labels",
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


def generate_lesson_plan(question: str, settings: Settings, client: Optional[OpenAI]) -> tuple[dict, str, int, float]:
    started = time.perf_counter()
    if client is None:
        lesson = fallback_lesson_plan(question)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return lesson, "Add your OpenAI API key to generate a live lesson.", elapsed_ms, 0.0

    try:
        response = client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}"},
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


def generate_scene_images(
    scene_prompts: List[str],
    settings: Settings,
    client: Optional[OpenAI],
) -> tuple[List[GeneratedMedia], List[str], int, float]:
    started = time.perf_counter()
    images: List[GeneratedMedia] = []
    messages: List[str] = []
    estimated_cost = 0.0

    for prompt in scene_prompts:
        if client is None:
            images.append(
                GeneratedMedia(
                    content=_placeholder_svg_bytes(),
                    ext="svg",
                    media_type="image",
                    message="Add your OpenAI API key to generate sketch images.",
                )
            )
            continue

        image_prompt = (
            "Draw a black and white pencil sketch educational diagram for kids ages 6 to 10. "
            "Keep it simple, friendly, clear, and safe. Use simple labels. "
            f"Diagram idea: {add_whiteboard_style(prompt)}"
        )
        try:
            response = client.images.generate(
                model=settings.openai_image_model,
                prompt=image_prompt,
                size="1024x1024",
                quality="low",
                output_format="png",
                n=1,
            )
            image_base64 = _extract_image_base64(response)
            images.append(
                GeneratedMedia(
                    content=base64.b64decode(image_base64),
                    ext="png",
                    media_type="image",
                )
            )
            estimated_cost += 0.02
        except (OpenAIError, ValueError, AttributeError, TypeError):
            logger.exception("Image generation failed for one scene; using placeholder.")
            images.append(
                GeneratedMedia(
                    content=_placeholder_svg_bytes(),
                    ext="svg",
                    media_type="image",
                    message="The sketch could not be generated right now, so a placeholder is used.",
                )
            )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    for image in images:
        if image.message:
            messages.append(image.message)
    return images, messages, elapsed_ms, estimated_cost


def generate_audio(
    narration_lines: List[str],
    settings: Settings,
    client: Optional[OpenAI],
) -> tuple[Optional[GeneratedMedia], str, int, float]:
    started = time.perf_counter()
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
