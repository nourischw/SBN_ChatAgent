# SBN_ChatAgent

**Author: Nouris**

An AI-powered chat agent integrated with internal product APIs, supporting natural language queries about product catalog using Ollama LLM and RAG.

## Features

- 🤖 **Natural Language Queries** - Ask questions in plain English about product data
- 📦 **Product Catalog Integration** - Real-time access to product list from internal APIs
- 🔌 **RAG-Powered** - Retrieval-Augmented Generation using Ollama LLM for accurate responses
- 🐳 **Dockerized** - Easy deployment with Docker Compose

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| LLM | Ollama (Qwen2.5:0.5b) |
| RAG | LangChain, ChromaDB |
| Frontend | HTML, CSS, JavaScript |
| Container | Docker, Docker Compose |
| APIs | REST APIs (Product List) |

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

## Prerequisites

- Docker & Docker Compose
- Ollama installed locally (for LLM inference)
- Python 3.9+ (for local development)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SBN_ChatAgent
```

### 2. Pull the Ollama Model

```bash
ollama pull qwen2.5:0.5b
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your internal API URL
```

### 4. Start with Docker Compose

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send a chat message and get AI response |
| `/api/products` | GET | Fetch product list and add to RAG knowledge base |
| `/api/ingest` | POST | Manually ingest product data into RAG |
| `/api/vector-store/clear` | DELETE | Clear the RAG knowledge base |
| `/health` | GET | Health check endpoint |

## Example Usage

### Chat API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What products are available in the electronics category?"}'
```

### Load Products

```bash
curl http://localhost:8000/api/products
```

### Sample Queries

- "Show me all products"
- "What products are available in the electronics category?"
- "What are the product prices?"
- "Tell me about product availability"
- "Which products have the highest selling price?"

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
python backend/app.py
```

### Running Tests

```bash
pytest tests/
```

## Project Structure

```
SBN_ChatAgent/
├── backend/
│   ├── app.py            # FastAPI application
│   ├── rag_engine.py     # RAG implementation
│   ├── api_client.py     # Internal API client
│   └── models.py         # Pydantic models
├── frontend/
│   └── index.html        # Chat UI
├── data/                 # RAG document storage
├── docker-compose.yml    # Docker orchestration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server host | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5:0.5b` |
| `INTERNAL_API_URL` | Internal API base URL | `http://localhost:8000/api/products` |
| `CHROMA_PERSIST_DIR` | ChromaDB persistence directory | `./data/chroma` |
| `APP_HOST` | Application host | `0.0.0.0` |
| `APP_PORT` | Application port | `8000` |

## Data Flow

1. **Load Products**: Call `/api/products` to fetch product list from internal API
2. **RAG Ingestion**: Products are automatically added to the ChromaDB vector store
3. **Chat Query**: User asks questions via `/api/chat`
4. **RAG Retrieval**: Relevant product documents are retrieved from vector store
5. **LLM Response**: Ollama LLM generates response based on retrieved context

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact the development team.
