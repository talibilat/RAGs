"""LangGraph workflow for SQLRAG agent with production-ready error handling."""
import json
import logging
from pathlib import Path
from typing import Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage, HumanMessage

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.exceptions import LLMError
from app.agent.llm import get_chat_model
from app.agent.state import AgentState, ProposedChange
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.router import route_intent
from app.agent.tools_read import READ_TOOLS
from app.agent.tools_write import create_project, create_task, update_project, update_task

logger = get_logger(__name__)
_router_model = None
_read_model = None
_write_model = None

# --- Model Factory Functions (Lazy Initialization) ---

def get_read_model():
    """Get the Azure model with read tools bound."""
    global _read_model
    if _read_model is None:
        _read_model = get_chat_model(temperature=0).bind_tools(READ_TOOLS)
    return _read_model


def get_write_model():
    """Get the Azure model with write tools bound."""
    global _write_model
    if _write_model is None:
        write_tools = [create_project, create_task, update_project, update_task]
        _write_model = get_chat_model(temperature=0).bind_tools(write_tools)
    return _write_model


# --- Nodes ---

async def session_guard(state: AgentState):
    """Ensure user info is present. Real app would validate token here."""
    logger.debug("Session guard executed")
    if not state.get("user_info"):
        logger.warning("Missing user info in state; denying execution")
        return {"messages": [AIMessage(content="Authentication required to continue.")]}


async def read_executor(state: AgentState):
    """Execute read tools and generate a response."""
    logger.info("Executing read executor")
    try:
        model = get_read_model()
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await model.ainvoke(messages)
        logger.debug("Read executor completed successfully")
        return {"messages": [response]}
    except LLMError as e:
        logger.error(f"Read executor failed: {e}", exc_info=True)
        error_msg = AIMessage(
            content=(
                "LLM is not configured. Set `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` "
                "(or `OPENAI_API_KEY`) in `backend/.env` and restart the backend."
            )
        )
        return {"messages": [error_msg]}
    except Exception as e:
        logger.error(f"Read executor failed: {e}", exc_info=True)
        error_msg = AIMessage(content="I encountered an error while processing your request. Please try again.")
        return {"messages": [error_msg]}


# Tool node for executing read tools
read_tool_node = ToolNode(READ_TOOLS)


def should_continue_read(state: AgentState) -> Literal["read_tools", "end"]:
    """Check if we need to execute tools or can end."""
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.debug(f"Continuing to read_tools, found {len(last_message.tool_calls)} tool calls")
        return "read_tools"
    return "end"


async def read_continue(state: AgentState):
    """Continue after tool execution - let the model process tool results."""
    logger.debug("Continuing read execution after tool calls")
    try:
        model = get_read_model()
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await model.ainvoke(messages)
        return {"messages": [response]}
    except LLMError as e:
        logger.error(f"Read continue failed: {e}", exc_info=True)
        error_msg = AIMessage(
            content=(
                "LLM is not configured. Set `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` "
                "(or `OPENAI_API_KEY`) in `backend/.env` and restart the backend."
            )
        )
        return {"messages": [error_msg]}
    except Exception as e:
        logger.error(f"Read continue failed: {e}", exc_info=True)
        error_msg = AIMessage(content="I encountered an error processing the results. Please try again.")
        return {"messages": [error_msg]}


async def write_planner(state: AgentState):
    """Propose a write plan based on the user's request."""
    logger.info("Executing write planner")
    try:
        model = get_chat_model(temperature=0)
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        messages.append(SystemMessage(content="Analyze the request and produce a Proposed Change Plan in JSON format. Then ask for approval."))
        
        response = await model.ainvoke(messages)
        logger.debug("Write planner completed successfully")
        return {"messages": [response]}
    except LLMError as e:
        logger.error(f"Write planner failed: {e}", exc_info=True)
        error_msg = AIMessage(
            content=(
                "LLM is not configured. Set `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` "
                "(or `OPENAI_API_KEY`) in `backend/.env` and restart the backend."
            )
        )
        return {"messages": [error_msg]}
    except Exception as e:
        logger.error(f"Write planner failed: {e}", exc_info=True)
        error_msg = AIMessage(content="I encountered an error while planning the changes. Please try again.")
        return {"messages": [error_msg]}


async def write_executor(state: AgentState):
    """Execute the approved plan."""
    logger.info("Executing write executor")
    try:
        approved = state.get("approved")
        if approved is not True:
            logger.warning("Write executor invoked without approval")
            return {
                "messages": [
                    AIMessage(
                        content="Write operations were not approved. No changes were executed."
                    )
                ]
            }

        model = get_write_model()
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        messages.append(SystemMessage(content="The user has approved the plan. Execute the changes now using the available tools."))
        
        response = await model.ainvoke(messages)
        logger.debug("Write executor completed successfully")
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Write executor failed: {e}", exc_info=True)
        error_msg = AIMessage(content="I encountered an error while executing the changes. Please try again.")
        return {"messages": [error_msg]}


# Tool node for write tools
write_tools_list = [create_project, create_task, update_project, update_task]
write_tool_node = ToolNode(write_tools_list)


def should_continue_write(state: AgentState) -> Literal["write_tools", "end"]:
    """Check if we need to execute write tools or can end."""
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.debug(f"Continuing to write_tools, found {len(last_message.tool_calls)} tool calls")
        return "write_tools"
    return "end"


async def write_continue(state: AgentState):
    """Continue after write tool execution."""
    logger.debug("Continuing write execution after tool calls")
    try:
        model = get_write_model()
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await model.ainvoke(messages)
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Write continue failed: {e}", exc_info=True)
        error_msg = AIMessage(content="I encountered an error after executing changes. Please verify the results.")
        return {"messages": [error_msg]}


# --- Conditional Edges ---

def route_from_intent(state: AgentState):
    """Route based on the classified intent."""
    intent = state.get("intent")
    logger.debug(f"Routing based on intent: {intent}")
    if intent == "READ_QUERY":
        return "read_executor"
    elif intent == "WRITE_PROPOSAL":
        return "write_planner"
    elif intent == "WORKFLOW":
        return "write_planner"
    elif intent == "CLARIFY":
        return "read_executor"
    return "read_executor"

# --- Graph ---

workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("session_guard", session_guard)
workflow.add_node("router", route_intent)
workflow.add_node("read_executor", read_executor)
workflow.add_node("read_tools", read_tool_node)
workflow.add_node("read_continue", read_continue)
workflow.add_node("write_planner", write_planner)
workflow.add_node("write_executor", write_executor)
workflow.add_node("write_tools", write_tool_node)
workflow.add_node("write_continue", write_continue)

# Initial flow
workflow.add_edge(START, "session_guard")
workflow.add_edge("session_guard", "router")

# Route from intent
workflow.add_conditional_edges(
    "router",
    route_from_intent
)

# Read flow with tool loop
workflow.add_conditional_edges(
    "read_executor",
    should_continue_read,
    {
        "read_tools": "read_tools",
        "end": END
    }
)
workflow.add_edge("read_tools", "read_continue")
workflow.add_conditional_edges(
    "read_continue",
    should_continue_read,
    {
        "read_tools": "read_tools",
        "end": END
    }
)

# Write flow
workflow.add_edge("write_planner", "write_executor")

# Write executor with tool loop
workflow.add_conditional_edges(
    "write_executor",
    should_continue_write,
    {
        "write_tools": "write_tools",
        "end": END
    }
)
workflow.add_edge("write_tools", "write_continue")
workflow.add_conditional_edges(
    "write_continue",
    should_continue_write,
    {
        "write_tools": "write_tools",
        "end": END
    }
)

# --- Graph Initialization ---

async def create_graph(checkpointer=None):
    """Build and compile the graph with persistent checkpointer."""
    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        logger.warning("No checkpointer provided; falling back to in-memory checkpointer")
        checkpointer = MemorySaver()

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["write_executor"]
    )
