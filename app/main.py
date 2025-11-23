from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.routes import custom_rag, ingestion
from app.db.database import engine, Base
from app.db.models import Document, Chunk
from contextlib import asynccontextmanager

# for auto creation of db table on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created.")
    yield 
    print("🔻 Shutting down...")

app = FastAPI(title = 'Palm APIs', lifespan=lifespan)

app.include_router(ingestion.router, prefix='/ingestion', tags=["Document Ingestion"])
app.include_router(custom_rag.router, prefix='/rag', tags=["Custom RAG"])

# @app.get("/", response_class=HTMLResponse)
# def root():
#     html_content = """
#     <html>
#         <head>
#             <title>PALM API</title>
#         </head>
#         <body>
#             <h1>Welcome to PALM APIs</h1>
#             <ul>
#                 <li><a href="/ingestion/">Document Ingestion API</a></li>
#                 <li><a href="/rag/">Custom RAG API</a></li>
#                 <li><a href="/docs">Swagger Docs</a></li>
#                 <li><a href="/redoc">Redoc Docs</a></li>
#             </ul>
#         </body>
#     </html>
#     """
#     return HTMLResponse(content=html_content)

