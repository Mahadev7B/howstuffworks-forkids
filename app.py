import logging
from pathlib import Path
import random

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for
from sqlalchemy.exc import SQLAlchemyError

from lesson_platform import (
    get_approved_lessons_context,
    get_session,
    handle_question,
    init_db,
    list_lesson_improvements,
    load_settings,
    record_feedback,
    record_improvement,
)


load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = load_settings()
init_db(settings)


def _build_puzzle(kind: str) -> dict:
    puzzle_bank = {
        "pizza": {
            "title": "Pizza Planet Fractions",
            "prompt": "You have 1 whole space pizza. You eat 1/4 and your friend eats 2/4. How much pizza is left?",
            "options": ["1/4", "2/4", "3/4"],
            "answer": "1/4",
            "explanation": "1/4 + 2/4 = 3/4 eaten, so 1/4 is left.",
            "image_prompt": "cartoon kids on a spaceship sharing a pizza cut into 4 slices, educational fraction labels, colorful, kid friendly",
        },
        "icecream": {
            "title": "Ice Cream Moon Scoops",
            "prompt": "A cone has 6 scoops. 2 scoops melt in the sun. How many scoops are left?",
            "options": ["3", "4", "5"],
            "answer": "4",
            "explanation": "6 - 2 = 4 scoops left.",
            "image_prompt": "cartoon ice cream cone with 6 scoops on the moon, 2 scoops melting, numbers for kids, colorful, educational",
        },
    }
    if kind not in puzzle_bank:
        kind = random.choice(list(puzzle_bank.keys()))
    return puzzle_bank[kind] | {"kind": kind}


@app.route("/", methods=["GET"])
def home():
    examples = [
        "How does rain happen?",
        "How is rain formed?",
        "Why do plants need sunlight?",
    ]
    return render_template("index.html", examples=examples)


@app.route("/puzzle", methods=["POST"])
def puzzle():
    kind = request.form.get("kind", "").strip().lower()
    puzzle_data = _build_puzzle(kind)

    return render_template(
        "puzzle.html",
        puzzle=puzzle_data,
    )


@app.route("/animation", methods=["POST"])
def animation():
    question = request.form.get("question", "").strip()
    above_second = request.form.get("above_second", "").strip().lower() in {"yes", "true", "1", "on"}
    if not question:
        return redirect(url_for("home"))

    session = get_session()
    try:
        response = handle_question(question, session, settings)
    finally:
        session.close()

    lesson_payload = response.response_payload
    scenes = lesson_payload.get("scenes", [])
    lesson_id = lesson_payload.get("lesson_id")
    audio = {
        "src": lesson_payload.get("audio_url"),
        "message": None if lesson_payload.get("audio_url") else "Audio is unavailable for this lesson, so captions are guiding the lesson.",
    }
    improvements = []
    session = get_session()
    try:
        improvements = list_lesson_improvements(session=session, lesson_id=lesson_id, limit=10)
    finally:
        session.close()

    return render_template(
        "animation.html",
        question=question,
        lesson={
            "id": lesson_id,
            "title": lesson_payload.get("title"),
            "big_idea": lesson_payload.get("big_idea"),
        },
        scenes=scenes,
        audio=audio,
        above_second=above_second,
        improvements=improvements,
        error_message=" ".join(response.messages) if response.messages else None,
        reused=response.reused,
        similarity_score=round(response.similarity_score, 3),
        request_time_ms=response.request_time_ms,
        generation_time_ms=response.generation_time_ms,
        estimated_api_cost=response.estimated_api_cost,
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    lesson_id = request.form.get("lesson_id", type=int)
    feedback_type = request.form.get("feedback_type", "").strip().lower()
    completion_rate = request.form.get("watch_completion_rate", type=float)

    if not lesson_id:
        return jsonify({"ok": False, "error": "lesson_id is required"}), 400

    helpful = feedback_type == "helpful"
    confusing = feedback_type == "confusing"

    session = get_session()
    response_payload = None
    try:
        try:
            feedback_row = record_feedback(
                session=session,
                lesson_id=lesson_id,
                helpful=helpful,
                confusing=confusing,
                watch_completion_rate=completion_rate,
            )
        except SQLAlchemyError:
            logger.exception("Failed to persist feedback for lesson_id=%s", lesson_id)
            session.rollback()
            return jsonify({"ok": False, "error": "database error while saving feedback"}), 500

        if feedback_row is None:
            return jsonify({"ok": False, "error": "lesson not found"}), 404

        response_payload = {
            "ok": True,
            "helpful_votes": feedback_row.helpful_votes,
            "confusing_votes": feedback_row.confusing_votes,
            "replay_count": feedback_row.replay_count,
            "watch_completion_rate": feedback_row.watch_completion_rate,
        }
    finally:
        session.close()

    return jsonify(response_payload)


@app.route("/replay", methods=["POST"])
def replay():
    lesson_id = request.form.get("lesson_id", type=int)
    if not lesson_id:
        return jsonify({"ok": False, "error": "lesson_id is required"}), 400

    session = get_session()
    response_payload = None
    try:
        try:
            feedback_row = record_feedback(session=session, lesson_id=lesson_id, replay_increment=1)
        except SQLAlchemyError:
            logger.exception("Failed to persist replay for lesson_id=%s", lesson_id)
            session.rollback()
            return jsonify({"ok": False, "error": "database error while saving replay"}), 500

        if feedback_row is None:
            return jsonify({"ok": False, "error": "lesson not found"}), 404

        response_payload = {"ok": True, "replay_count": feedback_row.replay_count}
    finally:
        session.close()

    return jsonify(response_payload)


@app.route("/improvement", methods=["POST"])
def improvement():
    lesson_id = request.form.get("lesson_id", type=int)
    question = request.form.get("question", "").strip()
    category = request.form.get("category", "").strip().lower() or "general"
    comment_text = request.form.get("comment_text", "").strip()

    if not comment_text:
        return jsonify({"ok": False, "error": "comment_text is required"}), 400

    valid_categories = {"general", "spelling", "timing", "visuals", "voice"}
    if category not in valid_categories:
        category = "general"

    session = get_session()
    response_payload = None
    try:
        try:
            improvement_row = record_improvement(
                session=session,
                lesson_id=lesson_id,
                raw_question=question or "unknown",
                category=category,
                comment_text=comment_text,
            )
        except SQLAlchemyError:
            logger.exception("Failed to save improvement for lesson_id=%s", lesson_id)
            session.rollback()
            return jsonify({"ok": False, "error": "database error while saving improvement"}), 500

        response_payload = {
            "ok": True,
            "id": improvement_row.id,
            "category": improvement_row.category,
            "comment_text": improvement_row.comment_text,
            "status": improvement_row.status,
            "created_at": improvement_row.created_at.isoformat(),
        }
    finally:
        session.close()

    return jsonify(response_payload)


@app.route("/approved-context", methods=["GET"])
def approved_context():
    intent = request.args.get("intent")
    visual_type = request.args.get("visual_type")
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, 50))

    session = get_session()
    try:
        rows = get_approved_lessons_context(
            session=session,
            limit=limit,
            intent=intent,
            visual_type=visual_type,
        )
    finally:
        session.close()
    return jsonify({"rows": rows})


@app.route("/media/<path:relative_path>", methods=["GET"])
def media_file(relative_path: str):
    media_root = Path(settings.media_storage_path).resolve()
    absolute_path = (media_root / relative_path).resolve()
    if media_root not in absolute_path.parents and absolute_path != media_root:
        return jsonify({"ok": False, "error": "invalid path"}), 400
    if not absolute_path.exists():
        return jsonify({"ok": False, "error": "not found"}), 404
    return send_from_directory(media_root, relative_path)


if __name__ == "__main__":
    app.run(debug=True)
