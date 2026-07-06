"""
Pydantic models for the RAG API.

These models define the request/response schemas for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class LLMProvider(str, Enum):
    """Available LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE_LOCAL = "huggingface_local"
    HUGGINGFACE_API = "huggingface_api"


# ============= Query Endpoint =============

class QueryRequest(BaseModel):
    """Request model for the /query endpoint."""
    query: str = Field(
        ..., 
        min_length=1,
        max_length=500, 
        description="The question to ask the knowledge base"
    )
    k: int = Field(default=3, ge=1, le=10, description="Number of documents to retrieve")
    provider: LLMProvider = Field(
        default=LLMProvider.GEMINI,
        description="LLM provider to use for answer generation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the resolution target for a P1 incident?",
                "k": 3,
                "provider": "gemini"
            }
        }


class SourceDocument(BaseModel):
    """A source document returned with the answer."""
    content: str = Field(..., description="Content of the source document")
    source: str = Field(..., description="Name of the source file")
    chunk_index: Optional[int] = Field(None, description="Index of chunk if document was chunked")
    relevance_score: Optional[float] = Field(None, description="Relevance score from vector search")


class QueryResponse(BaseModel):
    """Response model for the /query endpoint."""
    answer: str = Field(..., description="Generated answer from the LLM")
    sources: List[SourceDocument] = Field(default_factory=list, description="Source documents used")
    query: str = Field(..., description="Original query")
    provider: LLMProvider = Field(..., description="LLM provider used")
    processing_time_ms: Optional[float] = Field(None, description="Total processing time in milliseconds")
    follow_up_questions: Optional[List[str]] = Field(None, description="AI-generated follow-up questions")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "A P1 (Critical) incident has a target resolution of 4 hours...",
                "sources": [
                    {
                        "content": "P1 (Critical) incidents have a target resolution of 4 hours...",
                        "source": "incident_management_guide.md",
                        "chunk_index": 0
                    }
                ],
                "query": "What is the resolution target for a P1 incident?",
                "provider": "gemini",
                "processing_time_ms": 1234.56
            }
        }


# ============= Ingest Endpoint =============

class IngestRequest(BaseModel):
    """Request model for the /ingest endpoint."""
    directory: str = Field(
        default="./data/example_inputs",
        description="Directory to ingest documents from"
    )
    chunk: bool = Field(
        default=True,
        description="Whether to chunk documents for better retrieval"
    )
    chunk_size: int = Field(
        default=800,
        ge=100,
        le=5000,
        description="Target chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=150,
        ge=0,
        le=1000,
        description="Overlap between chunks"
    )


class IngestResponse(BaseModel):
    """Response model for the /ingest endpoint."""
    success: bool = Field(..., description="Whether ingestion was successful")
    documents_processed: int = Field(..., description="Number of source documents processed")
    chunks_created: int = Field(..., description="Number of chunks created (if chunking enabled)")
    message: str = Field(..., description="Status message")


# ============= Health Endpoint =============

class ComponentStatus(BaseModel):
    """Status of a system component."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    details: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""
    status: str = Field(..., description="Overall system status")
    components: List[ComponentStatus] = Field(default_factory=list)
    version: str = Field(default="1.0.0")


# ============= Streaming Response =============

class StreamChunk(BaseModel):
    """A chunk of streaming response."""
    type: str = Field(..., description="Type of chunk: 'token', 'source', 'done', 'error'")
    content: Optional[str] = Field(None, description="Token content for 'token' type")
    source: Optional[SourceDocument] = Field(None, description="Source for 'source' type")
    error: Optional[str] = Field(None, description="Error message for 'error' type")


# ============= Analysis Endpoint =============

class AnalysisRequest(BaseModel):
    """Request model for the /analyze endpoint."""
    text: str = Field(
        ..., 
        min_length=10,
        max_length=5000, 
        description="Text to analyze"
    )
    provider: LLMProvider = Field(
        default=LLMProvider.GEMINI,
        description="LLM provider to use for analysis"
    )


class AnalysisResponse(BaseModel):
    """Response model for the /analyze endpoint."""
    summary: str = Field(..., description="AI-generated summary")
    tags: List[str] = Field(default_factory=list, description="Extracted topics/tags")
    complexity: Optional[str] = Field(None, description="Estimated complexity (beginner/intermediate/advanced)")
    processing_time_ms: Optional[float] = Field(None, description="Total processing time in milliseconds")


# ============= AI Status Endpoint =============

class AIStatusResponse(BaseModel):
    """Response model for the /ai-status endpoint."""
    provider: LLMProvider = Field(..., description="Current LLM provider")
    status: str = Field(..., description="Connection status: 'connected', 'degraded', 'disconnected'")
    model: Optional[str] = Field(None, description="Model name/version")
    details: Optional[str] = Field(None, description="Additional status details")
