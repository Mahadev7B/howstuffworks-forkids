# How It Works Kids

A simple Flask MVP for a kids educational AI app with a whiteboard-style animation mode.

Children or parents can ask questions like:

- How does rain happen?
- How do plants grow?
- Why is the sky blue?

The app can generate:

- A short animated lesson plan for kids ages 6 to 10
- 5 narration lines
- 5 matching pencil-sketch scenes
- 5 scene durations totaling about 30 seconds
- A one-line big idea
- Optional AI narration audio

## Project structure

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── static/
│   └── style.css
└── templates/
    ├── animation.html
    ├── index.html
    └── result.html
```

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```powershell
copy .env.example .env
```

Open `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_real_api_key_here
OPENAI_MODEL=gpt-4.1-mini
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=coral
```

You can also place the key in this local file:

```text
bash/env/API_KEY
```

The app also accepts this filename:

```text
bash/env/API KEY.txt
```

That file can contain either the raw key:

```text
sk-your-key-here
```

or:

```env
OPENAI_API_KEY=sk-your-key-here
```

## Run the app

```powershell
python app.py
```

Open the local site:

```text
http://127.0.0.1:5000
```

## How animation timing works

The backend asks OpenAI for exactly 5 scene durations. Each duration is in seconds and the total should be close to 30 seconds.

The `/animation` page uses JavaScript timers:

- Scene 1 appears first.
- The timer waits for scene 1 duration.
- The page fades to scene 2.
- This continues through all 5 scenes.
- The caption changes with each scene.
- The audio starts when the user clicks `Start lesson`.

If audio is unavailable, the same animation still runs with captions.

## API usage

The API key is used only on the Flask server.

- Lesson plan text: `OPENAI_MODEL`
- Scene images: `OPENAI_IMAGE_MODEL`
- Narration audio: `OPENAI_TTS_MODEL` and `OPENAI_TTS_VOICE`

Do not put API keys in HTML, CSS, or JavaScript.

## Notes

- Secrets are loaded from environment variables or the local key file fallback.
- Do not commit your `.env` file or local API key file.
- If lesson generation fails, the app shows a simple fallback lesson.
- If image generation fails, the app displays a placeholder image for that scene.
- If audio generation fails, the animation still plays with captions.
