from datetime import timedelta


def get_answer_stats(conn, today):
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*), SUM(CASE WHEN is_weak = 0 THEN 1 ELSE 0 END) FROM answers"
    )
    total, correct = cursor.fetchone()
    accuracy = correct / total if total else None

    # created_at is stored in UTC; group by local date to match get_due_reviews
    start = today - timedelta(days=6)
    cursor.execute(
        "SELECT date(created_at, 'localtime') AS d, COUNT(*) FROM answers "
        "WHERE d >= ? AND d <= ? GROUP BY d",
        (start.isoformat(), today.isoformat())
    )
    counts = dict(cursor.fetchall())

    last_7_days = []
    for i in range(7):
        day = (start + timedelta(days=i)).isoformat()
        last_7_days.append({"date": day, "count": counts.get(day, 0)})

    return {"total_answers": total, "accuracy": accuracy, "last_7_days": last_7_days}


def get_category_stats(conn, min_answers=3):
    # Category = the note's source; blank or missing sources share one bucket.
    # Alias is 'category', not 'source', so GROUP BY doesn't pick the raw n.source column.
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(NULLIF(TRIM(n.source), ''), '(no source)') AS category, "
        "COUNT(DISTINCT q.id), COUNT(a.id), "
        "COALESCE(SUM(CASE WHEN a.is_weak = 1 THEN 1 ELSE 0 END), 0) "
        "FROM questions q "
        "JOIN notes n ON n.id = q.note_id "
        "LEFT JOIN answers a ON a.question_id = q.id "
        "GROUP BY category "
        "ORDER BY COUNT(DISTINCT q.id) DESC, category"
    )

    categories = []
    for source, questions, answers, wrong in cursor.fetchall():
        # Skip the rate for tiny samples so 1 wrong out of 1 doesn't read as 100%
        error_rate = wrong / answers if answers >= min_answers else None
        categories.append({
            "source": source,
            "questions": questions,
            "answers": answers,
            "wrong": wrong,
            "error_rate": error_rate,
        })
    return categories
