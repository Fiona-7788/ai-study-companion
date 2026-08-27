import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("AI Study Companion")

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
            st.success(response.json())
        else:
            st.error(f"Upload failed: {response.text}")

with tab2:
    st.header("Generate and Answer a Question")
    topic = st.text_input("Topic you want to be tested on")
    
    if st.button("Generate Question"):
        response = requests.post(f"{API_URL}/quiz", json={"topic": topic})
        if response.status_code == 200:
            data = response.json()
            st.session_state["current_question"] = data
            st.write(data.get("question", data.get("error")))
        else:
            st.error("Failed to generate question")
    
    if "current_question" in st.session_state:
        answer = st.text_area("Your answer")
        if st.button("Submit Answer"):
            qid = st.session_state["current_question"]["question_id"]
            response = requests.post(
                f"{API_URL}/answer",
                json={"question_id": qid, "user_answer": answer}
            )
            if response.status_code == 200:
                result = response.json()
                if result["is_correct"]:
                    st.success("Correct!")
                else:
                    st.warning("This concept needs more review")


with tab3:
    st.header("Today's Reviews")
    
    if st.button("Refresh Review List"):
        response = requests.get(f"{API_URL}/review")
        if response.status_code == 200:
            data = response.json()
            st.write(f"You have {data['count']} question(s) due for review")
            for item in data["reviews"]:
                st.write(f"Question ID: {item['question_id']} — Due: {item['due_date']}")
        else:
            st.error("Failed to load reviews")