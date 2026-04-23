import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from .config import Settings
from .diagram_renderer import render_scene_svg


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

INFOGRAPHIC_TOPIC_BRIEF = """
Create a clean black-and-white pencil sketch educational infographic for the topic: "{topic}".

Style:
- hand-drawn pencil sketch
- simple line art
- minimal shading
- kid-friendly
- textbook/worksheet style
- high clarity, not artistic

Layout:
- title at the top
- 4 step-by-step panels arranged horizontally or in a grid
- arrows connecting each step to show progression
- one larger central diagram explaining the concept clearly
- small summary or key idea at the bottom

Content:
- each panel shows a different stage of the process
- include short, simple labels (1 sentence max per panel)
- show motion using arrows (airflow, water flow, movement, forces)
- highlight cause and effect clearly
- emphasize important parts using thicker lines or repeated arrows

Visual rules:
- no colors (black and white only)
- no clutter
- no overlapping labels
- clear spacing between sections
- consistent drawing style for all objects
- diagrams must be easy for kids to understand at a glance

Goal:
The final image should look like a clear educational worksheet that explains "{topic}" step-by-step using diagrams, arrows, and labels.
Use consistent diagram style similar to school science textbooks and simple engineering diagrams.
""".strip()


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


@dataclass(frozen=True)
class AIClient:
    provider: str
    api_key: str


class ProviderRateLimitError(RuntimeError):
    pass


def create_ai_client(settings: Settings) -> Optional[AIClient]:
    if not settings.openai_api_key:
        return None
    return AIClient(provider="openai", api_key=settings.openai_api_key)


def _openai_generate_text(*, model: str, api_key: str, system_prompt: str, user_prompt: str) -> str:
    endpoint = "https://api.openai.com/v1/chat/completions"
    retry_delays = [0.8, 1.6, 3.2]
    include_response_format = True
    body = None
    for attempt_index, delay_seconds in enumerate(retry_delays):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
        }
        if include_response_format:
            payload["response_format"] = {"type": "json_object"}

        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=45) as response:
                body = json.loads(response.read().decode("utf-8"))
                break
        except HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                error_body = ""

            if exc.code == 400 and include_response_format:
                include_response_format = False
                logger.warning(
                    "OpenAI rejected JSON response_format; retrying without response_format (attempt %s/%s).",
                    attempt_index + 1,
                    len(retry_delays),
                )
                continue
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                wait_seconds = delay_seconds
                if retry_after:
                    try:
                        wait_seconds = max(wait_seconds, float(retry_after))
                    except (TypeError, ValueError):
                        pass
                if attempt_index < len(retry_delays) - 1:
                    logger.warning(
                        "OpenAI rate limited (429). Retrying in %.2fs (attempt %s/%s).",
                        wait_seconds,
                        attempt_index + 1,
                        len(retry_delays),
                    )
                    time.sleep(wait_seconds)
                    continue
                raise ProviderRateLimitError("OpenAI is rate limited (HTTP 429).") from exc
            if 500 <= exc.code <= 599 and attempt_index < len(retry_delays) - 1:
                logger.warning(
                    "OpenAI upstream error %s. Retrying in %.2fs (attempt %s/%s).",
                    exc.code,
                    delay_seconds,
                    attempt_index + 1,
                    len(retry_delays),
                )
                time.sleep(delay_seconds)
                continue
            error_hint = ""
            if error_body:
                first_line = error_body.strip().splitlines()[0][:220]
                if first_line:
                    error_hint = f" | {first_line}"
            raise RuntimeError(f"OpenAI request failed: {exc}{error_hint}") from exc
        except (URLError, TimeoutError) as exc:
            if attempt_index < len(retry_delays) - 1:
                logger.warning(
                    "OpenAI request network issue. Retrying in %.2fs (attempt %s/%s).",
                    delay_seconds,
                    attempt_index + 1,
                    len(retry_delays),
                )
                time.sleep(delay_seconds)
                continue
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI returned invalid JSON response payload.") from exc

    if body is None:
        raise RuntimeError("OpenAI request failed without a response payload.")

    try:
        choices = body.get("choices", [])
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            output_text = "\n".join(part for part in text_parts if part).strip()
        else:
            output_text = str(content).strip()
    except (IndexError, KeyError, TypeError) as exc:
        raise RuntimeError("OpenAI response did not include text content.") from exc

    if not output_text:
        raise RuntimeError("OpenAI response text was empty.")
    return output_text


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


def _build_infographic_brief(topic: str) -> str:
    safe_topic = (topic or "").strip() or "this topic"
    return INFOGRAPHIC_TOPIC_BRIEF.format(topic=safe_topic)


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
    client: Optional[AIClient],
    improvement_notes: Optional[List[str]] = None,
) -> tuple[dict, str, int, float]:
    started = time.perf_counter()
    if client is None:
        lesson = fallback_lesson_plan(question)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return lesson, "Add your OpenAI API key to generate a live lesson.", elapsed_ms, 0.0

    def _generate_with_model(model_name: str) -> str:
        infographic_brief = _build_infographic_brief(question)
        return _openai_generate_text(
            model=model_name,
            api_key=client.api_key,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=(
                f"Question: {question}"
                f"{quality_notes}\n\n"
                f"Infographic brief:\n{infographic_brief}\n\n"
                f"{schema_hint}"
            ),
        )

    try:
        quality_notes = ""
        if improvement_notes:
            notes = [f"- {note}" for note in improvement_notes[:12]]
            quality_notes = (
                "\nQuality guidance from user feedback:\n"
                + "\n".join(notes)
                + "\nApply spelling corrections and avoid repeated mistakes."
            )

        schema_hint = (
            "Return only JSON with keys: title, narration_lines, scene_descriptions, scene_durations, big_idea. "
            "narration_lines must be exactly 5 strings. scene_descriptions must be exactly 5 strings. "
            "scene_durations must be exactly 5 integers."
        )
        raw_text = _generate_with_model(settings.openai_model)
        lesson = validate_lesson_plan(AnimationLesson.model_validate_json(raw_text))
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return lesson, "", elapsed_ms, 0.004
    except ProviderRateLimitError:
        logger.warning("OpenAI rate limited; using fallback lesson.")
        lesson = fallback_lesson_plan(question)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return (
            lesson,
            "OpenAI is busy right now, so we showed a quick fallback lesson. Please try again in a moment.",
            elapsed_ms,
            0.0,
        )
    except RuntimeError as exc:
        if "HTTP Error 400" in str(exc) and settings.openai_model != "gpt-4.1-mini":
            try:
                logger.warning(
                    "OpenAI model '%s' rejected request; retrying with gpt-4.1-mini.",
                    settings.openai_model,
                )
                raw_text = _generate_with_model("gpt-4.1-mini")
                lesson = validate_lesson_plan(AnimationLesson.model_validate_json(raw_text))
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                return lesson, "", elapsed_ms, 0.004
            except (RuntimeError, ValueError, AttributeError, TypeError):
                logger.exception("OpenAI fallback model also failed; using fallback lesson.")
        logger.exception("Lesson generation failed; using fallback lesson.")
        lesson = fallback_lesson_plan(question)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return (
            lesson,
            "We could not generate a fresh lesson right now, so here is a simple example.",
            elapsed_ms,
            0.0,
        )
    except (ValueError, AttributeError, TypeError):
        logger.exception("Lesson generation failed; using fallback lesson.")
        lesson = fallback_lesson_plan(question)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return (
            lesson,
            "We could not generate a fresh lesson right now, so here is a simple example.",
            elapsed_ms,
            0.0,
        )

def _topic_hint_from_scene_prompts(scene_prompts: List[str]) -> str:
    blob = " ".join(scene_prompts).lower()
    if any(word in blob for word in ("rain", "cloud", "water", "evaporation", "precipitation", "condensation")):
        return "water cycle rain cloud evaporation condensation precipitation"
    if any(word in blob for word in ("plant", "leaf", "sunlight", "photosynthesis")):
        return "plant sunlight photosynthesis leaf"
    if any(word in blob for word in ("rocket", "space", "planet", "moon")):
        return "space rocket planet moon"
    if any(word in blob for word in ("fraction", "slice", "divide")):
        return "fraction divide slice"
    if any(word in blob for word in ("force", "push", "pull", "motion")):
        return "force push pull motion"
    return ""


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


def generate_scene_images(
    scene_prompts: List[str],
    settings: Settings,
    client: Optional[AIClient],
) -> tuple[List[GeneratedMedia], List[str], int, float]:
    started = time.perf_counter()
    images: List[GeneratedMedia] = []
    messages: List[str] = []
    estimated_cost = 0.0

    topic_hint = _topic_hint_from_scene_prompts(scene_prompts)
    for index, scene_prompt in enumerate(scene_prompts, start=1):
        images.append(
            GeneratedMedia(
                content=render_scene_svg(index, scene_prompt, topic_hint=topic_hint),
                ext="svg",
                media_type="image",
            )
        )

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
    client: Optional[AIClient],
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

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return None, "", elapsed_ms, 0.0
