
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import documents, chat
from app.services.ollama_service import OllamaService
from app.config import config
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='Legal Contract Assistant',
    description='A RAG-based application for querying legal contract documents',
    version='1.0.0'
)

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include API routers
app.include_router(documents.router, prefix='/api/documents', tags=['documents'])
app.include_router(chat.router, prefix='/api/chat', tags=['chat'])

@app.get('/health')
async def health_check():
    '''
    Health check endpoint that includes Ollama status.
    '''
    ollama_service = OllamaService()
    ollama_health = await ollama_service.health_check()

    overall_status = 'healthy' if ollama_health['status'] == 'healthy' else 'degraded'

    return {
        'status': overall_status,
        'ollama': ollama_health
    }

# Serve the frontend static files
# Mount AFTER the API routes so /api/* is handled first
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
if os.path.isdir(FRONTEND_DIR):
    app.mount('/static', StaticFiles(directory=FRONTEND_DIR), name='static')

    @app.get('/')
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))
else:
    @app.get('/')
    async def root():
        return {'message': 'Legal Contract Assistant API is running'}
