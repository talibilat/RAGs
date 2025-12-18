from dotenv import load_dotenv
import os

load_dotenv(override=True)

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.middleware import RequestIdMiddleware, LoggingMiddleware, global_exception_handler
from app.core.exceptions import SQLRAGException
from app.db.session import init_db, close_db
from app.api.routers import router as api_router
from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logger = get_logger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    setup_logging()
    logger.info(
        "Application starting up",
        extra={"extra_data": {"environment": settings.environment}}
    )
    
    try:
        from app.agent.graph import create_graph
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        from pathlib import Path
        
        checkpoint_db = Path(settings.checkpoint_path).absolute()
        checkpoint_db.parent.mkdir(parents=True, exist_ok=True)
        
        async with AsyncSqliteSaver.from_conn_string(str(checkpoint_db)) as checkpointer:
            # langgraph-checkpoint-sqlite expects an `is_alive` helper on the aiosqlite
            # connection, but aiosqlite doesn't provide it; add a thin shim.
            conn = getattr(checkpointer, "conn", None)
            if conn and not hasattr(conn, "is_alive"):
                conn.is_alive = lambda: getattr(conn, "_running", False)
            app.state.graph = await create_graph(checkpointer=checkpointer)
            try:
                await init_db()
                app.state.db_available = True
                logger.info("Database and Graph initialized successfully (persistent)")
            except Exception as db_e:
                app.state.db_available = False
                if settings.db_required_effective:
                    raise
                logger.warning(
                    f"Database initialization failed; continuing without DB (DB_REQUIRED=false): {db_e}",
                    exc_info=True,
                )
            yield
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        # Fallback to in-memory if persistent fails
        try:
            from app.agent.graph import create_graph
            app.state.graph = await create_graph(checkpointer=None)
            try:
                await init_db()
                app.state.db_available = True
            except Exception as db_e:
                app.state.db_available = False
                if settings.db_required_effective:
                    raise
                logger.warning(
                    f"Database initialization failed; continuing without DB (DB_REQUIRED=false): {db_e}",
                    exc_info=True,
                )
            logger.warning("Application started with in-memory checkpointer due to error")
            yield
        except Exception as fallback_e:
            logger.critical(f"Critical failure during initialization: {fallback_e}")
            raise
    finally:
        # Shutdown
        try:
            await close_db()
        finally:
            logger.info("Application shutting down gracefully")


app = FastAPI(
    lifespan=lifespan,
    title="SQLRAG Backend",
    description="Production-ready SQL RAG API with LangGraph agent",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Set limiter state for slowapi
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom middleware (order matters - first added is outermost)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register global exception handler
app.add_exception_handler(SQLRAGException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "environment": settings.environment}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies database connectivity."""
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text
    
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        if not settings.db_required_effective:
            return {
                "status": "ready",
                "database": "disconnected",
                "db_required": False,
                "error": str(e),
            }
        return {
            "status": "not_ready",
            "database": "disconnected",
            "db_required": True,
            "error": str(e),
        }


# Include API routes
app.include_router(api_router)





if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
