from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    intent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    visual_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    meaning_group_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    big_idea: Mapped[str] = mapped_column(Text, nullable=False)
    steps_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    narration_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    scenes_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    lesson_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    approved_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    regeneration_needed_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    helpful_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    replay_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reuse_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_api_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    variants: Mapped[list["QuestionVariant"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    media_items: Mapped[list["LessonMedia"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    feedback_records: Mapped[list["LessonFeedback"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")


class QuestionVariant(Base):
    __tablename__ = "question_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_question: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_question: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    embedding: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    intent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    visual_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    lesson: Mapped[Lesson] = relationship(back_populates="variants")


class LessonMedia(Base):
    __tablename__ = "lesson_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    lesson: Mapped[Lesson] = relationship(back_populates="media_items")


class LessonFeedback(Base):
    __tablename__ = "lesson_feedback"
    __table_args__ = (UniqueConstraint("lesson_id", name="uq_lesson_feedback_lesson_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    helpful_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confusing_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replay_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watch_completion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    lesson: Mapped[Lesson] = relationship(back_populates="feedback_records")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    visual_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    layout_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class LessonRequest(Base):
    __tablename__ = "lesson_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    raw_question: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_question: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    intent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    visual_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    reused_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    request_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_api_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
