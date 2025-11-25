# PALM API - Document Ingestion & RAG

### How to run

# 1. Start Services
<!-- docker run -p 6333:6333 qdrant/qdrant -->
docker-compose up -d  # to start Qdrant & redis in background
docker compose down   # to stop the service

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Configure Environment
Create a .env file:
- GROQ_API_KEY=your_groq_api_key
- REDIS_HOST=localhost or ip if running remotely with wsl
- REDIS_PORT=6379

# 4. Open Swagger
http://localhost:8000/docs

# 5. Run the Server
uvicorn app.main:app --reload

### Feature 1 - Document Ingestion (/ingestion/ingest)
- Upload .pdf or .txt files
- Extract text and apply chunking (fixed or semantic)
- Generate embeddings and store in Qdrant
- Save metadata in SQLite

### Feature 2 - Conversational RAG (/rag/query)
- Retrieve relevant chunks from Qdrant
- Maintain chat memory in Redis
- Generate answers using LLM
- Support multi-turn conversation

### Feature 3 - Interview Booking (/rag/book-interview)
- Natural language booking requests
- LLM extracts name, email, phone, date, and time
- Validates and stores bookings
- Prevents duplicate

### Other Endpoints:
- GET /rag/bookings - List bookings
- PATCH /rag/booking/{id}/status - Update status (pending/confirmed/cancelled)
- DELETE /rag/booking/{id} - Cancel booking