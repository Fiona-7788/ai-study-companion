import json

from .embedding import get_client  # lazy client, so importing this module needs no API key

def generate_question(chunk):
    prompt = f"""Based on the following note content, generate one thought-provoking question to test understanding — don't ask for a plain definition, ask for explanation or application:

Note content: {chunk}

Return only the question, nothing else."""
    
    response = get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def judge_answer(question, user_answer, note=None):
    # The source note grounds the reference answer so the model doesn't invent one
    note_section = f"Source notes (ground truth):\n{note}\n\n" if note else ""
    prompt = f"""{note_section}Question: {question}
Student's answer: {user_answer}

Judge whether the answer reflects correct understanding of the concept (focus on whether it captures the core idea, not word-for-word precision).

Respond with a JSON object with these keys:
- "is_correct": true or false
- "feedback": 1-2 sentences to the student saying what they got right and what is missing or wrong. Be specific and encouraging.
- "reference_answer": a concise model answer (2-4 sentences), based on the source notes when given.
Write feedback and reference_answer in the same language as the question."""

    response = get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return parse_judgement(response.choices[0].message.content)

def parse_judgement(text):
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # Fall back to the old one-word format
        verdict = (text or "").strip().upper()
        return {"is_correct": verdict == "CORRECT", "feedback": "", "reference_answer": ""}

    is_correct = data.get("is_correct", False)
    if isinstance(is_correct, str):
        is_correct = is_correct.strip().lower() == "true"
    return {
        "is_correct": bool(is_correct),
        "feedback": str(data.get("feedback") or ""),
        "reference_answer": str(data.get("reference_answer") or ""),
    }

if __name__ == "__main__":
    test_chunk = "Gradient descent is a common method for optimizing machine learning model parameters."
    question = generate_question(test_chunk)
    print(question)