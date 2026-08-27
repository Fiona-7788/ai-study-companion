import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "study.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_note(content, source):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes (content, source) VALUES (?, ?)",
        (content, source)
    )
    conn.commit()
    conn.close()

def get_all_notes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_answers_paginated(page=1, page_size=10):
    conn = get_connection()
    cursor = conn.cursor()
    offset = (page - 1) * page_size
    cursor.execute(
        "SELECT * FROM answers ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (page_size, offset)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    create_note("测试笔记来自Python", "CSE 12")
    for row in get_all_notes():
        print(row)