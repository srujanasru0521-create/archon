"""FastAPI server for PCIL RAG system."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import logging

from .rag import CodeRAG, RAGResult

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="PCIL RAG API",
    description="Retrieval-Augmented Generation for semantic code search",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG instance
rag: Optional[CodeRAG] = None


# ============ Request/Response Models ============

class IndexRequest(BaseModel):
    """Request to build index."""
    workspace_path: str = "."
    output_path: Optional[str] = None


class QueryRequest(BaseModel):
    """Request to query code."""
    query: str
    k: int = 5


class RetrievalResult(BaseModel):
    """Single retrieval result."""
    symbol_id: str
    name: str
    signature: str
    docstring: str
    file_path: str
    similarity: float


class QueryResponse(BaseModel):
    """Query response."""
    results: List[RetrievalResult]
    total: int
    query: str


class RAGPromptRequest(BaseModel):
    """Request to generate RAG prompt."""
    query: str
    k: int = 3


class RAGPromptResponse(BaseModel):
    """RAG prompt response."""
    prompt: str
    context_count: int


class IndexInfo(BaseModel):
    """Index information."""
    total_symbols: int
    embedding_dimension: int
    backend: str


# ============ Lifecycle Events ============

@app.on_event("startup")
async def startup():
    """Initialize RAG on startup."""
    global rag
    try:
        rag = CodeRAG()
        logger.info("✓ RAG system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    global rag
    if rag:
        rag = None
        logger.info("✓ RAG system shutdown")


# ============ API Endpoints ============

@app.get("/", tags=["General"])
async def root():
    """API root endpoint."""
    return {
        "name": "PCIL RAG API",
        "version": "0.2.0",
        "endpoints": {
            "index": "/index",
            "query": "/query",
            "prompt": "/prompt",
            "info": "/info",
            "health": "/health"
        }
    }


@app.get("/health", tags=["General"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "rag_initialized": rag is not None
    }


@app.post("/index", tags=["Index"])
async def index_code(request: IndexRequest):
    """Build index from workspace."""
    if not rag:
        raise HTTPException(status_code=500, detail="RAG not initialized")

    try:
        workspace_path = Path(request.workspace_path)
        if not workspace_path.exists():
            raise HTTPException(status_code=400, detail=f"Path not found: {workspace_path}")

        logger.info(f"Indexing workspace: {workspace_path}")
        global rag
        rag = CodeRAG(workspace_root=workspace_path)
        rag.index_workspace()

        if request.output_path:
            output = Path(request.output_path)
            rag.save_index(output)
            return {
                "status": "success",
                "symbols_indexed": len(rag.vector_store.index),
                "index_saved_to": str(output)
            }

        return {
            "status": "success",
            "symbols_indexed": len(rag.vector_store.index)
        }

    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse, tags=["Search"])
async def query_code(request: QueryRequest):
    """Query code with natural language."""
    if not rag:
        raise HTTPException(status_code=500, detail="RAG not initialized")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        results = rag.retrieve(request.query, k=request.k)

        return QueryResponse(
            results=[
                RetrievalResult(
                    symbol_id=r.symbol_id,
                    name=r.name,
                    signature=r.signature,
                    docstring=r.docstring,
                    file_path=r.file_path,
                    similarity=r.similarity
                )
                for r in results
            ],
            total=len(results),
            query=request.query
        )

    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt", response_model=RAGPromptResponse, tags=["RAG"])
async def generate_rag_prompt(request: RAGPromptRequest):
    """Generate RAG-augmented prompt for LLM."""
    if not rag:
        raise HTTPException(status_code=500, detail="RAG not initialized")

    try:
        from .rag import create_rag_prompt

        results = rag.retrieve(request.query, k=request.k)
        prompt = create_rag_prompt(request.query, results)

        return RAGPromptResponse(
            prompt=prompt,
            context_count=len(results)
        )

    except Exception as e:
        logger.error(f"Prompt generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info", response_model=IndexInfo, tags=["Info"])
async def get_index_info():
    """Get index information and statistics."""
    if not rag:
        raise HTTPException(status_code=500, detail="RAG not initialized")

    try:
        return IndexInfo(
            total_symbols=len(rag.vector_store.index),
            embedding_dimension=rag.vector_store.embedding_dim,
            backend=type(rag.vector_store).__name__
        )

    except Exception as e:
        logger.error(f"Info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load-index", tags=["Index"])
async def load_index(index_path: str = Query(...)):
    """Load a saved index."""
    if not rag:
        raise HTTPException(status_code=500, detail="RAG not initialized")

    try:
        path = Path(index_path)
        if not path.exists():
            raise HTTPException(status_code=400, detail=f"Index not found: {path}")

        rag.load_index(path)
        return {
            "status": "success",
            "index_loaded_from": str(path),
            "total_symbols": len(rag.vector_store.index)
        }

    except Exception as e:
        logger.error(f"Load index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-index", tags=["Index"])
async def save_index(output_path: str = Query(...)):
    """Save current index to disk."""
    if not rag:
        raise HTTPException(status_code=500, detail="RAG not initialized")

    try:
        path = Path(output_path)
        rag.save_index(path)
        return {
            "status": "success",
            "index_saved_to": str(path)
        }

    except Exception as e:
        logger.error(f"Save index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Error Handlers ============

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "status": "error",
        "detail": str(exc)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
