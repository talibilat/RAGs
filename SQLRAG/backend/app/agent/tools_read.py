"""Read tools for database queries with production-ready error handling."""
from typing import List, Optional, Any
from langchain_core.tools import tool
from sqlalchemy import select, or_, and_

from app.db.session import AsyncSessionLocal
from app.db.models import Task, Project, TeamMember
from app.core.logging_config import get_logger
from datetime import datetime

logger = get_logger(__name__)


@tool
async def get_tasks(
    assignee_email: Optional[str] = None,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """Get tasks with optional filters."""
    logger.info(
        "Fetching tasks",
        extra={"extra_data": {"assignee": assignee_email, "project_id": project_id, "status": status}}
    )
    
    try:
        async with AsyncSessionLocal() as session:
            query = select(Task)
            if assignee_email:
                query = query.join(Task.assignee).where(TeamMember.email == assignee_email)
            if project_id:
                query = query.where(Task.project_id == project_id)
            if status:
                query = query.where(Task.status == status)
            
            query = query.limit(min(limit, 100))  # Cap at 100 for safety
            result = await session.execute(query)
            tasks = result.scalars().all()
            
            logger.debug(f"Found {len(tasks)} tasks")
            return [
                {"id": t.id, "title": t.title, "status": t.status, "project_id": t.project_id} 
                for t in tasks
            ]
    except Exception as e:
        logger.error(f"Failed to fetch tasks: {e}", exc_info=True)
        return [{"error": "Failed to fetch tasks. Please try again."}]


@tool
async def get_projects(
    owner_email: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """Get projects with optional filters."""
    logger.info(
        "Fetching projects",
        extra={"extra_data": {"owner": owner_email, "status": status}}
    )
    
    try:
        async with AsyncSessionLocal() as session:
            query = select(Project)
            if owner_email:
                query = query.join(Project.owner).where(TeamMember.email == owner_email)
            if status:
                query = query.where(Project.status == status)
            
            query = query.limit(min(limit, 100))
            result = await session.execute(query)
            projects = result.scalars().all()
            
            logger.debug(f"Found {len(projects)} projects")
            return [
                {"id": p.id, "name": p.name, "status": p.status, "description": p.description}
                for p in projects
            ]
    except Exception as e:
        logger.error(f"Failed to fetch projects: {e}", exc_info=True)
        return [{"error": "Failed to fetch projects. Please try again."}]


@tool
async def get_team_members(
    name_or_email: Optional[str] = None,
    limit: int = 20
) -> List[dict]:
    """Get team members."""
    logger.info("Fetching team members", extra={"extra_data": {"search": name_or_email}})
    
    try:
        async with AsyncSessionLocal() as session:
            query = select(TeamMember)
            if name_or_email:
                # Sanitize input for LIKE query
                search_term = name_or_email.replace("%", "").replace("_", "")
                query = query.where(
                    or_(
                        TeamMember.name.ilike(f"%{search_term}%"),
                        TeamMember.email.ilike(f"%{search_term}%")
                    )
                )
            query = query.limit(min(limit, 50))
            result = await session.execute(query)
            members = result.scalars().all()
            
            logger.debug(f"Found {len(members)} team members")
            return [
                {"id": m.id, "name": m.name, "email": m.email, "role": m.role}
                for m in members
            ]
    except Exception as e:
        logger.error(f"Failed to fetch team members: {e}", exc_info=True)
        return [{"error": "Failed to fetch team members. Please try again."}]


from app.tools.financial_rag import answer_financial_question


@tool
async def get_financial_data(question: str) -> str:
    """
    Get financial data or answer questions about companies, metrics, revenue, profit, etc.
    Use this for any question unrelated to Projects/Tasks/TeamMembers, specifically for financial analysis.
    """
    logger.info("Processing financial query", extra={"extra_data": {"question_length": len(question)}})
    
    try:
        import asyncio
        result = await asyncio.to_thread(answer_financial_question, question)
        logger.debug("Financial query completed successfully")
        return result
    except Exception as e:
        logger.error(f"Financial query failed: {e}", exc_info=True)
        return f"Error processing financial query: {str(e)}"


READ_TOOLS = [get_tasks, get_projects, get_team_members, get_financial_data]

