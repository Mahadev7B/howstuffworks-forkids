import logging
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for

from lesson_platform import get_approved_lessons_context, get_session, handle_question, init_db, load_settings, record_feedback


load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = load_settings()
init_db(settings)


@app.route("/", methods=["GET"])
def home():
    examples = [
        "How does rain happen?",
        "How is rain formed?",
        "Why do plants need sunlight?",
    ]
    return render_template("index.html", examples=examples)


@app.route("/animation", methods=["POST"])
def animation():
    question = request.form.get("question", "").strip()
    if not question:
        return redirect(url_for("home"))

    session = get_session()
    try:
        response = handle_question(question, session, settings)
    finally:
        session.close()

    lesson_payload = response.response_payload
    scenes = lesson_payload.get("scenes", [])
    audio = {
        "src": lesson_payload.get("audio_url"),
        "message": None if lesson_payload.get("audio_url") else "Audio is unavailable for this lesson, so captions are guiding the lesson.",
    }

    return render_template(
        "animation.html",
        question=question,
        lesson={
            "id": lesson_payload.get("lesson_id"),
            "title": lesson_payload.get("title"),
            "big_idea": lesson_payload.get("big_idea"),
        },
        scenes=scenes,
        audio=audio,
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
    try:
        feedback_row = record_feedback(
            session=session,
            lesson_id=lesson_id,
            helpful=helpful,
            confusing=confusing,
            watch_completion_rate=completion_rate,
        )
    finally:
        session.close()

    if feedback_row is None:
        return jsonify({"ok": False, "error": "lesson not found"}), 404

    return jsonify(
        {
            "ok": True,
            "helpful_votes": feedback_row.helpful_votes,
            "confusing_votes": feedback_row.confusing_votes,
            "replay_count": feedback_row.replay_count,
            "watch_completion_rate": feedback_row.watch_completion_rate,
        }
    )


@app.route("/replay", methods=["POST"])
def replay():
    lesson_id = request.form.get("lesson_id", type=int)
    if not lesson_id:
        return jsonify({"ok": False, "error": "lesson_id is required"}), 400

    session = get_session()
    try:
        feedback_row = record_feedback(session=session, lesson_id=lesson_id, replay_increment=1)
    finally:
        session.close()

    if feedback_row is None:
        return jsonify({"ok": False, "error": "lesson not found"}), 404

    return jsonify({"ok": True, "replay_count": feedback_row.replay_count})


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
