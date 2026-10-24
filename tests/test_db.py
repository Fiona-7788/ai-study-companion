import sqlite3
import numpy as np
from src.db import (
    init_db, get_question_text, get_connection,
    insert_note, load_note_index, backfill_embeddings,
)

def test_init_db_creates_all_tables(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("src.db.DB_PATH", db_file)

    init_db()

    conn = sqlite3.connect(db_file)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    names = {row[0] for row in rows}
    assert {"notes", "questions", "answers", "review_schedule"} <= names

def test_init_db_is_safe_to_run_twice(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("src.db.DB_PATH", db_file)

    init_db()
    init_db()  # Run it twice to ensure it's safe

    conn = sqlite3.connect(db_file)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    names = {row[0] for row in rows}
    assert {"notes", "questions", "answers", "review_schedule"} <= names

def test_get_question_text_returns_text(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("src.db.DB_PATH", db_file)
    init_db()

    conn = sqlite3.connect(db_file)
    cursor = conn.execute(
        "INSERT INTO questions (note_id, question_text, difficulty) VALUES (?, ?, ?)",
        (1, "What is a heap?", "medium")
    )
    qid = cursor.lastrowid
    conn.commit()
    conn.close()

    assert get_question_text(qid) == "What is a heap?"

def test_get_question_text_missing_id_returns_none(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("src.db.DB_PATH", db_file)
    init_db()

    assert get_question_text(99) is None

def test_init_db_adds_embedding_column_to_old_notes_table(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("src.db.DB_PATH", db_file)
    # Simulate a database created before the embedding column existed
    conn = sqlite3.connect(db_file)
    conn.execute(
        "CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, "
        "source TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute("INSERT INTO notes (content) VALUES ('old note')")
    conn.commit()
    conn.close()

    init_db()
    init_db()  # migration must be safe to run twice

    conn = sqlite3.connect(db_file)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(notes)")}
    assert "embedding" in cols
    assert conn.execute("SELECT content FROM notes").fetchone()[0] == "old note"

def test_insert_note_and_load_index_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr("src.db.DB_PATH", str(tmp_path / "test.db"))
    init_db()
    conn = get_connection()
    insert_note(conn, "chunk a", "CSE 12", np.array([0.1, 0.2, 0.3]))
    conn.commit()

    index = load_note_index(conn)
    assert list(index) == ["chunk a"]
    assert np.allclose(index["chunk a"], [0.1, 0.2, 0.3])

def test_load_index_skips_notes_without_embedding(tmp_path, monkeypatch):
    monkeypatch.setattr("src.db.DB_PATH", str(tmp_path / "test.db"))
    init_db()
    conn = get_connection()
    conn.execute("INSERT INTO notes (content) VALUES ('no vector yet')")
    conn.commit()

    assert load_note_index(conn) == {}

def test_backfill_embeddings_fills_only_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("src.db.DB_PATH", str(tmp_path / "test.db"))
    init_db()
    conn = get_connection()
    insert_note(conn, "has vector", None, np.array([1.0, 0.0]))
    conn.execute("INSERT INTO notes (content) VALUES ('missing vector')")
    conn.commit()

    calls = []
    def fake_embed(text):
        calls.append(text)
        return np.array([0.0, 1.0])

    assert backfill_embeddings(conn, fake_embed) == 1
    assert calls == ["missing vector"]
    index = load_note_index(conn)
    assert np.allclose(index["missing vector"], [0.0, 1.0])
    assert np.allclose(index["has vector"], [1.0, 0.0])
