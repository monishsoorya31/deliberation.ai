
from celery import shared_task
from agents.graph import agent_graph
from deliberations.models import Conversation, Message
from utils.security import store_api_keys
from utils.stream import publish_update
from langchain_core.messages import HumanMessage

@shared_task
def run_deliberation_task(conversation_id, question, max_rounds):
    # Store keys first (if not already stored separately, but task might run on different worker)
    # Actually, keys should be stored by the View before calling task to ensure they are available.
    # But just in case, we can refresh them or access them here.
    
    # Initialize State
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "current_round": 1,
        "max_rounds": max_rounds,
        # Logic in graph: current_round > max_rounds. 
        # If we want 3 full rounds of debate: max_rounds=3.
        # Nodes: OpenAI -> Gemini -> DeepSeek -> Update (+1).
        # So loop runs 3 times.
        "participants": ["OpenAI", "Gemini", "DeepSeek"],
        "final_answer": None,
        "question": question,
        "conversation_id": conversation_id
    }
    
    # Run Graph
    # We use invoke for synchronous run in Celery worker
    try:
        config = {"configurable": {"thread_id": conversation_id}}
        final_state = agent_graph.invoke(initial_state, config=config)
        
        # Mark conversation as completed
        try:
            convo = Conversation.objects.get(id=conversation_id)
            convo.is_completed = True
            convo.save()
        except:
            pass
            
    except Exception as e:
        # Log error
        publish_update(conversation_id, {
            "type": "error",
            "message": str(e)
        })
        raise e
