"""
FastAPI Backend for GreenScape Copilot

This API serves as the backend for the React frontend, providing:
- /api/query - Ask questions to the knowledge base
- /api/ingest - Ingest documents into the vector store
- /api/health - System health check

Run with: uvicorn app.api.main:app --reload --port 8000
"""

import sys
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Load environment variables from .env before anything reads them.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.api.models import (
    QueryRequest, QueryResponse, SourceDocument,
    IngestRequest, IngestResponse,
    HealthResponse, ComponentStatus,
    LLMProvider, AnalysisRequest, AnalysisResponse, AIStatusResponse
)
from app.rag.retriever import Retriever
from app.rag.llm_connector import LLMConnector
from app.rag.embedder import Embedder
from app.ingest.document_loader import DocumentLoader
from app.ingest.chunker import TextChunker
from app.vectorstore.chroma_client import ChromaClient


# Global instances (lazy-loaded)
_retriever: Optional[Retriever] = None
_llm_connectors: dict = {}

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def get_retriever() -> Retriever:
    """Get or create the retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def get_llm(provider: str) -> LLMConnector:
    """Get or create an LLM connector for the given provider."""
    global _llm_connectors
    if provider not in _llm_connectors:
        _llm_connectors[provider] = LLMConnector(provider=provider)
    return _llm_connectors[provider]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    print("🚀 Starting GreenScape Copilot API...")
    
    # Pre-warm the LLM so it's ready for the first request
    print("🔄 Pre-warming LLM connection...")
    try:
        llm = get_llm("gemini")
        connection_status = llm.check_connection()
        status = connection_status.get("status", "unknown")
        model = connection_status.get("model", "unknown")
        details = connection_status.get("details", "")
        if status == "connected":
            print(f"✅ LLM connected: {model} — {details}")
        else:
            print(f"⚠️ LLM status: {status} — {model} — {details}")
    except Exception as e:
        print(f"❌ LLM pre-warm failed: {e}")
    
    # Pre-warm the retriever (loads embedder + vector store)
    print("🔄 Pre-warming retriever...")
    try:
        retriever = get_retriever()
        print(f"✅ Retriever ready (ChromaDB: {retriever.vector_store.collection.count()} docs)")
    except Exception as e:
        print(f"❌ Retriever pre-warm failed: {e}")
    
    print("🚀 API ready to serve requests!")
    yield
    # Shutdown
    print("👋 Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title="GreenScape Copilot API",
    description="RAG-powered knowledge assistant for GreenScape Lawn & Landscape employees",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["Content-Type", "Authorization"],  # Specific headers
)


# ============= API Endpoints =============

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Check the health of all system components.
    
    Returns status of:
    - Vector Store (ChromaDB)
    - LLM (configured provider)
    - Embedding Model
    """
    components = []
    overall_status = "healthy"
    
    # Check Vector Store
    try:
        chroma = ChromaClient()
        count = chroma.collection.count()
        components.append(ComponentStatus(
            name="Vector Store (ChromaDB)",
            status="healthy",
            details=f"{count} documents indexed"
        ))
    except Exception as e:
        components.append(ComponentStatus(
            name="Vector Store (ChromaDB)",
            status="unhealthy",
            details=str(e)
        ))
        overall_status = "degraded"
    
    # Check Embedder
    try:
        embedder = Embedder()
        test_embedding = embedder.generate_embeddings(["test"])
        components.append(ComponentStatus(
            name="Embedding Model",
            status="healthy",
            details="all-MiniLM-L6-v2 loaded"
        ))
    except Exception as e:
        components.append(ComponentStatus(
            name="Embedding Model",
            status="unhealthy",
            details=str(e)
        ))
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        components=components,
        version="1.0.0"
    )


@app.post("/api/query", response_model=QueryResponse, tags=["RAG"])
@limiter.limit("20/minute")  # Rate limit: 20 requests per minute
async def query_knowledge_base(request: Request, query_request: QueryRequest):
    """
    Query the knowledge base and get an AI-generated answer.
    
    This endpoint:
    1. Retrieves relevant documents from the vector store
    2. Sends context + query to the LLM
    3. Returns the answer with source citations
    """
    start_time = time.time()
    
    try:
        # 1. Retrieve relevant documents
        retriever = get_retriever()
        docs = retriever.retrieve(query_request.query, k=query_request.k)
        
        # 2. Generate answer
        if docs:
            llm = get_llm(query_request.provider.value)
            answer = llm.generate_answer(query_request.query, docs)
            
            # Generate follow-up questions
            try:
                follow_up_questions = llm.generate_follow_up_questions(query_request.query, answer)
            except Exception as e:
                print(f"Error generating follow-up questions: {e}")
                follow_up_questions = []
        else:
            answer = "No relevant documents found in the knowledge base. Please try rephrasing your question or ensure documents have been ingested."
            follow_up_questions = []
        
        # 3. Format sources
        sources = []
        for doc in docs:
            metadata = doc.get('metadata', {})
            sources.append(SourceDocument(
                content=doc['content'][:500],  # Truncate for response
                source=metadata.get('source', doc.get('source', 'Unknown')),
                chunk_index=metadata.get('chunk_index'),
                relevance_score=doc.get('score')
            ))
        
        processing_time = (time.time() - start_time) * 1000
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            query=query_request.query,
            provider=query_request.provider,
            processing_time_ms=round(processing_time, 2),
            follow_up_questions=follow_up_questions if follow_up_questions else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/api/ingest", response_model=IngestResponse, tags=["Admin"])
async def ingest_documents(request: IngestRequest):
    """
    Ingest documents from a directory into the vector store.
    
    This endpoint:
    1. Loads documents from the specified directory
    2. Chunks them for optimal retrieval (if enabled)
    3. Generates embeddings
    4. Stores in ChromaDB
    """
    try:
        # Validate directory exists
        if not os.path.isdir(request.directory):
            raise HTTPException(
                status_code=400, 
                detail=f"Directory not found: {request.directory}"
            )
        
        # Create chunker with custom settings
        chunker = TextChunker(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        # Load documents
        loader = DocumentLoader(request.directory, chunker=chunker)
        documents = loader.load_documents(chunk=request.chunk)
        
        if not documents:
            return IngestResponse(
                success=False,
                documents_processed=0,
                chunks_created=0,
                message="No documents found in the specified directory"
            )
        
        # Prepare for embedding
        texts = [doc['content'] for doc in documents]
        metadatas = [doc.get('metadata', {"source": doc['source']}) for doc in documents]
        
        # Generate unique IDs
        ids = []
        for doc in documents:
            metadata = doc.get('metadata', {})
            chunk_idx = metadata.get('chunk_index', 0)
            source = doc['source']
            ids.append(f"{source}_chunk_{chunk_idx}")
        
        # Generate embeddings
        embedder = Embedder()
        embeddings = embedder.generate_embeddings(texts)
        
        # Store in ChromaDB
        chroma = ChromaClient()
        chroma.upsert_documents(texts, metadatas, ids, embeddings)
        
        # Count unique source files
        unique_sources = len(set(doc['source'] for doc in documents))
        
        return IngestResponse(
            success=True,
            documents_processed=unique_sources,
            chunks_created=len(documents),
            message=f"Successfully ingested {unique_sources} documents ({len(documents)} chunks)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/api/stats", tags=["Admin"])
async def get_stats():
    """Get statistics about the knowledge base."""
    try:
        chroma = ChromaClient()
        count = chroma.collection.count()
        
        return {
            "total_chunks": count,
            "vector_store": "ChromaDB",
            "embedding_model": "all-MiniLM-L6-v2"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze", response_model=AnalysisResponse, tags=["AI"])
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def analyze_document(request: Request, analysis_request: AnalysisRequest):
    """
    Analyze a document using AI to generate a summary, tags, and complexity rating.
    
    This endpoint:
    1. Takes text input
    2. Uses the specified LLM provider to analyze the content
    3. Returns summary, tags, and complexity assessment
    """
    start_time = time.time()
    
    try:
        llm = get_llm(analysis_request.provider.value)
        analysis = llm.analyze_document(analysis_request.text)
        
        processing_time = (time.time() - start_time) * 1000
        
        return AnalysisResponse(
            summary=analysis.get("summary", "Analysis unavailable"),
            tags=analysis.get("tags", []),
            complexity=analysis.get("complexity", "intermediate"),
            processing_time_ms=round(processing_time, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/ai-status", response_model=AIStatusResponse, tags=["AI"])
async def get_ai_status(provider: str = "gemini"):
    """
    Check the connection status of an AI provider.
    
    This endpoint tests the connection to the specified LLM provider
    and returns the status along with model information.
    """
    try:
        # Validate provider
        if provider not in LLMConnector.get_available_providers():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Available providers: {LLMConnector.get_available_providers()}"
            )
        
        llm = get_llm(provider)
        connection_status = llm.check_connection()
        
        # Map to enum
        provider_enum = LLMProvider(provider)
        
        return AIStatusResponse(
            provider=provider_enum,
            status=connection_status.get("status", "disconnected"),
            model=connection_status.get("model"),
            details=connection_status.get("details")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


# Root redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
