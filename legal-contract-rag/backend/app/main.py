import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.api.v1.router import api_router
from backend.app.llm.factory import LLMProviderFactory
from backend.app.presentation.handlers.error_handlers import setup_exception_handlers
from backend.app.presentation.middlewares.correlation import CorrelationIdMiddleware

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise RAG application for legal contract ingestion, chunking, vector indexing, and grounded Q&A.",
    version=settings.VERSION
)

# 1. Register Cross-Cutting Middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Register Global RFC 7807 Error Handlers
setup_exception_handlers(app)

# 3. Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    active_provider = LLMProviderFactory.get_provider()
    llm_health = await active_provider.health_check()
    overall_status = "healthy" if llm_health.get("status") == "healthy" else "degraded"
    return {
        "status": overall_status,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "active_llm": llm_health
    }


# Serve Angular compiled static frontend if available
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "message": "Enterprise Legal Contract RAG API is running",
            "docs": "/docs",
            "version": settings.VERSION
        }
