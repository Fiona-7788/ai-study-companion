from datetime import date
from src.review import compute_next_schedule
import sqlite3
from src.review import update_review_schedule

def test_correct_answer_doubles_interval():
    today = date(2026, 1, 1)
    next_date, interval, streak = compute_next_schedule(
        interval_days=2, correct_streak=1, is_correct=True, today=today
    )
    assert interval == 4
    assert streak == 2
    assert next_date == date(2026, 1, 5)

def test_wrong_answer_resets_interval():
    today = date(2026, 1, 1)
    next_date, interval, streak = compute_next_schedule(
            interval_days=4, correct_streak=6, is_correct=False, today=today
        )
    assert interval == 1
    assert streak == 0
    assert next_date == date(2026, 1, 2)

def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE review_schedule ("
        "question_id INTEGER PRIMARY KEY, "
        "next_review_date TEXT, "
        "interval_days INTEGER, "
        "correct_streak INTEGER)"
    )
    return conn

def test_first_answer_creates_schedule_row():
    conn = make_conn()
    update_review_schedule(conn, question_id=1, is_correct=True)
    row = conn.execute(
        "SELECT interval_days, correct_streak FROM review_schedule WHERE question_id = 1"
    ).fetchone()
    assert row == (2, 1)

def test_second_correct_answer_updates_existing_row():
    conn = make_conn()
    update_review_schedule(conn, question_id = 1, is_correct = True)
    update_review_schedule(conn, question_id = 1, is_correct = True)
    row = conn.execute(
        "SELECT interval_days, correct_streak FROM review_schedule WHERE question_id = 1"
    ).fetchone()
    assert row == (4, 2)