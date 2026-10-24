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
