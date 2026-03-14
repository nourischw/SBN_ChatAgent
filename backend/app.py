"""
SBN ChatAgent - FastAPI Backend
AI chat agent with RAG and internal API integration
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import uvicorn

try:
    from .models import ChatRequest, ChatResponse, QueryResponse, Product
    from .api_client import InternalAPIClient
    from .rag_engine import RAGEngine
except ImportError:
    from models import ChatRequest, ChatResponse, QueryResponse, Product
    from api_client import InternalAPIClient
    from rag_engine import RAGEngine

# Initialize FastAPI app
app = FastAPI(
    title="SBN ChatAgent",
    description="AI Chat Agent with RAG and Internal API Integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
api_client = InternalAPIClient()
rag_engine = None  # Lazy initialization

# Ensure data directory exists
os.makedirs("./data/chroma", exist_ok=True)


def get_rag_engine() -> RAGEngine:
    """Get or initialize RAG engine"""
    global rag_engine
    if rag_engine is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        rag_engine = RAGEngine(persist_dir=persist_dir)
    return rag_engine


@app.get("/")
async def root():
    """Serve the frontend chat UI"""
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    api_healthy = await api_client.health_check()
    
    # Test Ollama connection
    ollama_status = "unknown"
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/tags", timeout=5.0)
            if response.status_code == 200:
                ollama_status = "connected"
                models = response.json().get("models", [])
                ollama_models = [m.get("name") for m in models]
            else:
                ollama_status = "error"
                ollama_models = []
    except Exception as e:
        ollama_status = f"disconnected: {str(e)}"
        ollama_models = []
    
    return {
        "status": "healthy",
        "api_available": api_healthy,
        "ollama_status": ollama_status,
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "ollama_model": ollama_model,
        "available_models": ollama_models
    }


@app.get("/api/ollama/test")
async def test_ollama():
    """Test Ollama LLM connection and generate a simple response"""
    try:
        engine = get_rag_engine()
        
        # Simple test query without RAG context
        test_response = engine.llm.invoke("Say hello, this is a test.")
        
        return {
            "success": True,
            "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"),
            "response": test_response,
            "message": "Ollama LLM is working correctly!"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to connect to Ollama LLM"
        }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Process user message and return AI response
    Uses RAG with Ollama LLM for intelligent responses based on product data
    """
    try:
        engine = get_rag_engine()
        result = engine.query(request.message)

        return ChatResponse(
            response=result["answer"],
            conversation_id=request.conversation_id or "default",
            sources=result.get("sources")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products", response_model=QueryResponse)
async def get_products():
    """Fetch product list from internal API and add to RAG system"""
    import logging
    logging.info("=== /api/products endpoint called ===")
    try:
        logging.info(f"INTERNAL_API_URL: {api_client.base_url}")
        # Fetch products from internal API
        logging.info("Calling api_client.get_product_list()...")
        products = await api_client.get_product_list()
        logging.info(f"Got {len(products)} products")

        # Convert to dict format for RAG
        product_data = [p.model_dump() for p in products]

        # Add to RAG for future queries
        engine = get_rag_engine()
        engine.add_product_data(product_data)

        return QueryResponse(
            success=True,
            data=product_data,
            message=f"Retrieved {len(products)} products and added to knowledge base"
        )
    except Exception as e:
        import traceback
        logging.error(f"Error in /api/products: {str(e)}")
        logging.error(traceback.format_exc())
        return QueryResponse(
            success=False,
            data=[],
            message=str(e)
        )


@app.post("/api/ingest")
async def ingest_data(data_type: str, data: List[dict]):
    """Manually ingest data into RAG system"""
    try:
        engine = get_rag_engine()
        if data_type == "product":
            engine.add_product_data(data)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        return {"success": True, "message": f"Ingested {len(data)} {data_type} records"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/vector-store/clear")
async def clear_vector_store():
    """Clear the vector store (reset RAG knowledge base)"""
    try:
        engine = get_rag_engine()
        engine.clear_vector_store()
        return {"success": True, "message": "Vector store cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "3030"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug
    )
