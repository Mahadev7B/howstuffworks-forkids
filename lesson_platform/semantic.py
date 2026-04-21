import hashlib
import math
from typing import Iterable, List, Optional

from openai import OpenAI, OpenAIError

from .models import Lesson, QuestionVariant


def _token_hash_vector(text: str, size: int = 128) -> List[float]:
    vector = [0.0] * size
    tokens = text.split()
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], byteorder="big") % size
        vector[index] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(vec_a: Iterable[float], vec_b: Iterable[float]) -> float:
    a = list(vec_a)
    b = list(vec_b)
    if len(a) != len(b) or not a:
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def compute_embedding(
    text: str,
    embedding_model: str,
    openai_client: Optional[OpenAI],
) -> List[float]:
    if not text:
        return _token_hash_vector(text)

    if openai_client is None:
        return _token_hash_vector(text)

    try:
        response = openai_client.embeddings.create(model=embedding_model, input=text)
        if not response.data:
            return _token_hash_vector(text)
        return list(response.data[0].embedding)
    except (OpenAIError, AttributeError, TypeError, ValueError):
        return _token_hash_vector(text)


def find_similar_lesson(
    *,
    variants: Iterable[QuestionVariant],
    query_embedding: List[float],
    similarity_threshold: float,
) -> tuple[Optional[Lesson], Optional[QuestionVariant], float]:
    best_lesson = None
    best_variant = None
    best_score = -1.0

    for variant in variants:
        if not variant.embedding:
            continue
        score = cosine_similarity(query_embedding, variant.embedding)
        if score > best_score:
            best_score = score
            best_lesson = variant.lesson
            best_variant = variant

    if best_lesson is None or best_score < similarity_threshold:
        return None, None, best_score

    return best_lesson, best_variant, best_score


def should_reuse_lesson(
    *,
    lesson: Optional[Lesson],
    similarity_score: float,
    similarity_threshold: float,
    intent: str,
    visual_type: str,
) -> bool:
    if lesson is None:
        return False
    if lesson.regeneration_needed_flag:
        return False
    if lesson.intent != intent or lesson.visual_type != visual_type:
        return False
    return similarity_score >= similarity_threshold
