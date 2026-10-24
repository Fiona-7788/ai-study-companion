import streamlit as st
import requests
import html
import math

import altair as alt
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Study Companion", page_icon="🧠", layout="centered")

st.markdown("""
<style>
/* Page background: soft lavender-pink gradient, light enough to keep #2A2B5E text readable */
[data-testid="stApp"] {
    background: linear-gradient(135deg, #FCF8FB 0%, #EEEBFA 50%, #FBEAF3 100%);
    background-attachment: fixed;
}
/* Let the gradient show through the top header bar */
[data-testid="stHeader"] {
    background: transparent;
}
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
.q-card, [data-testid="stMetric"] {
    box-shadow: 0 4px 14px rgba(42, 43, 94, 0.08);
}
.q-card { background: #FFFFFF; border-left: 6px solid #969BE7; }
.fb-ok { background: #E3F6EA; border-left: 6px solid #4CAF82; }
.fb-review { background: #FDE8F0; border-left: 6px solid #E58DB8; }

[data-testid="stMetric"] {
    background: #FFFFFF;
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
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F3F1FC 0%, #FBEFF6 100%);
    border-right: 1px solid #E9E8F8;
}
.side-brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 1.2rem;
}
.side-brand span {
    background: linear-gradient(90deg, #6F74D0, #E58DB8);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
/* Sidebar nav: full-width, left-aligned items */
[data-testid="stSidebar"] .stButton > button {
    border-radius: 14px;
    padding: 0.55rem 1rem;
}
[data-testid="stSidebar"] .stButton > button p {
    font-size: 1rem;
}
/* Left-align the label; if Streamlit changes this markup it just falls back to centered */
[data-testid="stSidebar"] .stButton > button > div {
    justify-content: flex-start;
    width: 100%;
}
/* Inactive pages: transparent, light highlight on hover */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: transparent;
    box-shadow: none;
    font-weight: 500;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background: rgba(150, 155, 231, 0.15);
    transform: none;
}
/* Dashboard cards */
.dash-card, .st-key-chart_card {
    background: #FFFFFF;
    border-radius: 20px;
    box-shadow: 0 4px 14px rgba(42, 43, 94, 0.08);
}
.dash-card {
    padding: 1.2rem 1.4rem;
    min-height: 210px;
    color: #2A2B5E;
}
.st-key-chart_card { padding: 1.2rem 1.4rem 0.6rem; margin-top: 0.8rem; }
.dash-label { color: #5A5C8A; font-weight: 700; font-size: 0.95rem; }
.dash-big { font-size: 3.6rem; font-weight: 800; line-height: 1.1; margin-top: 0.6rem; }
.dash-sub { color: #5A5C8A; font-size: 0.9rem; }
.dash-ring { display: flex; align-items: center; gap: 1.2rem; margin-top: 0.6rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="app-title">AI Study Companion</p>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Turn your notes into active recall practice.</p>', unsafe_allow_html=True)

PAGE_ICONS = {
    "Dashboard": ":material/dashboard:",
    "Upload": ":material/edit_note:",
    "Quiz": ":material/quiz:",
    "Review": ":material/replay:",
}

# Logo: open book with a spark, on a rounded gradient tile
LOGO_SVG = """
<svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true">
  <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#969BE7"/><stop offset="1" stop-color="#E58DB8"/>
  </linearGradient></defs>
  <rect width="36" height="36" rx="10" fill="url(#logo-grad)"/>
  <path d="M8 13 C12 11.5 15.5 12 18 14 C20.5 12 24 11.5 28 13 V27 C24 25.5 20.5 26 18 28 C15.5 26 12 25.5 8 27Z"
        fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>
  <path d="M18 14 V28" stroke="#fff" stroke-width="2"/>
  <path d="M25 4.5 L25.8 7.2 L28.5 8 L25.8 8.8 L25 11.5 L24.2 8.8 L21.5 8 L24.2 7.2Z" fill="#fff"/>
</svg>
"""

def go_to(name):
    st.session_state["page"] = name

# Current page lives in session_state so it survives reruns
st.session_state.setdefault("page", "Dashboard")
page = st.session_state["page"]

with st.sidebar:
    st.markdown(f'<div class="side-brand">{LOGO_SVG}<span>Study Companion</span></div>',
                unsafe_allow_html=True)
    nav = st.container(gap="xxsmall")
    for name, icon in PAGE_ICONS.items():
        # The active page is a primary (gradient) button; the rest are plain
        nav.button(
            name,
            icon=icon,
            key=f"nav_{name}",
            type="primary" if name == page else "secondary",
            width="stretch",
            on_click=go_to,
            args=(name,),
        )

def accuracy_ring(accuracy):
    # SVG donut: a gradient arc whose length is accuracy * circumference
    r = 42
    circumference = 2 * math.pi * r
    filled = (accuracy or 0) * circumference
    label = "—" if accuracy is None else f"{accuracy:.0%}"
    return f"""
<svg width="120" height="120" viewBox="0 0 120 120">
  <defs><linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#969BE7"/><stop offset="1" stop-color="#E58DB8"/>
  </linearGradient></defs>
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="#E9E8F8" stroke-width="12"/>
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="url(#ring-grad)" stroke-width="12"
          stroke-linecap="round" stroke-dasharray="{filled} {circumference}"
          transform="rotate(-90 60 60)"/>
  <text x="60" y="67" text-anchor="middle" font-size="22" font-weight="800" fill="#2A2B5E">{label}</text>
</svg>"""

def activity_chart(last_7_days):
    df = pd.DataFrame(last_7_days)
    df["date"] = pd.to_datetime(df["date"])
    base = alt.Chart(df).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%b %d", tickCount=7, grid=False)),
        y=alt.Y("count:Q", title=None, axis=alt.Axis(tickMinStep=1, gridColor="#E9E8F8")),
        tooltip=[alt.Tooltip("date:T", format="%b %d"), alt.Tooltip("count:Q", title="answers")],
    )
    area = base.mark_area(
        interpolate="monotone",
        color=alt.Gradient(
            gradient="linear", x1=1, x2=1, y1=1, y2=0,
            stops=[alt.GradientStop(color="#FFFFFF", offset=0),
                   alt.GradientStop(color="#E58DB8", offset=1)],
        ),
        opacity=0.35,
    )
    line = base.mark_line(interpolate="monotone", color="#969BE7", strokeWidth=3)
    points = base.mark_point(filled=True, color="#6F74D0", size=60)
    return (area + line + points).properties(height=220, background="#FFFFFF").configure_view(strokeWidth=0)

if page == "Dashboard":
    st.header("Dashboard")
    try:
        response = requests.get(f"{API_URL}/stats")
        stats = response.json() if response.status_code == 200 else None
    except requests.ConnectionError:
        stats = None

    if stats is None:
        st.error("Couldn't load stats. Is the backend running?")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
<div class="dash-card">
  <div class="dash-label">Due for review today</div>
  <div class="dash-big">{stats["due_today"]}</div>
  <div class="dash-sub">{stats["total_answers"]} answers recorded so far</div>
</div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
<div class="dash-card">
  <div class="dash-label">Accuracy</div>
  <div class="dash-ring">{accuracy_ring(stats["accuracy"])}
    <div class="dash-sub">Share of answers<br>judged correct</div>
  </div>
</div>""", unsafe_allow_html=True)

        # key gives the container a stable .st-key-chart_card class for styling
        with st.container(key="chart_card"):
            st.markdown('<div class="dash-label">Answers in the last 7 days</div>',
                        unsafe_allow_html=True)
            st.altair_chart(activity_chart(stats["last_7_days"]), width="stretch")

elif page == "Upload":
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

elif page == "Quiz":
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

elif page == "Review":
    st.header("Review")

    # --- load the queue ---
    if st.button("Start / Refresh Review"):
        response = requests.get(f"{API_URL}/review")
        if response.status_code == 200:
            items = [r for r in response.json()["reviews"] if r.get("question_text")]
            st.session_state["rv_queue"] = items
            st.session_state["rv_idx"] = 0
            st.session_state["rv_result"] = None
        else:
            st.error("Failed to load reviews")

    # --- run the session ---
    if "rv_queue" in st.session_state:
        queue = st.session_state["rv_queue"]
        idx = st.session_state["rv_idx"]
        result = st.session_state["rv_result"]

        if not queue:
            st.markdown('<div class="fb-ok">🎉 Nothing to review right now.</div>',
                        unsafe_allow_html=True)
        elif idx >= len(queue):
            st.markdown(f'<div class="fb-ok">🎉 All done! You reviewed {len(queue)} question(s).</div>',
                        unsafe_allow_html=True)
        else:
            item = queue[idx]
            st.progress(idx / len(queue))
            st.caption(f"Question {idx + 1} of {len(queue)}")
            st.markdown(f'<div class="q-card">🧠 {html.escape(item["question_text"])}</div>',
                        unsafe_allow_html=True)

            if result is None:
                answer = st.text_area("Your answer", key=f"rv_answer_{idx}")
                if st.button("Submit", key=f"rv_submit_{idx}"):
                    if not answer.strip():
                        st.warning("Write an answer first.")
                    else:
                        resp = requests.post(
                            f"{API_URL}/answer",
                            json={"question_id": item["question_id"], "user_answer": answer},
                        )
                        if resp.status_code == 200:
                            st.session_state["rv_result"] = resp.json()["is_correct"]
                            st.rerun()
                        else:
                            st.error("Failed to submit answer")
            else:
                if result:
                    st.toast("Correct!", icon="🎉")
                    st.markdown('<div class="fb-ok">🎉 Correct! Nice work.</div>',
                                unsafe_allow_html=True)
                else:
                    st.toast("Needs more review", icon="📚")
                    st.markdown('<div class="fb-review">📚 Not quite. You will see this one again.</div>',
                                unsafe_allow_html=True)

                last = idx == len(queue) - 1
                if st.button("Finish" if last else "Next →", key=f"rv_next_{idx}"):
                    st.session_state["rv_idx"] = idx + 1
                    st.session_state["rv_result"] = None
                    st.rerun()