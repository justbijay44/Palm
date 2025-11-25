# chat.py
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

def rag_chat():
    st.header("💬 Chat with Your Documents")
    
    session_id = st.text_input("Session ID", value="user1")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if query := st.chat_input("Ask a question..."):

        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/rag/query",
                        json={"query": query, "session_id": session_id, "top_k": 5}
                    ).json()
                    
                    st.markdown(resp["answer"])
                    st.session_state.messages.append({"role": "assistant", "content": resp["answer"]})
                    
                except Exception as e:
                    st.error(f"Error: {e}")