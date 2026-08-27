from dotenv import load_dotenv
load_dotenv()

import numpy as np
from openai import OpenAI

client = OpenAI()  # automatically reads OPENAI_API_KEY from the environment

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding)

def build_index(chunks):
    index = {}
    for chunk in chunks:
        index[chunk] = get_embedding(chunk)
    return index

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

def find_most_relevant_chunk(topic, index):
    topic_embedding = get_embedding(topic)

    best_chunk = None
    best_score = -1

    for chunk, chunk_embedding in index.items():
        score = cosine_similarity(topic_embedding, chunk_embedding)
        if score > best_score:
            best_score = score
            best_chunk = chunk

    return best_chunk
