import streamlit as st
import requests

st.set_page_config(page_title="Local RAG Explorer", layout="wide")
st.title("Local Hybrid RAG Engine")

API_URL = "http://backend:8000/query"

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "citations" in msg:
            with st.expander("View Citations"):
                for cite in msg["citations"]:
                    st.caption(f"**Source:** `{cite['source']}`")
                    st.text(cite['content'])

if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Searching and re-ranking documents..."):
            try:
                response = requests.post(API_URL, json={"query": prompt}).json()
                answer = response.get("answer", "Error generating answer.")
                citations = response.get("citations", [])
                
                st.markdown(answer)
                with st.expander("View Citations"):
                    for cite in citations:
                        st.caption(f"**Source:** `{cite['source']}`")
                        st.text(cite['content'])
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "citations": citations
                })
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")