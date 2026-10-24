import os
import sqlite3
from datetime import date

from src.stats import get_answer_stats

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schema.sql")
TODAY = date(2026, 10, 23)


def make_conn():
    # In-memory DB built from the real schema
    conn = sqlite3.connect(":memory:")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    return conn


def add_answer(conn, created_at, is_weak):
    # Noon UTC keeps the same calendar date after 'localtime' conversion in US timezones
    conn.execute(
        "INSERT INTO answers (question_id, user_answer, is_weak, created_at) VALUES (?, ?, ?, ?)",
        (1, "x", is_weak, created_at),
    )


def test_empty_db():
    stats = get_answer_stats(make_conn(), TODAY)
    assert stats["total_answers"] == 0
    assert stats["accuracy"] is None
    assert len(stats["last_7_days"]) == 7
    assert stats["last_7_days"][0] == {"date": "2026-10-17", "count": 0}
    assert stats["last_7_days"][-1] == {"date": "2026-10-23", "count": 0}


def test_accuracy_counts_non_weak_as_correct():
    conn = make_conn()
    for weak in (False, False, False, True):
        add_answer(conn, "2026-10-23 12:00:00", weak)
    stats = get_answer_stats(conn, TODAY)
    assert stats["total_answers"] == 4
    assert stats["accuracy"] == 0.75


def test_last_7_days_groups_by_day_and_fills_zeros():
    conn = make_conn()
    add_answer(conn, "2026-10-23 12:00:00", False)
    add_answer(conn, "2026-10-23 12:00:00", True)
    add_answer(conn, "2026-10-20 12:00:00", False)
    counts = {d["date"]: d["count"] for d in get_answer_stats(conn, TODAY)["last_7_days"]}
    assert counts["2026-10-23"] == 2
    assert counts["2026-10-20"] == 1
    assert counts["2026-10-21"] == 0


def test_answers_older_than_7_days_excluded_from_chart_but_counted_in_total():
    conn = make_conn()
    add_answer(conn, "2026-10-16 12:00:00", False)  # 7 days ago, one day before the window
    stats = get_answer_stats(conn, TODAY)
    assert stats["total_answers"] == 1
    assert sum(d["count"] for d in stats["last_7_days"]) == 0
