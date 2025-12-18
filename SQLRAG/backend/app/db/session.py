"""Database session management with production-ready error handling."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.models import Base
from app.core.config import settings
from app.core.logging_config import get_logger
import os

logger = get_logger(__name__)

# Use settings for URL
DATABASE_URL = settings.database_url_async

# SQLite doesn't support pool_size/max_overflow, so conditionally set engine options
if settings.database_is_sqlite:
    logger.info("Initializing SQLite database engine")
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        # SQLite needs this for async
        connect_args={"check_same_thread": False}
    )
else:
    logger.info(
        "Initializing PostgreSQL database engine",
        extra={"extra_data": {"host": settings.database_hostname, "db": settings.database_name}}
    )
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        pool_size=settings.db_max_connections,
        max_overflow=settings.db_max_connections * 2,
        pool_timeout=settings.db_connection_timeout,
        pool_pre_ping=True,  # Enable connection health checks
    )

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def close_db():
    """Dispose engine connections on shutdown."""
    await engine.dispose()


async def init_db():
    """Initialize database tables and seed with sample data if enabled."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed sample data only in non-production environments
    if settings.environment != "production" and settings.seed_demo_data:
        await seed_sample_data()
    else:
        logger.info("Skipping demo data seed for production environment")

async def seed_sample_data():
    """Add sample data if the database is empty."""
    from app.db.models import Project, Task, TeamMember
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # Check if we already have data
        result = await session.execute(select(TeamMember).limit(1))
        if result.scalars().first():
            return  # Already have data
        
        # Create sample team members with various roles
        team_members = [
            TeamMember(name="Talib Bilat", email="talib@example.com", role="admin"),
            TeamMember(name="Sarah Chen", email="sarah@example.com", role="admin"),
            TeamMember(name="Alice Smith", email="alice@example.com", role="developer"),
            TeamMember(name="Bob Johnson", email="bob@example.com", role="manager"),
            TeamMember(name="Carol Williams", email="carol@example.com", role="designer"),
            TeamMember(name="David Lee", email="david@example.com", role="developer"),
            TeamMember(name="Emma Garcia", email="emma@example.com", role="analyst"),
            TeamMember(name="Frank Miller", email="frank@example.com", role="developer"),
            TeamMember(name="Grace Kim", email="grace@example.com", role="manager"),
            TeamMember(name="Henry Wilson", email="henry@example.com", role="member"),
        ]
        session.add_all(team_members)
        await session.commit()
        
        # Refresh to get IDs
        for tm in team_members:
            await session.refresh(tm)
        
        # Create sample projects
        projects = [
            Project(name="Website Redesign", status="active", owner_id=team_members[3].id, description="Modernize the company website with new branding"),
            Project(name="Mobile App v2", status="planning", owner_id=team_members[2].id, description="Build version 2 of the mobile app with React Native"),
            Project(name="Data Pipeline", status="active", owner_id=team_members[0].id, description="Set up ETL pipelines for real-time analytics"),
            Project(name="Customer Portal", status="completed", owner_id=team_members[3].id, description="Self-service customer portal with dashboard"),
            Project(name="API Gateway", status="active", owner_id=team_members[5].id, description="Centralized API gateway for microservices"),
            Project(name="ML Pipeline", status="planning", owner_id=team_members[6].id, description="Machine learning model training pipeline"),
            Project(name="Security Audit", status="active", owner_id=team_members[1].id, description="Quarterly security and compliance audit"),
            Project(name="Cloud Migration", status="in_progress", owner_id=team_members[8].id, description="Migrate on-prem services to AWS"),
        ]
        session.add_all(projects)
        await session.commit()
        
        for p in projects:
            await session.refresh(p)
        
        # Create sample tasks
        tasks = [
            Task(title="Design homepage mockup", status="completed", project_id=projects[0].id, assignee_id=team_members[4].id),
            Task(title="Implement responsive header", status="in_progress", project_id=projects[0].id, assignee_id=team_members[2].id),
            Task(title="Set up CI/CD pipeline", status="todo", project_id=projects[1].id, assignee_id=team_members[0].id),
            Task(title="Write API documentation", status="in_progress", project_id=projects[2].id, assignee_id=team_members[2].id),
            Task(title="User testing", status="todo", project_id=projects[0].id, assignee_id=team_members[3].id),
            Task(title="Database schema design", status="completed", project_id=projects[4].id, assignee_id=team_members[5].id),
            Task(title="Rate limiting implementation", status="in_progress", project_id=projects[4].id, assignee_id=team_members[7].id),
            Task(title="Model training experiments", status="todo", project_id=projects[5].id, assignee_id=team_members[6].id),
            Task(title="Penetration testing", status="in_progress", project_id=projects[6].id, assignee_id=team_members[1].id),
            Task(title="VPC setup", status="completed", project_id=projects[7].id, assignee_id=team_members[5].id),
            Task(title="S3 bucket migration", status="in_progress", project_id=projects[7].id, assignee_id=team_members[7].id),
            Task(title="RDS instance setup", status="todo", project_id=projects[7].id, assignee_id=team_members[2].id),
            Task(title="Create navigation component", status="in_progress", project_id=projects[0].id, assignee_id=team_members[5].id),
            Task(title="Fix mobile layout bugs", status="todo", project_id=projects[0].id, assignee_id=team_members[4].id),
            Task(title="Performance optimization", status="todo", project_id=projects[2].id, assignee_id=team_members[0].id),
        ]
        session.add_all(tasks)
        await session.commit()
        
        logger.info("Sample data seeded successfully")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
