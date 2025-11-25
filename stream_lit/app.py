import streamlit as st
import requests
from chat import rag_chat

API_BASE =  "http://127.0.0.1:8000/"

st.set_page_config(
    page_title="PALm API Demo",
    page_icon= "🤲",
    layout="wide"
)

st.title("PALM API Demo")

menu = ["📄 Document Ingestion", "💬 Query RAG", "📅 Book Interview", "📋 View Bookings"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "📄 Document Ingestion":
    st.header("📄 Upload a document")

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt"])

    col1, col2 = st.columns(2)
    with col1:
        chunk_strategy = st.selectbox("Chunk Strategy", ["fixed", "semantic"])
    with col2:
        chunk_size = st.number_input("Chunk Size", value=500, min_value=100, max_value=2000)

    if st.button("Upload"):
        if uploaded_file:
            with st.spinner("Processing document..."):
                files = {"file": uploaded_file}
                params = {"Chunk strategy": chunk_size, "chunk_size": chunk_size}
                
                try:  
                    resp = requests.post(f"{API_BASE}/ingestion/ingest", files=files, params=params)
                    result = resp.json()
                    st.json(result)
                except Exception as e:
                    st.error(f"Connection error {e}")

        else:
            st.warning("Please Upload a file first")

elif choice == "💬 Query RAG":
    rag_chat()
            
elif choice == "📅 Book Interview":
    st.header("Book an Interview")
    message = st.text_area("Booking Message (e.g., 'Book Dec 15 at 2pm. Name: Alice, email: alice@example.com, phone: 9812345678'), height=100")

    if st.button("Book"):
        resp = requests.post(f"{API_BASE}/rag/book-interview", json={"message": message})
        st.write(resp.json())

elif choice == "📋 View Bookings":
    st.header("All Bookings")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        resp = requests.get(f"{API_BASE}/rag/bookings")
        data = resp.json()

        if data:
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No bookings found.")
    except Exception as e:
        st.error(f"Failed to load bookings: {e}")