import heapq
from datetime import date, timedelta
from .db import get_connection

def get_due_reviews():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT question_id, next_review_date FROM review_schedule WHERE next_review_date <= ?",
        (date.today().isoformat(),)
    )
    rows = cursor.fetchall()
    conn.close()

    heap = [(row[1], row[0]) for row in rows]
    heapq.heapify(heap)
    return heap

def update_review_schedule(conn, question_id, is_correct):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT interval_days, correct_streak FROM review_schedule WHERE question_id = ?",
        (question_id,)
    )
    row = cursor.fetchone()
    
    if row is None:
        # 第一次答这道题,还没有调度记录,初始化一条
        interval_days, correct_streak = 1, 0
    else:
        interval_days, correct_streak = row
    
    next_date, interval_days, correct_streak = compute_next_schedule(
        interval_days, correct_streak, is_correct, date.today()
    )

    if row is None:
        cursor.execute(
            "INSERT INTO review_schedule (question_id, next_review_date, interval_days, correct_streak) VALUES (?, ?, ?, ?)",
            (question_id, next_date.isoformat(), interval_days, correct_streak)
        )
    else:
        cursor.execute(
            "UPDATE review_schedule SET next_review_date = ?, interval_days = ?, correct_streak = ? WHERE question_id = ?",
            (next_date.isoformat(), interval_days, correct_streak, question_id)
        )
    conn.commit()

def compute_next_schedule(interval_days, correct_streak, is_correct, today):
    if is_correct:
        correct_streak += 1
        interval_days = interval_days * 2
    else:
        correct_streak = 0
        interval_days = 1

    next_date = today + timedelta(days=interval_days)
    return next_date, interval_days, correct_streak

if __name__ == "__main__":
    conn = get_connection()
    
    # 测试1:更新调度(模拟答对question_id=1,答错question_id=2)
    update_review_schedule(conn, question_id=1, is_correct=True)
    update_review_schedule(conn, question_id=2, is_correct=False)
    conn.close()
    
    # 测试2:查询今天该复习的题目
    due = get_due_reviews()
    print(f"{len(due)} question(s) due for review today:")
    while due:
        review_date, qid = heapq.heappop(due)
        print(f"question_id={qid}, due={review_date}")