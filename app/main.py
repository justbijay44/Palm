from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.routes import custom_rag, ingestion

app = FastAPI(title = 'Palm APIs')

app.include_router(ingestion.router, prefix='/ingestion', tags=["Document Ingestion"])
app.include_router(custom_rag.router, prefix='/rag', tags=["Custom RAG"])

@app.get("/", response_class=HTMLResponse)
def root():
    html_content = """
    <html>
        <head>
            <title>PALM API</title>
        </head>
        <body>
            <h1>Welcome to PALM APIs</h1>
            <ul>
                <li><a href="/ingest/">Document Ingestion API</a></li>
                <li><a href="/rag/">Custom RAG API</a></li>
                <li><a href="/docs">Swagger Docs</a></li>
                <li><a href="/redoc">Redoc Docs</a></li>
            </ul>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)