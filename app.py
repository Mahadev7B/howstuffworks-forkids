import base64
import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY_FILES = [
    Path("bash/env/API_KEY"),
    Path("bash/env/API KEY.txt"),
]


class KidAnswer(BaseModel):
    title: str = Field(description="A short friendly title for the answer.")
    explanation: str = Field(description="A short paragraph for kids age 6 to 10.")
    steps: List[str] = Field(
        min_length=4,
        max_length=4,
        description="Exactly 4 short step sentences.",
    )
    big_idea: str = Field(description="One short sentence with the main idea.")
    pencil_sketch_prompt: str = Field(
        description="A black and white pencil sketch diagram prompt."
    )


class AnimationLesson(BaseModel):
    title: str = Field(description="A short friendly title for the lesson.")
    narration_lines: List[str] = Field(
        min_length=5,
        max_length=5,
        description="Exactly 5 short narration lines for kids ages 6 to 10.",
    )
    scene_descriptions: List[str] = Field(
        min_length=5,
        max_length=5,
        description="Exactly 5 pencil sketch scene descriptions.",
    )
    scene_durations: List[int] = Field(
        min_length=5,
        max_length=5,
        description="Exactly 5 scene durations in seconds, total close to 30.",
    )
    big_idea: str = Field(description="One short sentence with the main idea.")


SYSTEM_PROMPT = """
You create simple, friendly learning answers for kids ages 6 to 10.

Rules:
- Answer the child's question in a safe, calm, cheerful way.
- Use simple words and short sentences.
- Avoid scary, harsh, or negative wording.
- Do not include complex technical details.
- Always return exactly 4 steps.
- Each step must be one short sentence.
- The big idea must be one short line.
- The pencil sketch prompt must describe a simple black and white educational diagram.
- The pencil sketch prompt should include simple labels and clear objects.
"""


LESSON_SYSTEM_PROMPT = """
You create YouTube-style whiteboard animation lesson plans for kids ages 6 to 10.

Rules:
- Keep everything simple, friendly, cheerful, and safe.
- Avoid scary, harsh, or negative wording.
- Use short sentences and easy words.
- Return exactly 5 narration lines.
- Return exactly 5 scene descriptions.
- Return exactly 5 scene durations.
- Each narration line must match the scene with the same number.
- Scene durations must total close to 30 seconds.
- Each scene description must be for a black and white pencil sketch diagram.
- Each scene description must be suitable for a clean worksheet-style educational drawing.
"""


def fallback_answer(question):
    topic = question.strip() or "this"
    return {
        "title": "A Simple Way To Think About It",
        "explanation": (
            f"{topic} can be understood by looking at the small steps that happen "
            "one after another."
        ),
        "steps": [
            "First, something starts the process.",
            "Next, the main parts begin to work together.",
            "Then, the parts make a change we can notice.",
            "Finally, we see the result.",
        ],
        "big_idea": "Big things are easier to understand in small steps.",
        "pencil_sketch_prompt": (
            "pencil sketch diagram showing a simple four step process, arrows, "
            "friendly labels, black and white, educational"
        ),
    }


def fallback_lesson_plan(question):
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


def placeholder_image_data_uri():
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
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def validate_answer(answer):
    data = answer.model_dump()
    steps = data.get("steps", [])

    if len(steps) != 4:
        raise ValueError("The answer did not include exactly 4 steps.")

    data["steps"] = [step.strip() for step in steps]
    return data


def validate_lesson_plan(lesson):
    data = lesson.model_dump()

    if len(data["narration_lines"]) != 5:
        raise ValueError("The lesson did not include exactly 5 narration lines.")

    if len(data["scene_descriptions"]) != 5:
        raise ValueError("The lesson did not include exactly 5 scene descriptions.")

    if len(data["scene_durations"]) != 5:
        raise ValueError("The lesson did not include exactly 5 scene durations.")

    data["narration_lines"] = [line.strip() for line in data["narration_lines"]]
    data["scene_descriptions"] = [
        add_whiteboard_style(description)
        for description in data["scene_descriptions"]
    ]
    data["scene_durations"] = [max(3, int(duration)) for duration in data["scene_durations"]]
    if not 25 <= sum(data["scene_durations"]) <= 35:
        data["scene_durations"] = [6, 6, 6, 6, 6]
    return data


def get_openai_api_key():
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key.strip()

    key_text = ""
    for key_file in API_KEY_FILES:
        if key_file.exists():
            key_text = key_file.read_text(encoding="utf-8").strip()
            break

    if not key_text:
        return None

    if "=" in key_text:
        name, value = key_text.split("=", 1)
        if name.strip() == "OPENAI_API_KEY":
            return value.strip().strip('"').strip("'")

    return key_text.strip().strip('"').strip("'")


def create_openai_client():
    api_key = get_openai_api_key()
    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def generate_kid_answer(question):
    client = create_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if client is None:
        return (
            fallback_answer(question),
            "Add your OpenAI API key to a .env file to generate live answers.",
        )

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Question: {question}",
                },
            ],
            text_format=KidAnswer,
        )
        if response.output_parsed is None:
            raise ValueError("The model did not return a structured answer.")

        return validate_answer(response.output_parsed), None
    except (OpenAIError, ValueError):
        logger.exception("Text generation failed; using fallback answer.")
        return (
            fallback_answer(question),
            "We could not generate a new answer right now, so here is a simple example.",
        )


def generate_lesson_plan(question):
    client = create_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if client is None:
        logger.info("Lesson generation skipped because no OpenAI API key was found.")
        return (
            fallback_lesson_plan(question),
            "Add your OpenAI API key to generate a live animated lesson.",
        )

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": LESSON_SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}"},
            ],
            text_format=AnimationLesson,
        )

        if response.output_parsed is None:
            raise ValueError("The model did not return a structured lesson.")

        return validate_lesson_plan(response.output_parsed), None
    except (OpenAIError, ValueError):
        logger.exception("Lesson generation failed; using fallback lesson.")
        return (
            fallback_lesson_plan(question),
            "We could not generate a fresh lesson right now, so here is a simple example.",
        )


def add_whiteboard_style(prompt):
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

    required_style = (
        "black and white pencil sketch, simple educational diagram for kids, "
        "clean lines, worksheet style"
    )
    return f"{prompt}, {required_style}"


def extract_image_base64(response):
    if not response.data:
        raise ValueError("Image API response had no data items.")

    first_image = response.data[0]
    image_base64 = getattr(first_image, "b64_json", None)

    if not image_base64:
        response_keys = list(first_image.model_dump().keys())
        raise ValueError(
            "Image API response did not include b64_json. "
            f"First data item keys: {response_keys}"
        )

    return image_base64


def generate_sketch_image(pencil_sketch_prompt):
    client = create_openai_client()
    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

    if client is None:
        logger.info("Image generation skipped because no OpenAI API key was found.")
        return {
            "src": placeholder_image_data_uri(),
            "is_placeholder": True,
            "message": "Add your OpenAI API key to generate a sketch image.",
        }

    image_prompt = (
        "Draw a black and white pencil sketch educational diagram for kids ages 6 to 10. "
        "Keep it simple, friendly, clear, and safe. Use simple labels. "
        f"Diagram idea: {pencil_sketch_prompt}"
    )

    try:
        logger.info("Starting image generation with model=%s", model)
        logger.info("Image prompt preview: %s", image_prompt[:500])

        response = client.images.generate(
            model=model,
            prompt=image_prompt,
            size="1024x1024",
            quality="low",
            output_format="png",
            n=1,
        )

        logger.info("Image API returned %s data item(s).", len(response.data or []))
        image_base64 = extract_image_base64(response)
        logger.info("Image base64 length: %s characters.", len(image_base64))

        return {
            "src": f"data:image/png;base64,{image_base64}",
            "is_placeholder": False,
            "message": None,
        }
    except (OpenAIError, ValueError, AttributeError) as error:
        logger.exception("Image generation failed; using placeholder. Error: %s", error)
        return {
            "src": placeholder_image_data_uri(),
            "is_placeholder": True,
            "message": "The sketch could not be generated right now, so here is a placeholder.",
        }


def generate_scene_images(scene_prompts):
    images = []

    for index, scene_prompt in enumerate(scene_prompts, start=1):
        logger.info("Generating scene image %s of %s.", index, len(scene_prompts))
        images.append(generate_sketch_image(add_whiteboard_style(scene_prompt)))

    return images


def generate_audio(narration_lines):
    client = create_openai_client()
    model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    voice = os.getenv("OPENAI_TTS_VOICE", "coral")

    if client is None:
        logger.info("Audio generation skipped because no OpenAI API key was found.")
        return {
            "src": None,
            "message": "Add your OpenAI API key to generate narration audio.",
        }

    narration_text = " ".join(narration_lines)

    try:
        logger.info("Starting TTS generation with model=%s voice=%s", model, voice)
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=narration_text,
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

        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        logger.info("Audio base64 length: %s characters.", len(audio_base64))
        return {
            "src": f"data:audio/mpeg;base64,{audio_base64}",
            "message": None,
        }
    except (OpenAIError, AttributeError, ValueError):
        logger.exception("Audio generation failed; animation will use captions only.")
        return {
            "src": None,
            "message": "Audio could not be generated right now, so captions will guide the lesson.",
        }


@app.route("/", methods=["GET"])
def home():
    examples = [
        "How does rain happen?",
        "How do plants grow?",
        "Why is the sky blue?",
    ]
    return render_template("index.html", examples=examples)


@app.route("/result", methods=["POST"])
def result():
    question = request.form.get("question", "").strip()

    if not question:
        return redirect(url_for("home"))

    answer, error_message = generate_kid_answer(question)
    image = generate_sketch_image(answer["pencil_sketch_prompt"])
    return render_template(
        "result.html",
        question=question,
        answer=answer,
        image=image,
        error_message=error_message,
    )


@app.route("/animation", methods=["POST"])
def animation():
    question = request.form.get("question", "").strip()

    if not question:
        return redirect(url_for("home"))

    lesson, error_message = generate_lesson_plan(question)
    images = generate_scene_images(lesson["scene_descriptions"])
    audio = generate_audio(lesson["narration_lines"])

    scenes = []
    for index, narration in enumerate(lesson["narration_lines"]):
        scenes.append(
            {
                "number": index + 1,
                "narration": narration,
                "description": lesson["scene_descriptions"][index],
                "duration": lesson["scene_durations"][index],
                "image": images[index],
            }
        )

    return render_template(
        "animation.html",
        question=question,
        lesson=lesson,
        scenes=scenes,
        audio=audio,
        error_message=error_message,
    )


if __name__ == "__main__":
    app.run(debug=True)
