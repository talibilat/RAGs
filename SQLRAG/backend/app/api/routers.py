"""API routes with production-ready error handling and logging."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select

from app.core.auth import create_access_token, get_current_user
from app.core.logging_config import get_logger
from app.core.limiter import limiter
from app.db.session import AsyncSessionLocal

from app.db.models import TeamMember


logger = get_logger(__name__)

router = APIRouter()


# Request/Response Models with Validation
class LoginRequest(BaseModel):
    email: str
    model_config = ConfigDict(extra="ignore")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or '@' not in v:
            raise ValueError('Invalid email format')
        return v.strip().lower()


class ChatRequest(BaseModel):
    thread_id: str
    message: str
    model_config = ConfigDict(extra="ignore")
    
    @field_validator('thread_id')
    @classmethod
    def validate_thread_id(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError('thread_id is required')
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('message cannot be empty')
        if len(v) > 10000:
            raise ValueError('message exceeds maximum length of 10000 characters')
        return v.strip()


class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool
    approval_token: str
    model_config = ConfigDict(extra="ignore")
    
    @field_validator('thread_id')
    @classmethod
    def validate_thread_id(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError('thread_id is required')
        return v.strip()
    
    @field_validator('approval_token')
    @classmethod
    def validate_approval_token(cls, v: str) -> str:
        if not v:
            raise ValueError('approval_token is required')
        return v.strip()


# Routes
@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, req: LoginRequest):
    """Authenticate user by email lookup."""
    logger.info("Login attempt", extra={"extra_data": {"email": req.email}})
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TeamMember).where(TeamMember.email == req.email)
            )
            user = result.scalars().first()
        
        if not user:
            logger.warning("User not found", extra={"extra_data": {"email": req.email}})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = create_access_token(user)
        logger.info(
            "Login successful",
            extra={"extra_data": {"user_id": user.id, "role": user.role}}
        )
        return {
            "token": token,
            "role": user.role,
            "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}
        }
        
    except Exception as e:
        logger.error("Login failed", exc_info=True, extra={"extra_data": {"email": req.email}})
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


@router.post("/chat")
@limiter.limit("30/minute")
async def chat(request: Request, req: ChatRequest, user: TeamMember = Depends(get_current_user)):
    """
    Main chat endpoint.
    1. Updates graph with user message.
    2. Runs graph.
    3. Checks if paused (interrupt).
    """
    logger.info(
        "Chat request received",
        extra={"extra_data": {"thread_id": req.thread_id, "role": user.role, "user_id": user.id}}
    )
    
    try:
        thread_key = f"user:{user.id}:{req.thread_id}"
        config = {"configurable": {"thread_id": thread_key}}
        
        inputs = {
            "messages": [("user", req.message)],
            "user_info": {"id": user.id, "role": user.role, "email": user.email},
        }
        
        graph_app = request.app.state.graph
        results = await graph_app.ainvoke(inputs, config=config)
        
        # Check status
        snapshot = await graph_app.aget_state(config)
        if snapshot and snapshot.next:
            if "write_executor" in snapshot.next:
                if user.role != "admin":
                    logger.info(
                        "Write access denied for non-admin",
                        extra={"extra_data": {"thread_id": req.thread_id, "role": user.role, "user_id": user.id}}
                    )
                    return {
                        "type": "message",
                        "content": (
                            "⚠️ **Access Denied**\n\n"
                            "You don't have sufficient rights to perform this action. "
                            "Please contact an **admin** to make changes to the system.\n\n"
                            f"Your current role: **{user.role}**\n\n"
                            "Required role: **admin**"
                        )
                    }
                
                last_msg = snapshot.values["messages"][-1]
                approval_token = str(uuid.uuid4())
                await graph_app.aupdate_state(
                    config,
                    {"approval_token": approval_token, "approved": None}
                )
                logger.info(
                    "Admin approval required",
                    extra={"extra_data": {"thread_id": req.thread_id, "user_id": user.id}}
                )
                return {
                    "type": "approval_required",
                    "message": last_msg.content,
                    "interrupt_id": "write_executor",
                    "approval_token": approval_token,
                }
        
        # Normal completion
        last_msg = results["messages"][-1]
        logger.info(
            "Chat completed successfully",
            extra={"extra_data": {"thread_id": req.thread_id, "user_id": user.id}}
        )
        return {"type": "message", "content": last_msg.content}
        
    except Exception as e:
        logger.error(
            "Chat endpoint failed",
            exc_info=True,
            extra={"extra_data": {"thread_id": req.thread_id, "user_id": user.id}}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your message. Please try again."
        )


@router.post("/chat/resume")
async def resume(request: Request, req: ResumeRequest, user: TeamMember = Depends(get_current_user)):
    """Resume a paused chat workflow after admin approval/rejection."""
    logger.info(
        "Resume request received",
        extra={"extra_data": {"thread_id": req.thread_id, "approved": req.approved, "role": user.role, "user_id": user.id}}
    )
    
    try:
        thread_key = f"user:{user.id}:{req.thread_id}"
        graph_app = request.app.state.graph
        config = {"configurable": {"thread_id": thread_key}}
        
        snapshot = await graph_app.aget_state(config)
        if not snapshot or not snapshot.next:
            return {"type": "message", "content": "No pending approval for this thread."}
        
        # Double-check role for resume as well
        if user.role != "admin":
            logger.warning(
                "Resume denied for non-admin",
                extra={"extra_data": {"thread_id": req.thread_id, "role": user.role, "user_id": user.id}}
            )
            return {
                "type": "message",
                "content": (
                    "⚠️ **Access Denied**\n\n"
                    "Only admins can approve or reject changes. "
                    "Please contact an **admin** to proceed."
                )
            }
        
        stored_token = snapshot.values.get("approval_token")
        if not stored_token or stored_token != req.approval_token:
            logger.warning(
                "Resume denied due to token mismatch",
                extra={"extra_data": {"thread_id": req.thread_id, "user_id": user.id}}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired approval token",
            )
        
        if not req.approved:
            await graph_app.aupdate_state(config, {"approved": False, "approval_token": None})
            logger.info("Change rejected by admin", extra={"extra_data": {"thread_id": req.thread_id}})
            return {"type": "message", "content": "Change rejected. No actions were executed."}
        else:
            await graph_app.aupdate_state(config, {"approved": True, "approval_token": None})
            logger.info("Change approved by admin", extra={"extra_data": {"thread_id": req.thread_id}})
        
        # Continue execution
        results = await graph_app.ainvoke(None, config=config)
        
        last_msg = results["messages"][-1]
        logger.info(
            "Resume completed successfully",
            extra={"extra_data": {"thread_id": req.thread_id, "user_id": user.id}}
        )
        return {"type": "message", "content": last_msg.content}
        
    except Exception as e:
        logger.error(
            "Resume endpoint failed",
            exc_info=True,
            extra={"extra_data": {"thread_id": req.thread_id, "user_id": user.id}}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while resuming the workflow. Please try again."
        )
