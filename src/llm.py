from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI()  # automatically reads OPENAI_API_KEY from the environment

def generate_question(chunk):
    prompt = f"""Based on the following note content, generate one thought-provoking question to test understanding — don't ask for a plain definition, ask for explanation or application:

Note content: {chunk}

Return only the question, nothing else."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def judge_answer(question, user_answer):
    prompt = f"""Question: {question}
User's answer: {user_answer}

Judge whether this answer reflects correct understanding of the concept (focus on whether it captures the core idea, not word-for-word precision).
Return only one word: CORRECT or INCORRECT."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content.strip()
    return result == "CORRECT"

if __name__ == "__main__":
    test_chunk = "Gradient descent is a common method for optimizing machine learning model parameters."
    question = generate_question(test_chunk)
    print(question)