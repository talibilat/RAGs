from typing import Annotated, Any, Literal, Optional, List, Dict
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class UserInfo(BaseModel):
    id: int
    role: Literal["admin", "pm", "member"]
    email: str

class ProposedChange(BaseModel):
    action: Literal["create", "update", "delete"]
    table: Literal["projects", "tasks", "team_members"]
    where: Dict[str, Any] = Field(default_factory=dict)
    values: Dict[str, Any] = Field(default_factory=dict)
    reason: str

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_info: Optional[UserInfo]
    intent: Optional[Literal["READ_QUERY", "WRITE_PROPOSAL", "WORKFLOW", "CLARIFY"]]
    proposed_plan: Optional[List[ProposedChange]]
    clarification_needed: Optional[str]
    approved: Optional[bool]
    approval_token: Optional[str]
