import sqlite3
from src.db import init_db

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
