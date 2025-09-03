"""Database connection management with connection pooling and performance optimizations."""
import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

from .config import settings

logger = logging.getLogger(__name__)

# Global engine instance (singleton pattern)
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """Get database engine with connection pooling (singleton)."""
    global _engine
    
    if _engine is None:
        # Connection pool configuration
        pool_config = {
            "poolclass": QueuePool,
            "pool_size": min(settings.db_max_connections, 20),
            "max_overflow": min(settings.db_max_connections * 2, 40),
            "pool_timeout": settings.db_connection_timeout,
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Validate connections before use
            "echo": False,
            "future": True,
        }
        
        _engine = create_engine(settings.database_url, **pool_config)
        
        # Add query timeout event listener
        @event.listens_for(_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            if total > 1.0:  # Log slow queries
                logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")
        
        logger.info(f"Database engine initialized with pool_size={pool_config['pool_size']}")
    
    return _engine


def get_session_factory() -> sessionmaker:
    """Get session factory (singleton)."""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine, future=True)
        logger.info("Session factory initialized")
    
    return _SessionLocal


@contextmanager
def get_db_session():
    """Get database session with automatic cleanup."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_health() -> Dict[str, Any]:
    """Check database health and connection status."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Basic connectivity test
            result = conn.execute(text("SELECT 1 as health_check"))
            health_check = result.scalar()
            
            # Get connection pool status
            pool = engine.pool
            pool_status = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
            
            return {
                "status": "healthy" if health_check == 1 else "unhealthy",
                "health_check": health_check,
                "pool_status": pool_status,
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_status": {},
        }


def optimize_database_connections() -> None:
    """Optimize database connections for production."""
    engine = get_engine()
    
    # Create essential indexes for performance
    with engine.connect() as conn:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_company_financials_company ON company_financials(company)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_company_id ON financial_metrics_normalized(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_period_date ON financial_metrics_normalized(period_date)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_metric_name ON financial_metrics_normalized(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_cap_table_company_id ON cap_table_normalized(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_cap_table_as_of_date ON cap_table_normalized(as_of_date)",
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                logger.info(f"Created index: {index_sql.split()[-1]}")
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
        
        conn.commit()


def close_database_connections() -> None:
    """Close all database connections (for graceful shutdown)."""
    global _engine, _SessionLocal
    
    if _engine:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")
    
    _SessionLocal = None
