# Deliberation.ai ⚡🤖

**Deliberation.ai** is a sophisticated multi-agent consensus engine designed to synthesize high-quality answers through structured AI debate. It pits multiple LLMs against each other to critique, refine, and harmonize perspectives on complex questions.

## 🚀 Features

- **Multi-Agent Deliberation**: Uses a "Panel of Experts" (Llama 3.2, Qwen 2.5, and Phi 3 or cloud models) to evaluate questions from multiple angles.
- **Adjustable Depth**: Configure 1-5 rounds of deliberation. More rounds lead to deeper critique and more robust consensus.
- **Real-time Streaming**: "ChatGPT-style" token-by-token streaming for a dynamic, live deliberation experience.
- **Local-First (M1 Optimized)**: Fully supports local execution using **Ollama**, optimized specifically for Apple Silicon (M1/M2/M3) MacBook Airs.
- **Aesthetic UI**: A premium, glassmorphic React interface with real-time feedback and state management.

## 🛠 Tech Stack

- **Backend**: Python, Django, Celery, Redis, LangChain, LangGraph.
- **Frontend**: React, TypeScript, Tailwind CSS, Vite.
- **Local Models**: Ollama (llama3.2:1b, qwen2.5:1.5b, phi3:mini, llama3.2:3b).
- **Orchestration**: Docker Compose.

## 📦 Getting Started

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
