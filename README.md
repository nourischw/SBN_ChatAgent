# SBN ChatAgent

**Author: Nouris**

An AI-powered chat agent integrated with internal product APIs, supporting natural language queries about product catalog using Ollama LLM and RAG (Retrieval-Augmented Generation).

## Features

- 🤖 **Natural Language Queries** - Ask questions in plain English about product data
- 📦 **Product Catalog Integration** - Real-time access to product list from internal APIs
- 🔌 **RAG-Powered** - Retrieval-Augmented Generation using Ollama LLM for accurate responses
- 💬 **Conversation History** - Multi-turn conversations with context awareness
- 🔒 **Input Validation** - Comprehensive input sanitization and validation
- 🛡️ **Rate Limiting** - Protection against abuse (10 req/min per IP)
- 🐳 **Dockerized** - Easy deployment with Docker Compose
- 📊 **Health Checks** - Built-in health monitoring

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| LLM | Ollama (Qwen2.5:0.5b) |
| RAG | LangChain, ChromaDB |
| Frontend | HTML, CSS, JavaScript |
| Container | Docker, Docker Compose |
| Configuration | pydantic-settings |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│   Ollama    │
│  (Chat UI)  │     │  (FastAPI)   │     │ (Qwen LLM)  │
└─────────────┘     └──────────────┘     └─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Product     │
                   │  API         │
                   └──────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose **OR** Python 3.9+
- Ollama installed locally (for LLM inference)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd SBN_ChatAgent

# Copy environment configuration
cp .env.example .env

# Pull the Ollama model (on host machine)
ollama pull qwen2.5:0.5b

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:3030
- API Docs: http://localhost:3030/docs

### Option 2: Local Development

```bash
# Clone the repository
git clone <repository-url>
cd SBN_ChatAgent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Pull the Ollama model
ollama pull qwen2.5:0.5b

# Start Ollama (if not running)
ollama serve

# Run the backend
cd backend
python app.py

# Or with uvicorn directly
uvicorn backend.app:app --host 0.0.0.0 --port 3030 --reload
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Application Settings
APP_HOST=0.0.0.0
APP_PORT=3030
DEBUG=false
LOG_LEVEL=INFO

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b

# Internal API Configuration
INTERNAL_API_URL=http://localhost:8000/api/products
INTERNAL_API_TIMEOUT=10.0

# ChromaDB Configuration
CHROMA_PERSIST_DIR=./data/chroma

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Conversation Settings
MAX_CONVERSATION_HISTORY=10
MAX_MESSAGE_LENGTH=2000
```

## API Endpoints

### Chat Endpoints

#### POST /api/chat
Send a chat message and get AI response.

```bash
curl -X POST http://localhost:3030/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What products are available?",
    "conversation_id": "session-123",
    "include_history": true,
    "history_limit": 5
  }'
```

Response:
```json
{
  "response": "We have several products available...",
  "conversation_id": "session-123",
  "sources": ["Product Name: Widget A..."],
  "history_included": true,
  "message_count": 2,
  "timestamp": "2026-03-15T10:30:00Z"
}
```

#### GET /api/products
Fetch product list from internal API and add to RAG knowledge base.

```bash
curl http://localhost:3030/api/products
```

#### POST /api/ingest
Manually ingest data into RAG system.

```bash
curl -X POST "http://localhost:3030/api/ingest?data_type=product" \
  -H "Content-Type: application/json" \
  -d '[{"ProdName": "Widget", "ProdId": 1}]'
```

#### DELETE /api/vector-store/clear
Clear the RAG knowledge base.

```bash
curl -X DELETE http://localhost:3030/api/vector-store/clear
```

### Conversation Management

#### DELETE /api/conversations/{conversation_id}
Clear a specific conversation history.

```bash
curl -X DELETE http://localhost:3030/api/conversations/session-123
```

#### GET /api/conversations/stats
Get conversation manager statistics.

```bash
curl http://localhost:3030/api/conversations/stats
```

### System Endpoints

#### GET /health
Health check endpoint.

```bash
curl http://localhost:3030/health
```

Response:
```json
{
  "status": "healthy",
  "api_available": true,
  "ollama_status": "connected",
  "ollama_host": "http://localhost:11434",
  "ollama_model": "qwen2.5:0.5b",
  "available_models": ["qwen2.5:0.5b"]
}
```

#### GET /api/ollama/test
Test Ollama LLM connection.

```bash
curl http://localhost:3030/api/ollama/test
```

## Sample Queries

Once products are loaded, try these queries:

- "Show me all products"
- "What products are available in the electronics category?"
- "What are the product prices?"
- "Tell me about product availability"
- "Which products have the highest selling price?"
- "Compare the prices of product A and product B"

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_validators.py -v
```

### Project Structure

```
SBN_ChatAgent/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── rag_engine.py          # RAG implementation
│   ├── api_client.py          # Internal API client
│   ├── models.py              # Pydantic models
│   ├── config.py              # Configuration management
│   ├── validators.py          # Input validation
│   ├── conversation_manager.py # Conversation history
│   ├── rate_limiter.py        # Rate limiting middleware
│   └── logging_config.py      # Logging configuration
├── frontend/
│   └── index.html             # Chat UI
├── tests/
│   ├── test_validators.py     # Validator tests
│   └── test_conversation_manager.py # Conversation tests
├── data/                      # RAG document storage
├── logs/                      # Application logs
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Backend container
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                  # This file
```

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull the required model
ollama pull qwen2.5:0.5b

# Restart Ollama
ollama serve
```

### Docker Issues

```bash
# View container logs
docker-compose logs backend

# Rebuild containers
docker-compose up -d --build

# Check container health
docker-compose ps
```

### Rate Limiting

If you receive HTTP 429 errors:
- Wait for the specified retry period
- Increase `RATE_LIMIT_REQUESTS` or `RATE_LIMIT_WINDOW` in `.env`

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact the development team.
