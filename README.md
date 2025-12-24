# Voice Agentic AI Platform

A scalable, voice-to-voice AI platform where users interact with dynamically routed AI agents through natural speech.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for frontend apps)
- Python 3.11+ (for backend development)
- API Keys: OpenAI/OpenRouter, Deepgram

### 1. Clone and Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Qdrant (port 6333)
- LiveKit Server (port 7880)

### 3. Run Backend

```bash
cd backend
pip install -e .
python -m src.main
```

### 4. Run Admin Panel

```bash
cd admin-panel
npm install
npm run dev
```

### 5. Run User App

```bash
cd user-app
npm install
npm run dev
```

## Project Structure

```
├── backend/          # FastAPI backend
├── voice_agent/      # LiveKit Agents voice service
├── admin-panel/      # React admin UI
├── user-app/         # React voice interface
└── docker-compose.yml
```

## Documentation

See [Implementation Plan](./docs/implementation_plan.md) for detailed architecture.
