# Project Upgrades & Architectural Refinements 🚀

This document details the major technical upgrades implemented to transform **Deliberation.ai** into a production-ready, low-latency multi-agent system.

---

## 1. Multi-Agent Orchestration (LangGraph)
We replaced linear scripts with **LangGraph**, enabling a stateful, cyclic workflow.
- **Round-Based Logic**: Users can now select 1-5 rounds of deliberation. The graph dynamically routes between agents and an Arbiter based on the current round state.
- **State Persistence**: The conversation state is maintained across agents, ensuring Round 2 agents have full context of Round 1 critiques.

## 2. Real-Time Streaming Engine (SSE)
To provide a modern "ChatGPT-like" experience, we implemented a robust streaming bridge.
- **Server-Sent Events (SSE)**: The backend now streams tokens via Redis Pub/Sub to a specialized SSE view.
- **Frontend Sync**: `ChatInterface.tsx` was refactored with an asynchronous event listener that handles partial token updates, preventing race conditions.
- **Connection Heartbeats**: Added a 15-second heartbeat (ping) mechanism. This keeps the browser connection alive during the Arbiter's intense synthesis phase, which can take ~60-90s on local hardware.

## 3. Local Model Optimization (M1 Air Tuned)
The system is now specifically optimized for **Apple Silicon (M1/M2/M3)** MacBook Airs using **Ollama**.
- **SLMs (Small Language Models)**: We transitioned from heavy 7B-13B models to high-performance SLMs:
  - **Llama 3.2 1B**: Leading the first round for speed.
  - **Qwen 2.5 1.5B**: Providing technical critiques.
  - **Phi 3 Mini**: Offering specialized insights.
- **Arbiter (Llama 3.2 3B)**: Balanced reasoning for the final synthesis without overwhelming the M1 processor.

## 4. Anti-Hallucination & Logic Shielding
Small models often try to simulate a whole debate in one go. We implemented three layers of protection:
- **Round-Aware Turn Instructions**: Agents are explicitly told if they are the "First Speaker" or a "Reviewer."
- **Strict Prompting**: System prompts now include hard rules: "ONLY speak as yourself" and "DO NOT roleplay other agents."
- **Empty-Bubble Fail-safe**: Every agent node has a fallback message. If a model returns whitespace or fails to stream, a default "Acknowledged, proceeding with analysis" message is sent to prevent UI hang.

## 5. UI & Visibility Refinements
- **Standardized Naming**: Backend agent names were standardized to lowercase to match the results filter.
- **Case-Insensitive Filtering**: The frontend results filter was updated to handle mixed-case model names from different LLM providers.
- **Dynamic Icons**: The UI now correctly attributes icons and labels to local models (🦙, 🧊, Φ) versus cloud models.

---
**Final Status**: Verified stable on M1 Air. All features pushed to [monishsoorya31/deliberation.ai](https://github.com/monishsoorya31/deliberation.ai).
