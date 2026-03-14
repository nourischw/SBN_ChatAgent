"""
SBN ChatAgent - FastAPI Backend
AI chat agent with RAG and internal API integration
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import uvicorn

try:
    from .models import ChatRequest, ChatResponse, QueryResponse, Product
    from .api_client import InternalAPIClient
    from .rag_engine import RAGEngine
    from .logging_config import setup_logging
    from .conversation_manager import conversation_manager
    from .validators import validate_chat_request, sanitize_text, validate_conversation_id
    from .rate_limiter import RateLimitMiddleware
    from .config import settings
except ImportError:
    from models import ChatRequest, ChatResponse, QueryResponse, Product
    from api_client import InternalAPIClient
    from rag_engine import RAGEngine
    from logging_config import setup_logging
    from conversation_manager import conversation_manager
    from validators import validate_chat_request, sanitize_text, validate_conversation_id
    from rate_limiter import RateLimitMiddleware
    from config import settings

# Setup logging
setup_logging(log_level=settings.log_level)
logger = logging.getLogger(__name__)

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

# Rate limiting middleware (configurable via settings)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_window=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window,
    exclude_paths=["/health", "/docs", "/openapi.json"]
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
        rag_engine = RAGEngine(persist_dir=settings.chroma_persist_dir)
    return rag_engine


@app.get("/")
async def root():
    """Serve the frontend chat UI"""
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    api_healthy = await api_client.health_check()

    # Test Ollama connection
    ollama_status = "unknown"
    ollama_models = []
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                ollama_status = "connected"
                ollama_models = [m.get("name") for m in response.json().get("models", [])]
            else:
                ollama_status = "error"
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        ollama_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "api_available": api_healthy,
        "ollama_status": ollama_status,
        "ollama_host": settings.ollama_host,
        "ollama_model": settings.ollama_model,
        "available_models": ollama_models
    }


@app.get("/api/ollama/test")
async def test_ollama():
    """Test Ollama LLM connection and generate a simple response"""
    try:
        engine = get_rag_engine()
        test_response = engine.llm.invoke("Say hello, this is a test.")

        return {
            "success": True,
            "ollama_host": settings.ollama_host,
            "model": settings.ollama_model,
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
    conversation_id = request.conversation_id or "default"
    logger.info(f"Chat request received: conversation_id={conversation_id}, message_length={len(request.message)}")
    
    # Validate input
    is_valid, error_msg = validate_chat_request(
        message=request.message,
        conversation_id=conversation_id,
        history_limit=request.history_limit
    )
    if not is_valid:
        logger.warning(f"Invalid chat request: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Sanitize message
    sanitized_message = sanitize_text(request.message)
    
    try:
        # Add user message to history
        conversation_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=sanitized_message
        )

        # Get conversation history if requested
        context_history = ""
        if request.include_history:
            context_history = conversation_manager.get_formatted_history(
                conversation_id,
                limit=request.history_limit
            )
            logger.debug(f"Including {request.history_limit} messages of history")

        # Query RAG engine
        engine = get_rag_engine()
        result = engine.query(sanitized_message, context_history=context_history)

        # Add assistant response to history
        conversation_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
            sources=result.get("sources")
        )

        # Get conversation stats
        conv_stats = conversation_manager.get_stats()
        msg_count = len(conv_stats.get("messages_per_conversation", {}).get(conversation_id, 0))

        logger.info(f"Chat response generated: {len(result.get('answer', ''))} chars, conversation messages: {msg_count}")
        
        return ChatResponse(
            response=result["answer"],
            conversation_id=conversation_id,
            sources=result.get("sources"),
            history_included=request.include_history,
            message_count=msg_count
        )
    except Exception as e:
        logger.exception(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@app.get("/api/products", response_model=QueryResponse)
async def get_products():
    """Fetch product list from internal API and add to RAG system"""
    logger.info("=== /api/products endpoint called ===")
    try:
        logger.info(f"INTERNAL_API_URL: {api_client.base_url}")
        # Fetch products from internal API
        logger.info("Calling api_client.get_product_list()...")
        products = await api_client.get_product_list()
        logger.info(f"Got {len(products)} products")

        # Convert to dict format for RAG
        product_data = [p.model_dump() for p in products]

        # Add to RAG for future queries
        engine = get_rag_engine()
        engine.add_product_data(product_data)

        logger.info(f"Successfully added {len(products)} products to RAG knowledge base")
        return QueryResponse(
            success=True,
            data=product_data,
            message=f"Retrieved {len(products)} products and added to knowledge base"
        )
    except Exception as e:
        logger.exception(f"Error in /api/products: {str(e)}")
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
        logger.exception(f"Error clearing vector store: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear a specific conversation history"""
    is_valid, error_msg = validate_conversation_id(conversation_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    success = conversation_manager.clear_conversation(conversation_id)
    if success:
        return {"success": True, "message": f"Conversation {conversation_id} cleared"}
    raise HTTPException(status_code=404, detail="Conversation not found")


@app.get("/api/conversations/stats")
async def get_conversation_stats():
    """Get conversation manager statistics"""
    return conversation_manager.get_stats()


if __name__ == "__main__":
    logger.info(f"Starting SBN ChatAgent on {settings.app_host}:{settings.app_port}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
