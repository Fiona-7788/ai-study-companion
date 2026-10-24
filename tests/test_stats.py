import os
import sqlite3
from datetime import date

from src.stats import get_answer_stats, get_category_stats

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


def add_question(conn, source, answers=()):
    # One note + one question; answers is a sequence of is_weak flags
    note_id = conn.execute(
        "INSERT INTO notes (content, source) VALUES (?, ?)", ("note", source)
    ).lastrowid
    qid = conn.execute(
        "INSERT INTO questions (note_id, question_text) VALUES (?, ?)", (note_id, "q")
    ).lastrowid
    for weak in answers:
        conn.execute(
            "INSERT INTO answers (question_id, user_answer, is_weak) VALUES (?, ?, ?)",
            (qid, "x", weak),
        )


def test_categories_empty_db():
    assert get_category_stats(make_conn()) == []


def test_categories_group_by_source_and_count():
    conn = make_conn()
    add_question(conn, "CSE 12", answers=(False, True))
    add_question(conn, "CSE 12", answers=(True,))
    add_question(conn, "MATH 20", answers=())
    by_source = {c["source"]: c for c in get_category_stats(conn)}
    assert by_source["CSE 12"]["questions"] == 2
    assert by_source["CSE 12"]["answers"] == 3
    assert by_source["CSE 12"]["wrong"] == 2
    assert by_source["MATH 20"]["questions"] == 1
    assert by_source["MATH 20"]["answers"] == 0
    assert by_source["MATH 20"]["wrong"] == 0


def test_categories_blank_sources_merge_into_no_source():
    conn = make_conn()
    add_question(conn, None)
    add_question(conn, "")
    add_question(conn, "   ")
    cats = get_category_stats(conn)
    assert len(cats) == 1
    assert cats[0]["source"] == "(no source)"
    assert cats[0]["questions"] == 3


def test_categories_error_rate_needs_min_answers():
    conn = make_conn()
    add_question(conn, "few", answers=(True, True))              # 2 answers: too few
    add_question(conn, "enough", answers=(True, False, False, False))
    by_source = {c["source"]: c for c in get_category_stats(conn)}
    assert by_source["few"]["error_rate"] is None
    assert by_source["enough"]["error_rate"] == 0.25


def test_categories_sorted_by_question_count():
    conn = make_conn()
    add_question(conn, "small")
    add_question(conn, "big")
    add_question(conn, "big")
    assert [c["source"] for c in get_category_stats(conn)] == ["big", "small"]
