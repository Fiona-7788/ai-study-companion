import sqlite3
import os

import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "study.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    schema_path = os.path.join(BASE_DIR, "schema.sql")
    with open(schema_path) as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    # CREATE TABLE IF NOT EXISTS won't add new columns to an existing table
    cols = {row[1] for row in conn.execute("PRAGMA table_info(notes)")}
    if "embedding" not in cols:
        conn.execute("ALTER TABLE notes ADD COLUMN embedding BLOB")
        conn.commit()
    conn.close()

def _to_blob(vec):
    # float32 is enough precision for similarity search and halves the size
    return np.asarray(vec, dtype=np.float32).tobytes()

def _from_blob(blob):
    return np.frombuffer(blob, dtype=np.float32)

def insert_note(conn, content, source, embedding):
    cursor = conn.execute(
        "INSERT INTO notes (content, source, embedding) VALUES (?, ?, ?)",
        (content, source, _to_blob(embedding))
    )
    return cursor.lastrowid

def load_note_index(conn):
    rows = conn.execute(
        "SELECT content, embedding FROM notes WHERE embedding IS NOT NULL"
    ).fetchall()
    return {content: _from_blob(blob) for content, blob in rows}

def backfill_embeddings(conn, embed_fn):
    # Compute embeddings for notes saved before the column existed
    rows = conn.execute("SELECT id, content FROM notes WHERE embedding IS NULL").fetchall()
    for note_id, content in rows:
        conn.execute(
            "UPDATE notes SET embedding = ? WHERE id = ?",
            (_to_blob(embed_fn(content)), note_id)
        )
        conn.commit()  # per row, so a mid-way failure keeps the work already done
    return len(rows)

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

def get_question_text(question_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT question_text FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    create_note("测试笔记来自Python", "CSE 12")
    for row in get_all_notes():
        print(row)