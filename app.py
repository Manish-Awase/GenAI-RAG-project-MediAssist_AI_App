import streamlit as st
import time
from vector_db import query_to_answer,data_ingestion
# Store previous input in session state
if "prev_output" not in st.session_state:
    st.session_state.prev_output = ""
if "prev_question" not in st.session_state:
    st.session_state.prev_question = ""

# Store previous .v_database_complete_state in session state after creating vector database
if "v_database_complete_state" not in st.session_state:
    st.session_state.v_database_complete_state = ""


# --- Sidebar: PubMed Search ---
st.sidebar.header("⬇️ Load PubMed articles")

articles = st.sidebar.text_input("Enter given PubMed keywords with ',' \n\nex-(obesity,Type 2 Diabetes,metabolic disorders)")
search_button_pressed = st.sidebar.button("Search & Ingest")

if search_button_pressed:

    article_list = [item.strip() for item in articles.split(",") if item.strip()!='']
    # articles = [article for article in articles if article.strip() != ""]
    # articles=articles.strip()
    if article_list :
        # check if new article is searched
        if article_list != st.session_state.article_list:
            st.session_state.article_list = article_list


            # TODO: Add PubMed API + ingestion logic here
            data_ingestion(article_list)
        st.sidebar.success(f"You are ready to research articles")
        st.session_state.v_database_complete_state = "document added in vectorstore"

        time.sleep(1)

    else:
        st.sidebar.warning(f"insert articles ")
        st.session_state.v_database_complete_state= "document not added in vectorstore"
# --- Main Interface: Query Bar ---
st.title("🩺 MediAssist AI")

user_question = st.text_input("🧠 Ask Questions About Ingested Articles")

if st.button("Get Answer"):
    if user_question.strip():

        if st.session_state.v_database_complete_state == "document added in vectorstore":
            # if new question is not same as previous question
            if user_question.strip()!=st.session_state.prev_question:
                st.session_state.prev_question = user_question
                # TODO: Add response logic here
                st.write(f"🔎 You asked: **{user_question}**")
                answer=query_to_answer(user_question)
                st.session_state.prev_output=answer
                # show response
                st.success(answer)

            else:
                st.success(st.session_state.prev_output)
        else:
            st.warning("Please load an article.")
    else:
        st.warning("Please enter a question.")
