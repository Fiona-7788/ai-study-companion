import sqlite3
from src.db import init_db, get_question_text

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
