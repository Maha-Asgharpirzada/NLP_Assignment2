# ShopEasy Customer Support Chatbot

A fully local, production-style conversational AI system built for CS 4063 - Natural Language Processing.

## Business Use Case
ShopEasy is an e-commerce customer support chatbot that handles:
- Order status and tracking inquiries
- Returns and refunds (30-day policy)
- Product information and availability
- Complaint handling and human escalation

## System Architecture
```
Browser (HTML/JS)
      ↕ WebSocket
FastAPI Server (main.py)
      ↕
Conversation Manager (conversation_manager.py)
      ↕
Sessions Store (sessions.py)
      ↕
LLM Engine (llm_engine.py)
      ↕
Ollama → Qwen 2.5 1.5B (local CPU inference)
```

## Tech Stack
- **Model**: Qwen 2.5 1.5B (GGUF quantized via Ollama)
- **Inference**: Ollama (llama.cpp backend)
- **Backend**: FastAPI + WebSocket
- **Frontend**: Vanilla HTML/JS
- **Containerization**: Docker + docker-compose

## Model Selection
Qwen 2.5 1.5B was selected for:
- Small memory footprint (~1GB)
- Strong instruction-following at its size
- CPU-friendly inference via Ollama
- No GPU required

## Context Memory Management
A **sliding window** scheme is used via Python's `deque(maxlen=10)`. This keeps the last 10 conversation turns in context, automatically dropping older turns. This prevents context window overflow while preserving conversational continuity.

## Performance Benchmarks
Tested on Apple MacBook (CPU only, Qwen 2.5 1.5B):

| Prompt                        | Time to First Token | Total Time | Tokens | Tokens/sec |
|-------------------------------|-------------------|------------|--------|------------|
| What is your return policy?   | 0.62s             | 11.53s     | 233    | 20.2       |
| I want to track my order      | 0.26s             | 11.57s     | 269    | 23.2       |
| Can I get a refund?           | 0.26s             | 2.61s      | 51     | 19.5       |
| What products do you sell?    | 0.38s             | 4.91s      | 80     | 16.3       |
| My package is late            | 0.31s             | 1.91s      | 39     | 20.4       |

**Average time to first token: 0.37s**  
**Average tokens/sec: 19.9**

## Setup Instructions

### Prerequisites
- Python 3.11+
- Docker + docker-compose
- Ollama installed

### 1. Install and start Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b
ollama serve
```

### 2. Run with Docker
```bash
docker-compose up --build
```

### 3. Run without Docker
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Open the frontend
Open `frontend/index.html` in your browser.

## API Reference

### Health Check
```
GET http://localhost:8000/health
Response: {"status": "ok"}
```

### WebSocket Chat
```
WS ws://localhost:8000/ws/chat

Send:    {"message": "What is your return policy?"}
Receive: {"type": "token", "content": "Our"}
         {"type": "token", "content": " return"}
         {"type": "done"}

Reset:   {"reset": true}
```

## Example Dialogues

**Return inquiry:**
> User: I want to return a jacket I bought last week  
> Bot: I can help with that! Our return policy allows returns within 30 days of purchase. Could you provide your order number so I can assist further?

**Out of scope:**
> User: Can you recommend a good restaurant?  
> Bot: Let me connect you to a human agent for that.

**Multi-turn:**
> User: I haven't received my order  
> Bot: I'm sorry to hear that. Could you share your order number?  
> User: It's 12345  
> Bot: Thank you. I'm unable to look up live order data, but I'd recommend checking your confirmation email for tracking info, or I can connect you to a human agent.

## Known Limitations
- No live order database — cannot fetch real order statuses
- Response time varies (1-12s) depending on response length
- In-memory session storage resets on server restart
- Single machine only — not horizontally scalable in current form
- CPU inference is slower than GPU; not suitable for high-traffic production

## Project Structure
```
customer-support-chatbot/
├── backend/
│   ├── main.py                  # FastAPI app + WebSocket endpoint
│   ├── conversation_manager.py  # Prompt orchestration + memory
│   ├── llm_engine.py            # Ollama streaming client
│   ├── sessions.py              # In-memory session store
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── index.html               # Chat UI
├── docker-compose.yml
├── postman_collection.json
└── README.md
```
