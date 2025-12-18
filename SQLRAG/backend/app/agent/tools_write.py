"""Write tools for database mutations with production-ready error handling."""
from typing import Optional, Any, Dict
from sqlalchemy import select, update, delete
from datetime import datetime
from langchain_core.tools import tool

from app.db.session import AsyncSessionLocal
from app.db.models import Task, Project, TeamMember
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Allowed fields for each model to prevent arbitrary field updates
ALLOWED_PROJECT_FIELDS = {"name", "description", "status", "owner_id"}
ALLOWED_TASK_FIELDS = {"title", "description", "status", "assignee_id", "due_date", "project_id"}


@tool
async def create_project(name: str, status: str, owner_email: str, description: Optional[str] = None):
    """
    Create a new project.
    
    Args:
        name: The name of the project.
        status: The status of the project.
        owner_email: The email of the project owner.
        description: A brief description of the project.
    """
    logger.info(
        "Creating project",
        extra={"extra_data": {"name": name, "status": status, "owner": owner_email}}
    )
    
    try:
        async with AsyncSessionLocal() as session:
            # Find owner
            res = await session.execute(select(TeamMember).where(TeamMember.email == owner_email))
            owner = res.scalars().first()
            if not owner:
                logger.warning(f"Owner not found: {owner_email}")
                return {"error": f"Owner with email {owner_email} not found"}
            
            project = Project(name=name, status=status, owner_id=owner.id, description=description)
            session.add(project)
            await session.commit()
            await session.refresh(project)
            
            logger.info(f"Project created successfully: id={project.id}")
            return {"id": project.id, "name": project.name, "status": "created"}
            
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        return {"error": f"Failed to create project: {str(e)}"}


@tool
async def create_task(project_id: int, title: str, status: str = "todo", assignee_email: Optional[str] = None, due_date: Optional[datetime] = None):
    """
    Create a new task within a project.
    
    Args:
        project_id: The ID of the project.
        title: The title of the task.
        status: The status of the task (default: "todo").
        assignee_email: The email of the assignee.
        due_date: The due date for the task.
    """
    logger.info(
        "Creating task",
        extra={"extra_data": {"project_id": project_id, "title": title, "assignee": assignee_email}}
    )
    
    try:
        async with AsyncSessionLocal() as session:
            # Verify project exists
            proj_res = await session.execute(select(Project).where(Project.id == project_id))
            if not proj_res.scalars().first():
                logger.warning(f"Project not found: {project_id}")
                return {"error": f"Project with id {project_id} not found"}
            
            assignee_id = None
            if assignee_email:
                res = await session.execute(select(TeamMember).where(TeamMember.email == assignee_email))
                assignee = res.scalars().first()
                if assignee:
                    assignee_id = assignee.id
                else:
                    logger.warning(f"Assignee not found: {assignee_email}")
            
            task = Task(project_id=project_id, title=title, status=status, assignee_id=assignee_id, due_date=due_date)
            session.add(task)
            await session.commit()
            await session.refresh(task)
            
            logger.info(f"Task created successfully: id={task.id}")
            return {"id": task.id, "title": task.title, "status": "created"}
            
    except Exception as e:
        logger.error(f"Failed to create task: {e}", exc_info=True)
        return {"error": f"Failed to create task: {str(e)}"}


@tool
async def update_project(project_id: int, patch: Dict[str, Any]):
    """
    Update an existing project.
    
    Args:
        project_id: The ID of the project to update.
        patch: A dictionary of fields to update.
    """
    logger.info(
        "Updating project",
        extra={"extra_data": {"project_id": project_id, "fields": list(patch.keys())}}
    )
    
    try:
        # Validate patch fields
        invalid_fields = set(patch.keys()) - ALLOWED_PROJECT_FIELDS
        if invalid_fields:
            logger.warning(f"Invalid fields in patch: {invalid_fields}")
            return {"error": f"Invalid fields: {invalid_fields}"}
        
        async with AsyncSessionLocal() as session:
            # Verify project exists
            result = await session.execute(select(Project).where(Project.id == project_id))
            if not result.scalars().first():
                logger.warning(f"Project not found: {project_id}")
                return {"error": f"Project with id {project_id} not found"}
            
            stmt = update(Project).where(Project.id == project_id).values(**patch)
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Project updated successfully: id={project_id}")
            return {"id": project_id, "status": "updated", "changes": patch}
            
    except Exception as e:
        logger.error(f"Failed to update project: {e}", exc_info=True)
        return {"error": f"Failed to update project: {str(e)}"}


@tool
async def update_task(task_id: int, patch: Dict[str, Any]):
    """
    Update an existing task.
    
    Args:
        task_id: The ID of the task to update.
        patch: A dictionary of fields to update.
    """
    logger.info(
        "Updating task",
        extra={"extra_data": {"task_id": task_id, "fields": list(patch.keys())}}
    )
    
    try:
        # Validate patch fields
        invalid_fields = set(patch.keys()) - ALLOWED_TASK_FIELDS
        if invalid_fields:
            logger.warning(f"Invalid fields in patch: {invalid_fields}")
            return {"error": f"Invalid fields: {invalid_fields}"}
        
        async with AsyncSessionLocal() as session:
            # Verify task exists
            result = await session.execute(select(Task).where(Task.id == task_id))
            if not result.scalars().first():
                logger.warning(f"Task not found: {task_id}")
                return {"error": f"Task with id {task_id} not found"}
            
            stmt = update(Task).where(Task.id == task_id).values(**patch)
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Task updated successfully: id={task_id}")
            return {"id": task_id, "status": "updated", "changes": patch}
            
    except Exception as e:
        logger.error(f"Failed to update task: {e}", exc_info=True)
        return {"error": f"Failed to update task: {str(e)}"}

