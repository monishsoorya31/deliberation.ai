
from typing import Dict, Any, List
from google import genai
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from django.conf import settings

# Local imports
from utils.security import get_api_keys
from utils.stream import publish_update, publish_chunk
from agents.prompts import DELIBERATION_PROMPT, ARBITER_PROMPT
from agents.state import AgentState

# Django imports (Needs to be run inside Django context)
try:
    from deliberations.models import Message, Conversation
except ImportError:
    pass # Handle potential import error if run outside Django context

def save_and_publish(state: AgentState, agent_name: str, content: str):
    conversation_id = state.get("conversation_id")
    round_num = state.get("current_round", 0)
    
    if not conversation_id:
        return

    # Save to DB
    try:
        convo = Conversation.objects.get(id=conversation_id)
        msg = Message.objects.create(
            conversation=convo,
            agent_name=agent_name.lower(),
            content=content,
            round_number=round_num
        )
    except Exception as e:
        print(f"Error saving message: {e}")

    # Publish to Redis
    publish_update(conversation_id, {
        "type": "message",
        "agent": agent_name,
        "content": content,
        "round": round_num
    })

def get_keys(state: AgentState) -> Dict[str, str]:
    conversation_id = state.get("conversation_id")
    if not conversation_id:
        return {}
    return get_api_keys(conversation_id)

def get_agent_names(keys: Dict[str, str]) -> Dict[str, str]:
    return {
        "openai": "OpenAI" if keys.get("openai") else "Llama 3.2",
        "gemini": "Gemini" if keys.get("gemini") else "Qwen 2.5",
        "deepseek": "DeepSeek" if keys.get("deepseek") else "Phi 3",
    }

def call_openai_node(state: AgentState):
    keys = get_keys(state)
    openai_key = keys.get("openai")
    
    names = get_agent_names(keys)
    agent_name = names["openai"]
    
    if not openai_key:
        print(f"DEBUG: OpenAI key missing, attempt Local Model ({agent_name})")
        llm = ChatOllama(
            model="llama3.2:1b",
            base_url="http://host.docker.internal:11434",
            temperature=0.7
        )
    else:
        llm = ChatOpenAI(api_key=openai_key, model="gpt-4o", temperature=0.7)
    
    peers = f"{names['gemini']}, {names['deepseek']}"
    prompt = DELIBERATION_PROMPT.format(
        agent_name=agent_name,
        peers=peers,
        question=state["question"],
        round_number=state["current_round"],
        max_rounds=state["max_rounds"]
    )
    
    messages = [SystemMessage(content=prompt)] + state["messages"]
    
    # Stream the response
    content = ""
    convo_id = state["conversation_id"]
    round_num = state["current_round"]
    
    try:
        for chunk in llm.stream(messages):
            # LangChain Ollama and OpenAI return chunks with .content attribute
            token = chunk.content
            content += token
            publish_chunk(convo_id, agent_name, token, round_num)
        
        response_msg = AIMessage(content=content, name=agent_name)
    except Exception as e:
        content = f"Local Error: {str(e)}"
        response_msg = AIMessage(content=content, name=agent_name)
    
    save_and_publish(state, agent_name, content)
    return {"messages": [response_msg]}

def call_gemini_node(state: AgentState):
    keys = get_keys(state)
    gemini_key = keys.get("gemini")
    
    names = get_agent_names(keys)
    agent_name = names["gemini"]
    
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            peers = f"{names['openai']}, {names['deepseek']}"
            prompt = DELIBERATION_PROMPT.format(
                agent_name=agent_name,
                peers=peers,
                question=state["question"],
                round_number=state["current_round"],
                max_rounds=state["max_rounds"]
            )

            formatted_messages = []
            for m in state["messages"]:
                if isinstance(m, HumanMessage):
                    formatted_messages.append({"role": "user", "content": m.content})
                elif isinstance(m, AIMessage):
                    formatted_messages.append({"role": "model", "content": m.content})
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt + "\n\nConversation so far:\n" + str(formatted_messages)
            )
            content = response.text
            response_msg = AIMessage(content=content, name=agent_name)
        except Exception as e:
            content = f"Gemini Error: {str(e)}"
            response_msg = AIMessage(content=content, name=agent_name)
    else:
        print(f"DEBUG: Gemini key missing, using Local ({agent_name})")
        try:
            llm = ChatOllama(
                model="qwen2.5:1.5b",
                base_url="http://host.docker.internal:11434",
                temperature=0.7
            )
            peers = f"{names['openai']}, {names['deepseek']}"
            prompt = DELIBERATION_PROMPT.format(
                agent_name=agent_name,
                peers=peers,
                question=state["question"],
                round_number=state["current_round"],
                max_rounds=state["max_rounds"]
            )
            messages = [SystemMessage(content=prompt)] + state["messages"]
            response = llm.invoke(messages)
            content = response.content
            response_msg = AIMessage(content=content, name=agent_name)
        except Exception as e:
            content = f"Local Error ({agent_name}): {str(e)}"
            response_msg = AIMessage(content=content, name=agent_name)

    save_and_publish(state, agent_name, content)
    return {"messages": [response_msg]}

def call_deepseek_node(state: AgentState):
    keys = get_keys(state)
    deepseek_key = keys.get("deepseek")
    
    names = get_agent_names(keys)
    agent_name = names["deepseek"]
    
    if deepseek_key:
        # Using OpenAI compatible endpoint for DeepSeek V3/R1
        llm = ChatOpenAI(
            api_key=deepseek_key, 
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat", 
            temperature=0.7
        )
    else:
        print(f"DEBUG: DeepSeek key missing, using Local ({agent_name})")
        llm = ChatOllama(
            model="phi3:mini", 
            base_url="http://host.docker.internal:11434",
            temperature=0.7
        )
    
    peers = f"{names['openai']}, {names['gemini']}"
    prompt = DELIBERATION_PROMPT.format(
        agent_name=agent_name,
        peers=peers,
        question=state["question"],
        round_number=state["current_round"],
        max_rounds=state["max_rounds"]
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    try:
        response = llm.invoke(messages)
        response.name = agent_name
        content = response.content
    except Exception as e:
        content = f"Error (DeepSeek/Local): {str(e)}"
        response = AIMessage(content=content, name=agent_name)
    
    save_and_publish(state, agent_name, content)
    return {"messages": [response]}


def arbiter_node(state: AgentState):
    keys = get_keys(state)
    openai_key = keys.get("openai") # Use OpenAI for Arbiter usually
    
    agent_name = "Arbiter"
    
    names = get_agent_names(keys)
    participants = f"{names['openai']}, {names['gemini']}, {names['deepseek']}"
    
    try:
        if openai_key:
            llm = ChatOpenAI(api_key=openai_key, model="gpt-4o", temperature=0.2)
            prompt = ARBITER_PROMPT.format(
                participants=participants,
                question=state["question"]
            )
            messages = [SystemMessage(content=prompt)] + state["messages"]
            response = llm.invoke(messages)
            content = response.content
        elif keys.get("gemini"):
            print("DEBUG: OpenAI missing for Arbiter, falling back to Gemini")
            client = genai.Client(api_key=keys.get("gemini"))
            prompt = ARBITER_PROMPT.format(
                participants=participants,
                question=state["question"]
            )
            formatted_history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt + "\n\nFull History:\n" + formatted_history
            )
            content = response.text
        else:
            print("DEBUG: Cloud keys missing, using Local (Llama 3.2 3B) for Arbiter")
            llm = ChatOllama(
                model="llama3.2:3b",
                base_url="http://host.docker.internal:11434",
                temperature=0.2
            )
            prompt = ARBITER_PROMPT.format(
                participants=participants,
                question=state["question"]
            )
            messages = [SystemMessage(content=prompt)] + state["messages"]
            response = llm.invoke(messages)
            content = response.content
            save_and_publish(state, agent_name, content)
            publish_update(state.get("conversation_id"), {
                "type": "final",
                "result": content
            })
            return {"messages": [AIMessage(content=content, name="Arbiter")], "final_answer": content}
    except Exception as e:
        print(f"Error in Arbiter: {str(e)}")
        error_msg = f"Arbiter Error: {str(e)}"
        # Even on error, publish an update to indicate completion
        publish_update(state.get("conversation_id"), {
            "type": "final",
            "result": error_msg
        })
        return {"messages": [AIMessage(content=error_msg, name="Arbiter")], "final_answer": error_msg}


def update_round_node(state: AgentState):
    new_round = state["current_round"] + 1
    # Publish logic for round update? Maybe
    publish_update(state.get("conversation_id"), {
        "type": "round_update",
        "round": new_round
    })
    return {"current_round": new_round}
