from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse


from .chunking import chunk_text
from .embedding import get_embedding, find_most_relevant_chunk
from .llm import generate_question, judge_answer
from .review import update_review_schedule
from .db import get_connection
from .review import get_due_reviews

import heapq

note_index = {}
app = FastAPI()

class NoteUpload(BaseModel):
    content: str
    source: str = None

@app.post("/upload")
def upload_note(note: NoteUpload):
    chunks = chunk_text(note.content)
    
    conn = get_connection()
    cursor = conn.cursor()
    inserted_ids = []
    
    for chunk in chunks:
        embedding = get_embedding(chunk)
        note_index[chunk] = embedding  # 存进全局索引
        
        cursor.execute(
            "INSERT INTO notes (content, source) VALUES (?, ?)",
            (chunk, note.source)
        )
        inserted_ids.append(cursor.lastrowid)
    
    conn.commit()
    conn.close()
    
    return {"message": f"{len(chunks)} chunk(s) uploaded", "note_ids": inserted_ids}

@app.get("/notes")
def list_notes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()
    return row

class QuizRequest(BaseModel):
    topic: str

@app.post("/quiz")
def generate_quiz(request: QuizRequest):
    relevant_chunk = find_most_relevant_chunk(request.topic, note_index)
    
    if relevant_chunk is None:
        return {"error": "No notes found. Please upload some notes first."}
    
    question = generate_question(relevant_chunk)
    
    # 存进questions表
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM notes WHERE content = ?",
        (relevant_chunk,)
    )
    note_row = cursor.fetchone()
    note_id = note_row[0] if note_row else None
    
    cursor.execute(
        "INSERT INTO questions (note_id, question_text, difficulty) VALUES (?, ?, ?)",
        (note_id, question, "medium")
    )
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"question_id": question_id, "question": question, "based_on": relevant_chunk}

class AnswerSubmit(BaseModel):
    question_id: int
    user_answer: str

@app.post("/answer")
def submit_answer(submit: AnswerSubmit):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT question_text FROM questions WHERE id = ?", (submit.question_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return {"error": "Question not found"}
    question_text = row[0]
    
    is_correct = judge_answer(question_text, submit.user_answer)
    
    cursor.execute(
        "INSERT INTO answers (question_id, user_answer, is_weak) VALUES (?, ?, ?)",
        (submit.question_id, submit.user_answer, not is_correct)
    )
    conn.commit()
    
    update_review_schedule(conn, submit.question_id, is_correct)
    conn.close()
    
    return {"is_correct": is_correct, "message": "Answer recorded, review schedule updated"}

@app.get("/review")
def get_reviews():
    due = get_due_reviews()
    result = []
    while due:
        review_date, qid = heapq.heappop(due)
        result.append({"question_id": qid, "due_date": review_date})
    return {"count": len(result), "reviews": result}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal error: {str(exc)}"}
    )
