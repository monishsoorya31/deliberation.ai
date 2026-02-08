
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import AgentState
from agents.nodes import (
    call_openai_node,
    call_gemini_node,
    call_deepseek_node,
    arbiter_node,
    update_round_node
)

def router(state: AgentState):
    current_round = state.get("current_round", 1)
    max_rounds = state.get("max_rounds", 3)
    
    if current_round > max_rounds:
        return "arbiter"
    return "openai"

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("openai", call_openai_node)
    workflow.add_node("gemini", call_gemini_node)
    workflow.add_node("deepseek", call_deepseek_node)
    workflow.add_node("update_round", update_round_node)
    workflow.add_node("arbiter", arbiter_node)
    
    # Define Edges (Sequential Flow: OpenAI -> Gemini -> DeepSeek -> Update -> Check)
    workflow.set_entry_point("openai") # Start directly with OpenAI? No, need to check round first?
    # Actually, usually we set entry to a router or the first node.
    # Let's set entry to a conditional edge or a dummy start. 
    # But for simplicity, we can let user input handle init. 
    # Default entry: OpenAI.
    
    workflow.add_edge("openai", "gemini")
    workflow.add_edge("gemini", "deepseek")
    workflow.add_edge("deepseek", "update_round")
    
    # Conditional Edge from Update Round
    workflow.add_conditional_edges(
        "update_round",
        router,
        {
            "openai": "openai",
            "arbiter": "arbiter"
        }
    )
    
    workflow.add_edge("arbiter", END)
    
    # Checkpointer
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

agent_graph = build_graph()
