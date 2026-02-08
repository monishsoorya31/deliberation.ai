
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
        "openai": "llama 3.2" if not keys.get("openai") else "openai",
        "gemini": "qwen 2.5" if not keys.get("gemini") else "gemini",
        "deepseek": "phi 3" if not keys.get("deepseek") else "deepseek",
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
    
    # Lead Agent (Usually Llama in Round 1) gets a special turn instruction
    turn_instruction = "You are the FIRST speaker. Provide an initial analysis." if state["current_round"] == 1 else "Review the discussion so far."
    
    prompt = DELIBERATION_PROMPT.format(
        agent_name=agent_name,
        peers=peers,
        question=state["question"],
        round_number=state["current_round"],
        max_rounds=state["max_rounds"],
        turn_instruction=turn_instruction
    )
    
    messages = [SystemMessage(content=prompt)] + state["messages"]
    
    # Stream the response
    content = ""
    convo_id = state["conversation_id"]
    round_num = state["current_round"]
    
    try:
        for chunk in llm.stream(messages):
            token = chunk.content
            content += token
            publish_chunk(convo_id, agent_name, token, round_num)
        
        if not content.strip():
            content = "Acknowledged. Proceeding with the analysis."
            publish_chunk(convo_id, agent_name, content, round_num)

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
            turn_instruction = "Review the previous agent's findings."
            prompt = DELIBERATION_PROMPT.format(
                agent_name=agent_name,
                peers=peers,
                question=state["question"],
                round_number=state["current_round"],
                max_rounds=state["max_rounds"],
                turn_instruction=turn_instruction
            )

            # Format history for Gemini
            history_text = "\n".join([f"{m.name if hasattr(m, 'name') else 'Participant'}: {m.content}" for m in state["messages"]])
            payload = f"{prompt}\n\nDISCUSSION HISTORY:\n{history_text}"
            
            # Stream Gemini
            content = ""
            convo_id = state["conversation_id"]
            round_num = state["current_round"]
            
            for chunk in client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=payload
            ):
                token = chunk.text
                content += token
                publish_chunk(convo_id, agent_name, token, round_num)
                
            if not content.strip():
                content = "I agree with the consensus and have nothing further to add."
                publish_chunk(convo_id, agent_name, content, round_num)

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
            turn_instruction = "Review the previous agent's findings."
            prompt = DELIBERATION_PROMPT.format(
                agent_name=agent_name,
                peers=peers,
                question=state["question"],
                round_number=state["current_round"],
                max_rounds=state["max_rounds"],
                turn_instruction=turn_instruction
            )
            messages = [SystemMessage(content=prompt)] + state["messages"]
            
            # Stream Local Gemini (Qwen)
            content = ""
            convo_id = state["conversation_id"]
            round_num = state["current_round"]
            for chunk in llm.stream(messages):
                token = chunk.content
                content += token
                publish_chunk(convo_id, agent_name, token, round_num)
                
            if not content.strip():
                content = "I agree with the consensus and have nothing further to add."
                publish_chunk(convo_id, agent_name, content, round_num)

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
    turn_instruction = "Review the perspectives from your peers."
    prompt = DELIBERATION_PROMPT.format(
        agent_name=agent_name,
        peers=peers,
        question=state["question"],
        round_number=state["current_round"],
        max_rounds=state["max_rounds"],
        turn_instruction=turn_instruction
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    
    # Stream DeepSeek
    content = ""
    convo_id = state["conversation_id"]
    round_num = state["current_round"]
    try:
        for chunk in llm.stream(messages):
            token = chunk.content
            content += token
            publish_chunk(convo_id, agent_name, token, round_num)
            
        if not content.strip():
            content = "My analysis aligns with the current debate."
            publish_chunk(convo_id, agent_name, content, round_num)

        response_msg = AIMessage(content=content, name=agent_name)
    except Exception as e:
        content = f"Error (DeepSeek/Local): {str(e)}"
        response_msg = AIMessage(content=content, name=agent_name)
    
    save_and_publish(state, agent_name, content)
    return {"messages": [response_msg]}


def arbiter_node(state: AgentState):
    keys = get_keys(state)
    openai_key = keys.get("openai") # Use OpenAI for Arbiter usually
    
    agent_name = "Arbiter"
    
    names = get_agent_names(keys)
    participants = f"{names['openai']}, {names['gemini']}, {names['deepseek']}"
    
    convo_id = state.get("conversation_id")
    try:
        if openai_key:
            llm = ChatOpenAI(
                api_key=openai_key,
                model="gpt-4o",
                temperature=0.2
            )
            prompt = ARBITER_PROMPT.format(
                participants=participants,
                question=state["question"]
            )
            # Standard history formatting for all models
            history_text = "\n".join([f"{m.name if hasattr(m, 'name') else 'Participant'}: {m.content}" for m in state["messages"]])
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"DISCUSSION HISTORY:\n{history_text}\n\nFinal Synthesis:")
            ]
            
            # Stream Cloud Arbiter
            content = ""
            for chunk in llm.stream(messages):
                token = chunk.content
                content += token
                publish_chunk(convo_id, agent_name, token, 0)
            
            if not content.strip():
                content = "I have reviewed the deliberation and synthesized the consensus as provided in the summary."
                publish_chunk(convo_id, agent_name, content, 0)
                
            response_msg = AIMessage(content=content, name=agent_name)
        elif keys.get("gemini"):
            print("DEBUG: OpenAI missing for Arbiter, falling back to Gemini")
            client = genai.Client(api_key=keys.get("gemini"))
            prompt = ARBITER_PROMPT.format(
                participants=participants,
                question=state["question"]
            )
            
            # Format history for Gemini
            history_text = "\n".join([f"{m.name if hasattr(m, 'name') else 'Participant'}: {m.content}" for m in state["messages"]])
            payload = f"{prompt}\n\nDISCUSSION HISTORY:\n{history_text}\n\nFinal Synthesis:"

            # Stream Gemini Arbiter
            content = ""
            for chunk in client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=payload
            ):
                token = chunk.text
                content += token
                publish_chunk(convo_id, agent_name, token, 0)
            
            if not content.strip():
                content = "I have reviewed the deliberation and synthesized the consensus as provided in the summary."
                publish_chunk(convo_id, agent_name, content, 0)

            response_msg = AIMessage(content=content, name=agent_name)
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
            # Standard history formatting for Local Arbiter
            history_text = "\n".join([f"{m.name if hasattr(m, 'name') else 'Participant'}: {m.content}" for m in state["messages"]])
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"DISCUSSION HISTORY:\n{history_text}\n\nFinal Synthesis:")
            ]
            
            # Stream Local Arbiter
            content = ""
            for chunk in llm.stream(messages):
                token = chunk.content
                content += token
                publish_chunk(convo_id, agent_name, token, 0)
                
            if not content.strip():
                content = "I have reviewed the deliberation and synthesized the consensus as provided in the summary."
                publish_chunk(convo_id, agent_name, content, 0)

            response_msg = AIMessage(content=content, name=agent_name)

        # Save to DB with round 0
        try:
            convo = Conversation.objects.get(id=convo_id)
            Message.objects.create(
                conversation=convo,
                agent_name=agent_name.lower(),
                content=content,
                round_number=0
            )
        except Exception as e:
            print(f"Error saving arbiter message: {e}")

        publish_update(convo_id, {
            "type": "final",
            "result": content
        })
        return {"messages": [response_msg], "final_answer": content}
            
    except Exception as e:
        print(f"Error in Arbiter: {str(e)}")
        error_msg = f"Arbiter Error: {str(e)}"
        publish_update(convo_id, {
            "type": "final",
            "result": error_msg
        })
        return {"messages": [AIMessage(content=error_msg, name=agent_name)], "final_answer": error_msg}


def update_round_node(state: AgentState):
    new_round = state["current_round"] + 1
    # Publish logic for round update? Maybe
    publish_update(state.get("conversation_id"), {
        "type": "round_update",
        "round": new_round
    })
    return {"current_round": new_round}
