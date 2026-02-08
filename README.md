# Deliberation.ai ⚡🤖

**Deliberation.ai** is a sophisticated multi-agent consensus engine designed to synthesize high-quality answers through structured AI debate. It pits multiple LLMs against each other to critique, refine, and harmonize perspectives on complex questions.

## 🚀 Latest Upgrades (Feb 8, 2026)

- **Anti-Hallucination Mode**: Agents are now strictly round-aware, preventing them from roleplaying their peers.
- **Dual-Model Support**: Seamlessly switch between OpenAI/Gemini/DeepSeek and Local Ollama models.
- **SSE Stability**: Integrated heartbeat pings to ensure long Arbiter sessions don't time out.
- **Optimized SLMs**: Tuned for 8GB RAM M1/M2 MacBooks using 1B-3B parameters models.

## 🧠 Architectural Deep-Dive
For a detailed look at the LangGraph orchestration, streaming implementation, and model optimizations, see [UPGRADES_DETAIL.md](file:///Users/monishsoorya/Documents/CHAT_AGENTS/UPGRADES_DETAIL.md).

## 📦 Getting Started
...

### Prerequisites
1.  **Docker & Docker Compose**
2.  **Ollama** (for local mode):
    ```bash
    ollama pull llama3.2:1b
    ollama pull qwen2.5:1.5b
    ollama pull phi3:mini
    ollama pull llama3.2:3b
    ```

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/monishsoorya/deliberation.ai.git
    cd deliberation.ai
    ```
2.  Start the services:
    ```bash
    docker-compose up -d
    ```
3.  Access the UI:
    Open [http://localhost:5173](http://localhost:5173) in your browser.

## 🧠 How it Works
1.  **Initiation**: You provide a question.
2.  **Deliberation**: Three distinct agents (Cloud or Local) provide their initial thoughts.
3.  **Critique Loop**: In subsequent rounds, agents review their peers' responses, challenging assumptions and identifying gaps.
4.  **Arbitration**: A final, high-reasoning Arbiter model synthesizes all arguments into a single, definitive consensus answer.

## 🛡 License
MIT License
