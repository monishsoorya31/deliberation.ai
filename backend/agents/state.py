
from typing import TypedDict, Annotated, List, Optional
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class AgentState(TypedDict):
    """
    Represents the state of the multi-agent deliberation.
    """
    messages: Annotated[list[BaseMessage], operator.add]
    current_round: int
    max_rounds: int
    participants: list[str] # ["OpenAI", "Gemini", "DeepSeek"]
    final_answer: Optional[str]
    question: str
    conversation_id: str
