# PALM - INTERN TASK
**Simple & Clean RAG Ingestion Backend using FastAPI**

### How to run

# 1. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 2. Install & run
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. Open Swagger
http://localhost:8000/docs

### Task 1 - Ingestion Feature
  Working :
    - User can upload file with extension .pdf or .txt where the text gets extracted, chunked, embedded and the
       vector are stored in qdrant whereas the metadata in sqlite

