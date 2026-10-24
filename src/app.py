import streamlit as st
import requests
import html

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Study Companion", page_icon="🧠", layout="centered")

st.markdown("""
<style>
.app-title {
    font-size: 3rem !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    background: linear-gradient(90deg, #6F74D0, #E58DB8);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.app-subtitle {
    color: #5A5C8A;
    margin-top: 0;
    margin-bottom: 1.5rem;
}
.stButton > button {
    background: linear-gradient(90deg, #969BE7, #E58DB8);
    color: #2A2B5E;
    border: none;
    border-radius: 999px;
    padding: 0.5rem 1.6rem;
    font-weight: 700;
}
.stButton > button p {
    color: #2A2B5E;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(111, 116, 208, 0.35);
    color: #2A2B5E;
}
textarea, input {
    border-radius: 14px !important;
}
.q-card, .fb-ok, .fb-review {
    border-radius: 20px;
    padding: 1.1rem 1.4rem;
    margin: 0.8rem 0 1.2rem 0;
    color: #2A2B5E;
    font-size: 1.05rem;
}
.q-card { background: #E9E8F8; border-left: 6px solid #969BE7; }
.fb-ok { background: #E3F6EA; border-left: 6px solid #4CAF82; }
.fb-review { background: #FDE8F0; border-left: 6px solid #E58DB8; }

[data-testid="stMetric"] {
    background: #E9E8F8;
    border-radius: 20px;
    padding: 1rem 1.4rem;
    border-left: 6px solid #E58DB8;
}
.rv-item {
    display: flex;
    justify-content: space-between;
    background: #FFFFFF;
    border: 1px solid #E9E8F8;
    border-radius: 16px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 0.6rem;
    color: #2A2B5E;
}
.rv-item span { color: #6F74D0; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="app-title">AI Study Companion</p>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Turn your notes into active recall practice.</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Upload Notes", "Quiz", "Review"])

with tab1:
    st.header("Upload Notes")
    content = st.text_area("Note content")
    source = st.text_input("Source (optional)")

    if st.button("Upload"):
        response = requests.post(
            f"{API_URL}/upload",
            json={"content": content, "source": source}
        )
        if response.status_code == 200:
            msg = response.json()["message"]
            st.markdown(f'<div class="fb-ok">✅ {html.escape(msg)}</div>',
                        unsafe_allow_html=True)
        else:
            st.error(f"Upload failed: {response.text}")

with tab2:
    st.header("Generate and Answer a Question")
    topic = st.text_input("Topic you want to be tested on")

    if st.button("Generate Question"):
        response = requests.post(f"{API_URL}/quiz", json={"topic": topic})
        if response.status_code == 200:
            st.session_state["current_question"] = response.json()
            st.session_state.pop("last_result", None)  # 换新题,清掉上一题的反馈
        else:
            st.error("Failed to generate question")

    if "current_question" in st.session_state:
        data = st.session_state["current_question"]
        text = data.get("question", data.get("error"))
        st.markdown(f'<div class="q-card">🧠 {html.escape(str(text))}</div>',
                    unsafe_allow_html=True)

        answer = st.text_area("Your answer")
        if st.button("Submit Answer"):
            qid = data["question_id"]
            response = requests.post(
                f"{API_URL}/answer",
                json={"question_id": qid, "user_answer": answer}
            )
            if response.status_code == 200:
                st.session_state["last_result"] = response.json()

        if "last_result" in st.session_state:
            if st.session_state["last_result"]["is_correct"]:
                st.markdown('<div class="fb-ok">🎉 Correct! Nice work.</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="fb-review">📚 This concept needs more review.</div>',
                            unsafe_allow_html=True)

def fetch_reviews():
    response = requests.get(f"{API_URL}/review")
    if response.status_code == 200:
        st.session_state["reviews"] = response.json()
    else:
        st.error("Failed to load reviews")

with tab3:
    st.header("Today's Reviews")

    if st.button("Refresh Review List"):
        st.session_state["rv_feedback"] = []
        fetch_reviews()

    # Feedback for questions answered in this session (newest first)
    for fb in st.session_state.get("rv_feedback", []):
        css = "fb-ok" if fb["is_correct"] else "fb-review"
        verdict = "🎉 Correct! Nice work." if fb["is_correct"] else "📚 This concept needs more review."
        st.markdown(
            f'<div class="{css}">{verdict}<br><small>{html.escape(fb["question_text"])}</small></div>',
            unsafe_allow_html=True
        )

    if "reviews" in st.session_state:
        data = st.session_state["reviews"]
        st.metric("Due for review", data["count"])
        for item in data["reviews"]:
            qid = item["question_id"]
            st.markdown(
                f'<div class="rv-item">📌 Question #{qid}'
                f'<span>Due {item["due_date"]}</span></div>',
                unsafe_allow_html=True
            )
            if item["question_text"] is None:
                st.caption("Question not found.")
                continue

            st.markdown(f'<div class="q-card">🧠 {html.escape(item["question_text"])}</div>',
                        unsafe_allow_html=True)
            # Unique keys so each question keeps its own widget state across reruns
            answer = st.text_area("Your answer", key=f"rv_answer_{qid}")
            if st.button("Submit", key=f"rv_submit_{qid}"):
                response = requests.post(
                    f"{API_URL}/answer",
                    json={"question_id": qid, "user_answer": answer}
                )
                result = response.json() if response.status_code == 200 else {"error": response.text}
                if "error" in result:
                    st.error(f"Submit failed: {result['error']}")
                else:
                    st.session_state.setdefault("rv_feedback", []).insert(0, {
                        "question_text": item["question_text"],
                        "is_correct": result["is_correct"],
                    })
                    # Answered questions get a future due date, so they drop off the list
                    fetch_reviews()
                    st.rerun()