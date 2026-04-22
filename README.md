# How It Works Kids: Data-Driven Lesson Platform

Flask app for generating and reusing kid-friendly lessons with PostgreSQL persistence, semantic matching, feedback tracking, and media references stored outside the database.

## What Changed

The app now:

1. Stores generated lessons in PostgreSQL.
2. Stores question variants with normalized text, intent, visual type, and embedding.
3. Reuses existing lessons only when semantic similarity is high and intent + visual type match.
4. Generates a new lesson only when no safe reusable match is found.
5. Saves image/audio files to filesystem storage and stores only file references in DB.
6. Tracks request analytics, replay count, and helpful/confusing feedback.

## Main Flow

When a question is submitted:

1. `normalize_question()` standardizes text.
2. `classify_question()` derives `intent` and `visual_type`.
3. Embedding is computed for the normalized question.
4. Candidate question variants are filtered by `intent` and `visual_type`.
5. Semantic similarity is computed.
6. If similarity >= `SIMILARITY_THRESHOLD` and lesson is valid, reuse path is used.
7. Otherwise, a new lesson and media are generated and persisted.
8. Request analytics are stored in `lesson_requests`.

## Project Structure

```text
.
├── app.py
├── lesson_platform/
│   ├── __init__.py
│   ├── ai_generation.py
│   ├── config.py
│   ├── db.py
│   ├── media_store.py
│   ├── models.py
│   ├── question_processing.py
│   ├── semantic.py
│   └── service.py
├── templates/
│   ├── animation.html
│   └── index.html
├── static/
│   └── style.css
├── requirements.txt
└── .env.example
```

## Database Schema

### `lessons`

`id`, `canonical_title`, `topic`, `intent`, `visual_type`, `meaning_group_id`, `explanation`, `big_idea`, `steps_json`, `narration_json`, `scenes_json`, `lesson_json`, `approved_flag`, `regeneration_needed_flag`, `helpful_score`, `replay_count`, `reuse_count`, `generation_time_ms`, `estimated_api_cost`, `created_at`, `updated_at`, `last_used_at`

### `question_variants`

`id`, `lesson_id`, `raw_question`, `normalized_question`, `embedding`, `intent`, `visual_type`, `created_at`, `last_used_at`

### `lesson_media`

`id`, `lesson_id`, `media_type`, `file_path`, `thumbnail_path`, `created_at`

### `lesson_feedback`

`id`, `lesson_id`, `helpful_votes`, `confusing_votes`, `replay_count`, `watch_completion_rate`, `created_at`, `updated_at`

### `templates`

`id`, `template_name`, `visual_type`, `description`, `layout_json`, `active_flag`, `created_at`

### `lesson_requests` (analytics helper table)

`id`, `lesson_id`, `raw_question`, `normalized_question`, `intent`, `visual_type`, `reused_flag`, `request_time_ms`, `generation_time_ms`, `estimated_api_cost`, `created_at`

## Environment Variables

Required:

- `DATABASE_URL` (PostgreSQL connection string)
- `OPENAI_API_KEY`

Recommended:

- `OPENAI_MODEL` (default `gpt-4.1-mini`)
- `OPENAI_IMAGE_MODEL` (default `gpt-image-1`)
- `OPENAI_TTS_MODEL` (default `gpt-4o-mini-tts`)
- `OPENAI_TTS_VOICE` (default `coral`)
- `OPENAI_EMBEDDING_MODEL` (default `text-embedding-3-small`)
- `SIMILARITY_THRESHOLD` (default `0.84`)
- `MEDIA_STORAGE_PATH` (default `media_store`)
- `LESSON_TIMEOUT_SECONDS` (default `180`)
- `IMAGE_PARALLELISM` (default `3`)
- `MAX_GENERATED_IMAGES` (default `5`) limits paid image calls per lesson to control cost
- `IMAGE_SIZE` (default `auto`; supported: `auto`, `1024x1024`, `1024x1536`, `1536x1024`)
- `AUDIO_ENABLED` (default `true`)
- `LOCAL_MEDIA_ONLY` (default `false`) generate all scene sketches in Python with no image API calls
- `LOCAL_TTS_ENABLED` (default `false`) attempt narration via local Python TTS (`pyttsx3`)

## Setup Steps

1. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

2. Create `.env`:

```powershell
copy .env.example .env
```

3. Update `.env` with real values, especially `DATABASE_URL` and `OPENAI_API_KEY`.

4. Ensure PostgreSQL exists and the database in `DATABASE_URL` is created.

5. Run the app:

```powershell
python app.py
```

6. Open:

```text
http://127.0.0.1:5000
```

Notes:

- Tables are initialized automatically on startup (`Base.metadata.create_all`).
- For production migrations, switch to Alembic later; current setup is bootstrap-friendly for initial rollout.

## Render Deployment

Use:

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 180`

Set Render environment variables:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_IMAGE_MODEL`
- `OPENAI_TTS_MODEL`
- `OPENAI_TTS_VOICE`
- `OPENAI_EMBEDDING_MODEL`
- `SIMILARITY_THRESHOLD`
- `MEDIA_STORAGE_PATH`
- `IMAGE_PARALLELISM`
- `MAX_GENERATED_IMAGES`
- `IMAGE_SIZE`
- `AUDIO_ENABLED`
- `LOCAL_MEDIA_ONLY`
- `LOCAL_TTS_ENABLED`

## API / Endpoints

- `GET /` home page
- `POST /animation` lesson generation/reuse path
- `POST /feedback` helpful/confusing and completion updates
- `POST /replay` replay tracking
- `GET /media/<path>` media file serving
- `GET /approved-context` approved lesson retrieval for future RAG pipeline

## Reuse Safety Rules

A lesson is reused only when:

1. `intent` matches.
2. `visual_type` matches.
3. semantic similarity score is above `SIMILARITY_THRESHOLD`.
4. lesson is not flagged for regeneration.

This prevents false reuse cases like health/safety questions reusing process-explanation lessons.

## Speed Tuning

For faster first response:

1. Increase parallel image generation:
   - `IMAGE_PARALLELISM=3` (or `4` if stable for your plan)
2. Use smaller images:
   - `IMAGE_SIZE=auto`
3. Disable audio generation when low latency matters:
   - `AUDIO_ENABLED=false`
