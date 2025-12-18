"""Intent classification router with production-ready error handling."""
from typing import Literal
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.core.logging_config import get_logger
from app.agent.llm import get_chat_model

logger = get_logger(__name__)
_router_model = None


def get_router_model() -> BaseChatModel:
    """Create router model with lazy initialization to avoid startup failures."""
    global _router_model
    if _router_model is None:
        _router_model = get_chat_model(temperature=0)
    return _router_model


router_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{messages}"),
    ("system", "Given the conversation above, determine the classification: READ_QUERY, WRITE_PROPOSAL, WORKFLOW, or CLARIFY. Return ONLY the classification string.")
])


async def route_intent(state: AgentState):
    """Analyze the conversation to determine the next step."""
    logger.info("Classifying user intent")
    
    try:
        model = get_router_model()
        chain = router_prompt | model
        response = await chain.ainvoke(state)
        intent = response.content.strip()
        
        # Fallback/Safety
        valid_intents = ["READ_QUERY", "WRITE_PROPOSAL", "WORKFLOW", "CLARIFY"]
        if intent not in valid_intents:
            logger.warning(f"Invalid intent received: '{intent}', defaulting to CLARIFY")
            intent = "CLARIFY"
        
        logger.info(f"Intent classified as: {intent}")
        return {"intent": intent}
        
    except Exception as e:
        logger.error(f"Intent classification failed: {e}", exc_info=True)
        # Default to CLARIFY on error to ask user for more details (or if LLM not configured)
        return {"intent": "CLARIFY"}
