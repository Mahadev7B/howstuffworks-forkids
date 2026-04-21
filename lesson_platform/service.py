import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from .ai_generation import create_openai_client, generate_audio, generate_lesson_plan, generate_scene_images
from .config import Settings
from .media_store import save_media_file
from .models import (
    Lesson,
    LessonFeedback,
    LessonImprovement,
    LessonMedia,
    LessonRequest,
    QuestionVariant,
)
from .question_processing import classify_question, normalize_question
from .semantic import (
    compute_embedding,
    find_similar_lesson as find_semantic_match,
    should_reuse_lesson,
)


logger = logging.getLogger(__name__)


@dataclass
class LessonResponse:
    lesson: Lesson
    response_payload: dict
    reused: bool
    similarity_score: float
    messages: list[str]
    request_time_ms: int
    generation_time_ms: int
    estimated_api_cost: float


def _utcnow():
    return datetime.now(timezone.utc)


def _meaning_group_id(intent: str, visual_type: str, normalized_question: str) -> str:
    return f"{intent}:{visual_type}:{normalized_question[:80]}"


def _media_url(file_path: str) -> str:
    return f"/media/{file_path}"


def _extract_spelling_fixes(improvement_notes: list[str]) -> list[tuple[str, str]]:
    fixes: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    arrow_pattern = re.compile(r"([A-Za-z][A-Za-z' -]{1,40})\s*(?:->|=>|→)\s*([A-Za-z][A-Za-z' -]{1,40})")
    replace_pattern = re.compile(
        r"replace\s+['\"]?([A-Za-z][A-Za-z' -]{1,40})['\"]?\s+with\s+['\"]?([A-Za-z][A-Za-z' -]{1,40})['\"]?",
        re.IGNORECASE,
    )

    for note in improvement_notes:
        for pattern in (arrow_pattern, replace_pattern):
            for match in pattern.findall(note):
                wrong = " ".join(match[0].strip().split())
                correct = " ".join(match[1].strip().split())
                if wrong.lower() == correct.lower():
                    continue
                key = (wrong.lower(), correct)
                if key in seen:
                    continue
                seen.add(key)
                fixes.append((wrong, correct))
    return fixes


def _apply_spelling_fixes(text: str, fixes: list[tuple[str, str]]) -> str:
    updated = text
    for wrong, correct in fixes:
        pattern = re.compile(rf"\b{re.escape(wrong)}\b", flags=re.IGNORECASE)
        updated = pattern.sub(correct, updated)
    return updated


def _apply_spelling_fixes_to_lesson(lesson_data: dict, fixes: list[tuple[str, str]]) -> dict:
    if not fixes:
        return lesson_data

    lesson_data["title"] = _apply_spelling_fixes(lesson_data.get("title", ""), fixes)
    lesson_data["big_idea"] = _apply_spelling_fixes(lesson_data.get("big_idea", ""), fixes)
    lesson_data["narration_lines"] = [_apply_spelling_fixes(line, fixes) for line in lesson_data["narration_lines"]]
    lesson_data["scene_descriptions"] = [
        _apply_spelling_fixes(desc, fixes) for desc in lesson_data["scene_descriptions"]
    ]
    return lesson_data


def _get_recent_improvement_notes(*, session, limit: int = 25) -> list[str]:
    rows = session.execute(
        select(LessonImprovement)
        .order_by(LessonImprovement.created_at.desc())
        .limit(limit)
    ).scalars()
    return [row.comment_text for row in rows if row.comment_text]


def save_lesson(
    *,
    session,
    question: str,
    normalized_question: str,
    intent: str,
    visual_type: str,
    lesson_data: dict,
    image_refs: list[str],
    audio_ref: Optional[str],
    generation_time_ms: int,
    estimated_api_cost: float,
) -> Lesson:
    scenes = []
    for index, narration in enumerate(lesson_data["narration_lines"]):
        scenes.append(
            {
                "number": index + 1,
                "narration": narration,
                "description": lesson_data["scene_descriptions"][index],
                "duration": lesson_data["scene_durations"][index],
                "image_url": _media_url(image_refs[index]),
            }
        )

    lesson_json = {
        "title": lesson_data["title"],
        "question": question,
        "big_idea": lesson_data["big_idea"],
        "scenes": scenes,
        "audio_url": _media_url(audio_ref) if audio_ref else None,
    }

    lesson = Lesson(
        canonical_title=lesson_data["title"],
        topic=normalized_question.split(" ")[0] if normalized_question else "general",
        intent=intent,
        visual_type=visual_type,
        meaning_group_id=_meaning_group_id(intent, visual_type, normalized_question),
        explanation=" ".join(lesson_data["narration_lines"]),
        big_idea=lesson_data["big_idea"],
        steps_json=lesson_data["narration_lines"][:4],
        narration_json=lesson_data["narration_lines"],
        scenes_json=scenes,
        lesson_json=lesson_json,
        approved_flag=False,
        regeneration_needed_flag=False,
        helpful_score=0.0,
        replay_count=0,
        reuse_count=0,
        generation_time_ms=generation_time_ms,
        estimated_api_cost=estimated_api_cost,
        last_used_at=_utcnow(),
    )
    session.add(lesson)
    session.flush()

    for image_ref in image_refs:
        session.add(
            LessonMedia(
                lesson_id=lesson.id,
                media_type="image",
                file_path=image_ref,
                thumbnail_path=None,
            )
        )

    if audio_ref:
        session.add(
            LessonMedia(
                lesson_id=lesson.id,
                media_type="audio",
                file_path=audio_ref,
                thumbnail_path=None,
            )
        )

    session.add(
        LessonFeedback(
            lesson_id=lesson.id,
            helpful_votes=0,
            confusing_votes=0,
            replay_count=0,
            watch_completion_rate=0.0,
        )
    )
    session.flush()
    return lesson


def save_question_variant(
    *,
    session,
    lesson_id: int,
    raw_question: str,
    normalized_question: str,
    embedding: list[float],
    intent: str,
    visual_type: str,
) -> QuestionVariant:
    variant = QuestionVariant(
        lesson_id=lesson_id,
        raw_question=raw_question,
        normalized_question=normalized_question,
        embedding=embedding,
        intent=intent,
        visual_type=visual_type,
        last_used_at=_utcnow(),
    )
    session.add(variant)
    session.flush()
    return variant


def find_similar_lesson(
    *,
    session,
    normalized_question: str,
    intent: str,
    visual_type: str,
    query_embedding: list[float],
    similarity_threshold: float,
) -> tuple[Optional[Lesson], Optional[QuestionVariant], float]:
    candidates = session.execute(
        select(QuestionVariant)
        .options(joinedload(QuestionVariant.lesson))
        .where(QuestionVariant.intent == intent, QuestionVariant.visual_type == visual_type)
    ).scalars()
    return find_semantic_match(
        variants=candidates,
        query_embedding=query_embedding,
        similarity_threshold=similarity_threshold,
    )


def generate_new_lesson(
    *,
    question: str,
    normalized_question: str,
    intent: str,
    visual_type: str,
    query_embedding: list[float],
    session,
    settings: Settings,
) -> tuple[Lesson, dict, list[str], int, float]:
    client = create_openai_client(settings)
    improvement_notes = _get_recent_improvement_notes(session=session)
    lesson_data, lesson_message, lesson_ms, lesson_cost = generate_lesson_plan(
        question, settings, client, improvement_notes=improvement_notes
    )
    spelling_fixes = _extract_spelling_fixes(improvement_notes)
    lesson_data = _apply_spelling_fixes_to_lesson(lesson_data, spelling_fixes)

    with ThreadPoolExecutor(max_workers=2) as executor:
        image_future = executor.submit(
            generate_scene_images, lesson_data["scene_descriptions"], settings, client
        )
        audio_future = executor.submit(
            generate_audio, lesson_data["narration_lines"], settings, client
        )
        image_results, image_messages, image_ms, image_cost = image_future.result()
        audio_result, audio_message, audio_ms, audio_cost = audio_future.result()

    image_refs = [
        save_media_file(settings.media_storage_path, media_type="image", ext=image.ext, content=image.content)
        for image in image_results
    ]
    audio_ref = None
    if audio_result:
        audio_ref = save_media_file(
            settings.media_storage_path,
            media_type="audio",
            ext=audio_result.ext,
            content=audio_result.content,
        )

    generation_time_ms = lesson_ms + image_ms + audio_ms
    estimated_api_cost = lesson_cost + image_cost + audio_cost
    logger.info(
        "generation_breakdown_ms lesson=%s images=%s audio=%s total=%s notes=%s fixes=%s",
        lesson_ms,
        image_ms,
        audio_ms,
        generation_time_ms,
        len(improvement_notes),
        len(spelling_fixes),
    )

    lesson = save_lesson(
        session=session,
        question=question,
        normalized_question=normalized_question,
        intent=intent,
        visual_type=visual_type,
        lesson_data=lesson_data,
        image_refs=image_refs,
        audio_ref=audio_ref,
        generation_time_ms=generation_time_ms,
        estimated_api_cost=estimated_api_cost,
    )

    save_question_variant(
        session=session,
        lesson_id=lesson.id,
        raw_question=question,
        normalized_question=normalized_question,
        embedding=query_embedding,
        intent=intent,
        visual_type=visual_type,
    )

    messages = [msg for msg in [lesson_message, audio_message] if msg]
    messages.extend(image_messages)
    return lesson, _build_lesson_payload(lesson), messages, generation_time_ms, estimated_api_cost


def _build_lesson_payload(lesson: Lesson) -> dict:
    payload = json.loads(json.dumps(lesson.lesson_json))
    payload.setdefault("audio_url", None)
    payload.setdefault("scenes", [])
    payload["lesson_id"] = lesson.id
    return payload


def _media_exists(media_storage_path: str, media_url: str) -> bool:
    if not media_url or not media_url.startswith("/media/"):
        return False
    relative_path = media_url[len("/media/") :]
    media_root = Path(media_storage_path).resolve()
    candidate = (media_root / relative_path).resolve()
    if media_root not in candidate.parents and candidate != media_root:
        return False
    return candidate.exists()


def _lesson_has_reusable_media(lesson: Lesson, settings: Settings) -> bool:
    payload = _build_lesson_payload(lesson)
    scenes = payload.get("scenes", [])
    if not scenes:
        return False

    for scene in scenes:
        image_url = scene.get("image_url")
        if not _media_exists(settings.media_storage_path, image_url):
            return False

    audio_url = payload.get("audio_url")
    if audio_url and not _media_exists(settings.media_storage_path, audio_url):
        return False

    return True


def handle_question(question: str, session, settings: Settings) -> LessonResponse:
    started = time.perf_counter()
    normalized_question = normalize_question(question)
    intent, visual_type = classify_question(question)
    client = create_openai_client(settings)
    embedding_started = time.perf_counter()
    query_embedding = compute_embedding(normalized_question, settings.openai_embedding_model, client)
    embedding_ms = int((time.perf_counter() - embedding_started) * 1000)

    semantic_started = time.perf_counter()
    matched_lesson, matched_variant, similarity_score = find_similar_lesson(
        session=session,
        normalized_question=normalized_question,
        intent=intent,
        visual_type=visual_type,
        query_embedding=query_embedding,
        similarity_threshold=settings.similarity_threshold,
    )
    semantic_ms = int((time.perf_counter() - semantic_started) * 1000)

    if should_reuse_lesson(
        lesson=matched_lesson,
        similarity_score=similarity_score,
        similarity_threshold=settings.similarity_threshold,
        intent=intent,
        visual_type=visual_type,
    ) and _lesson_has_reusable_media(matched_lesson, settings):
        lesson = matched_lesson
        lesson.reuse_count += 1
        lesson.last_used_at = _utcnow()
        if matched_variant:
            matched_variant.last_used_at = _utcnow()

        save_question_variant(
            session=session,
            lesson_id=lesson.id,
            raw_question=question,
            normalized_question=normalized_question,
            embedding=query_embedding,
            intent=intent,
            visual_type=visual_type,
        )
        response_payload = _build_lesson_payload(lesson)
        generation_time_ms = 0
        estimated_api_cost = 0.0
        reused = True
        messages = []
    else:
        lesson, response_payload, messages, generation_time_ms, estimated_api_cost = generate_new_lesson(
            question=question,
            normalized_question=normalized_question,
            intent=intent,
            visual_type=visual_type,
            query_embedding=query_embedding,
            session=session,
            settings=settings,
        )
        lesson.last_used_at = _utcnow()
        reused = False

    request_time_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "request_timing_ms total=%s embedding=%s semantic=%s reused=%s generation=%s",
        request_time_ms,
        embedding_ms,
        semantic_ms,
        reused,
        generation_time_ms,
    )
    session.add(
        LessonRequest(
            lesson_id=lesson.id,
            raw_question=question,
            normalized_question=normalized_question,
            intent=intent,
            visual_type=visual_type,
            reused_flag=reused,
            request_time_ms=request_time_ms,
            generation_time_ms=generation_time_ms,
            estimated_api_cost=estimated_api_cost,
        )
    )
    session.commit()

    return LessonResponse(
        lesson=lesson,
        response_payload=response_payload,
        reused=reused,
        similarity_score=max(similarity_score, 0.0),
        messages=messages,
        request_time_ms=request_time_ms,
        generation_time_ms=generation_time_ms,
        estimated_api_cost=estimated_api_cost,
    )


def record_feedback(
    *,
    session,
    lesson_id: int,
    helpful: bool = False,
    confusing: bool = False,
    replay_increment: int = 0,
    watch_completion_rate: Optional[float] = None,
) -> Optional[LessonFeedback]:
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        return None

    feedback = session.execute(
        select(LessonFeedback).where(LessonFeedback.lesson_id == lesson_id)
    ).scalar_one_or_none()
    if feedback is None:
        feedback = LessonFeedback(lesson_id=lesson_id)
        session.add(feedback)
        session.flush()

    if helpful:
        feedback.helpful_votes += 1
    if confusing:
        feedback.confusing_votes += 1
    if replay_increment:
        feedback.replay_count += replay_increment
        lesson.replay_count += replay_increment
    if watch_completion_rate is not None:
        feedback.watch_completion_rate = max(0.0, min(1.0, watch_completion_rate))

    total_votes = feedback.helpful_votes + feedback.confusing_votes
    lesson.helpful_score = (
        0.0 if total_votes == 0 else feedback.helpful_votes / float(total_votes)
    )
    lesson.updated_at = _utcnow()
    session.commit()
    return feedback


def record_improvement(
    *,
    session,
    lesson_id: Optional[int],
    raw_question: str,
    category: str,
    comment_text: str,
) -> LessonImprovement:
    improvement = LessonImprovement(
        lesson_id=lesson_id,
        raw_question=raw_question,
        category=(category or "general").strip().lower(),
        comment_text=comment_text.strip(),
        status="received",
    )
    session.add(improvement)
    session.commit()
    return improvement


def list_lesson_improvements(
    *,
    session,
    lesson_id: Optional[int],
    limit: int = 20,
) -> list[dict]:
    query = select(LessonImprovement).order_by(LessonImprovement.created_at.desc()).limit(limit)
    if lesson_id:
        query = query.where(LessonImprovement.lesson_id == lesson_id)

    rows = session.execute(query).scalars()
    return [
        {
            "id": row.id,
            "category": row.category,
            "comment_text": row.comment_text,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def get_approved_lessons_context(
    *,
    session,
    limit: int = 10,
    intent: Optional[str] = None,
    visual_type: Optional[str] = None,
) -> list[dict]:
    query = select(Lesson).where(
        Lesson.approved_flag.is_(True),
        Lesson.regeneration_needed_flag.is_(False),
    )
    if intent:
        query = query.where(Lesson.intent == intent)
    if visual_type:
        query = query.where(Lesson.visual_type == visual_type)

    lessons = session.execute(
        query.order_by(Lesson.last_used_at.desc()).limit(limit)
    ).scalars()

    contexts = []
    for lesson in lessons:
        contexts.append(
            {
                "lesson_id": lesson.id,
                "title": lesson.canonical_title,
                "intent": lesson.intent,
                "visual_type": lesson.visual_type,
                "big_idea": lesson.big_idea,
                "content": lesson.explanation,
            }
        )
    return contexts
