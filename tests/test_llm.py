from src.llm import parse_judgement


def test_parse_valid_json():
    text = '{"is_correct": true, "feedback": "Good.", "reference_answer": "Because X."}'
    assert parse_judgement(text) == {
        "is_correct": True,
        "feedback": "Good.",
        "reference_answer": "Because X.",
    }


def test_parse_string_booleans():
    # Models sometimes quote booleans; "false" must not become True
    assert parse_judgement('{"is_correct": "false"}')["is_correct"] is False
    assert parse_judgement('{"is_correct": "TRUE"}')["is_correct"] is True


def test_parse_missing_fields_default_to_empty():
    result = parse_judgement('{"is_correct": false}')
    assert result == {"is_correct": False, "feedback": "", "reference_answer": ""}


def test_parse_falls_back_to_plain_verdict():
    # Old one-word format still works if the model ignores the JSON instruction
    assert parse_judgement("CORRECT")["is_correct"] is True
    assert parse_judgement("INCORRECT")["is_correct"] is False
    assert parse_judgement("not json at all")["is_correct"] is False
