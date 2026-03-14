"""
Pydantic models for SBN ChatAgent API
"""
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's chat message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    include_history: bool = Field(default=False, description="Whether to include conversation history in context")
    history_limit: int = Field(default=5, description="Number of previous messages to include in context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="AI assistant's response")
    conversation_id: str = Field(..., description="Conversation ID for context")
    sources: Optional[List[str]] = Field(default=None, description="RAG source documents used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    history_included: bool = Field(default=False, description="Whether conversation history was included in context")
    message_count: int = Field(default=0, description="Total messages in this conversation")


class QueryResponse(BaseModel):
    """Generic response model for data queries"""
    success: bool = Field(..., description="Whether the query was successful")
    data: Any = Field(..., description="Query result data")
    message: Optional[str] = Field(None, description="Optional message or error details")


class Product(BaseModel):
    """Product model"""
    ProdId: int
    ProdNum: Optional[str] = None
    ProdBrandName: Optional[str] = None
    ProdCatgName: Optional[str] = None
    ProdName: Optional[str] = None
    ProdSize: Optional[str] = None
    Qty: Optional[int] = None
    SellingPrice: Optional[Decimal] = None
    ReferencePrice: Optional[Decimal] = None
    ProductCost: Optional[Decimal] = None
    Currency: Optional[str] = None
    ImageURL: Optional[str] = None
    ProdLangLongDesc: Optional[str] = None
    ProdPubToInternet: Optional[bool] = None


class ProductListResponse(BaseModel):
    """Product list response model"""
    success: bool
    data: list[Product]
    cached: bool
    message: str
