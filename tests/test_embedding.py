import numpy as np
import pytest
from src.embedding import cosine_similarity
from src.embedding import find_most_relevant_chunk

def test_identical_vectors_have_similarity_one():
    v = np.array([1.0, 2.0, 3.0])
    assert cosine_similarity(v, v) == pytest.approx(1.0)

def test_orthogonal_vectors_have_similarity_zero():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert cosine_similarity(a, b) == pytest.approx(0.0)

def test_opposite_vectors_have_similarity_negative_one():
    a = np.array([1.0, 0.0])
    b = np.array([-1.0, 0.0])
    assert cosine_similarity(a, b) == pytest.approx(-1.0)

def test_find_most_relevant_chunk_returns_closest(monkeypatch):
    monkeypatch.setattr("src.embedding.get_embedding", lambda text: np.array([1.0, 0.0]))

    index = {
        "about cats": np.array([1.0, 0.1]),
        "about cars": np.array([0.0, 1.0]),
    }
    assert find_most_relevant_chunk("anything", index) == "about cats"

def test_find_most_relevant_chunk_empty_index_returns_none():
    index = {}
    assert find_most_relevant_chunk("anything", index) is None