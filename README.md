# AI Study Companion

An AI study tool that turns your notes into active recall practice. Paste in your notes, and the app retrieves the most relevant passages, generates Socratic follow-up questions with an LLM, judges your answers, and schedules reviews with a spaced repetition algorithm (SM-2) so weak topics come back sooner.

## Features

- **Note ingestion**: paste text notes, which are split into paragraph-based chunks
- **Semantic retrieval**: chunks are embedded with OpenAI `text-embedding-3-small` and matched to a topic by cosine similarity
- **Socratic questions**: an LLM generates a follow-up question from the retrieved chunk
- **Answer judging**: the LLM evaluates your answer
- **Spaced repetition**: a simplified SM-2 scheduler doubles the review interval on correct answers and resets it to 1 day on wrong ones
- **Review queue**: a min-heap surfaces the questions that are due, earliest first

## Tech Stack

Python, FastAPI, Streamlit, SQLite, OpenAI API, pytest. Deployed on Render.

## Architecture

```
Streamlit UI (src/app.py)
        │  HTTP
        ▼
FastAPI backend (src/main.py)
        │
  ┌─────┼───────────────┬─────────────────┐
  ▼     ▼               ▼                 ▼
/upload /quiz         /answer           /review
  │      │               │                 │
chunk   retrieve       LLM judges       min-heap of
  │     top chunk      the answer       due questions
embed   (cosine)         │
  │      │             update SM-2
  ▼      ▼             schedule
SQLite + in-memory   SQLite
embedding index      (answers, review_schedule)
```

**Data flow**

1. **Upload**: a note is split into chunks, each chunk is embedded with the OpenAI embeddings API, and the note is saved to SQLite. Embeddings are kept in an in-memory index.
2. **Quiz**: given a topic, the app finds the most similar chunk (cosine similarity), and an LLM turns it into a Socratic follow-up question stored in SQLite.
3. **Answer**: an LLM judges the answer, the result is saved, and the SM-2 scheduler updates the question's next review date.
4. **Review**: questions whose review date is today or earlier are returned, earliest first.

## Getting Started

```bash
git clone https://github.com/Fiona-7788/ai-study-companion.git
cd ai-study-companion
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_key_here
```

The SQLite database is created automatically on first start from `schema.sql`.

Start the backend and the UI in two terminals:

```bash
uvicorn src.main:app --reload
streamlit run src/app.py
```

The API docs are available at `http://127.0.0.1:8000/docs`.

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests cover the SM-2 scheduler (including database updates against an in-memory SQLite), the embedding utilities (cosine similarity and retrieval, with the OpenAI call mocked), and database initialization.

## Deployment

The backend is deployed on Render: https://ai-study-companion-604v.onrender.com/docs

> Hosted on Render's free tier, so the first request after a period of inactivity can take about a minute while the service wakes up. The database is recreated empty on each fresh deploy.

## Engineering Notes

- **Memory limit on Render**: the first deployment crashed with an out-of-memory error because `sentence-transformers` (PyTorch) exceeded the 512 MB free-tier limit. I replaced the local model with the OpenAI embeddings API, which removed the heavy dependencies and fixed the crash.
- **Testable design**: the SM-2 scheduling logic was extracted into a pure function (`compute_next_schedule`) separate from database access, so it can be unit tested with fixed dates. The OpenAI client is created lazily so modules import without an API key.
- **Single source of truth for the database**: a duplicated database connection (with a hardcoded path) caused `unable to open database file` errors after moving the project. All modules now share `get_connection()` and the path is derived from the file location.

## Known Limitations

- The embedding index lives in memory and is not persisted, so notes must be re-uploaded after a server restart.
- Notes are plain text only; PDF upload is planned.
- Questions are linked to their source note by exact content match, so the quiz can fail if no matching note is found.

## Future Work

- PDF and slide upload
- Persist embeddings so the index survives restarts
- UI polish