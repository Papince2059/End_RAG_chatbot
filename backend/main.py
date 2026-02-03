"""
Homeopathy RAG System - FastAPI Backend

This backend provides semantic search and RAG capabilities
for homeopathy remedies using Endee vector database.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from endee import Endee
from sentence_transformers import SentenceTransformer
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Homeopathy RAG API",
    description="Semantic search and Q&A for homeopathy remedies",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models and clients
INDEX_NAME = "homeopathy_remedies"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

endee_client = None
embedding_model = None
index = None


# Pydantic models for request/response validation
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class RemedyResult(BaseModel):
    id: str
    remedy_name: str
    alternative_names: str
    similarity: float
    text_preview: str
    full_text: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[RemedyResult]
    query_time_ms: float
    total_results: int


class StatsResponse(BaseModel):
    total_remedies: int
    index_name: str
    dimension: int
    metric: str
    status: str


# Startup event - initialize models
@app.on_event("startup")
async def startup_event():
    global endee_client, embedding_model, index
    
    try:
        logger.info("Initializing Endee client...")
        # Endee SDK v0.1.8 doesn't accept host/port in constructor
        # We must manually override the base_url for Docker networking
        endee_client = Endee()
        
        host = os.getenv("ENDEE_HOST", "localhost")
        port = os.getenv("ENDEE_PORT", "8080")
        
        # Force the connection URL
        new_url = f"http://{host}:{port}/api/v1"
        endee_client.base_url = new_url
        logger.info(f"Connected to Endee at: {new_url}")
        
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        logger.info(f"Getting index: {INDEX_NAME}...")
        index = endee_client.get_index(name=INDEX_NAME)
        
        logger.info("DONE: Backend initialized successfully")
    except Exception as e:
        logger.error(f"ERROR: Failed to initialize backend: {e}")
        raise


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Homeopathy RAG API",
        "version": "1.0.0",
        "endee_connected": endee_client is not None,
        "model_loaded": embedding_model is not None
    }


# Search endpoint
@app.post("/api/search", response_model=SearchResponse)
async def search_remedies(request: SearchRequest):
    """
    Semantic search for homeopathy remedies
    
    Args:
        request: SearchRequest with query and top_k
        
    Returns:
        SearchResponse with matching remedies and metadata
    """
    try:
        start_time = time.time()
        
        # Validate input
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if request.top_k < 1 or request.top_k > 50:
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 50")
        
        logger.info(f"Search query: '{request.query}' (top_k={request.top_k})")
        
        # Generate query embedding
        query_embedding = embedding_model.encode(
            request.query,
            normalize_embeddings=True
        )
        
        # Search Endee index
        results = index.query(
            vector=query_embedding.tolist(),
            top_k=request.top_k
        )
        
        # Format results
        remedy_results = []
        for result in results:
            meta = result.get('meta', {})
            remedy_results.append(RemedyResult(
                id=result.get('id', ''),
                remedy_name=meta.get('remedy_name', 'Unknown'),
                alternative_names=meta.get('alternative_names', ''),
                similarity=result.get('similarity', 0.0),
                text_preview=meta.get('text_preview', ''),
                full_text=meta.get('full_text', '')
            ))
        
        query_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(f"Found {len(remedy_results)} results in {query_time:.2f}ms")
        
        return SearchResponse(
            results=remedy_results,
            query_time_ms=round(query_time, 2),
            total_results=len(remedy_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Statistics endpoint
@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get database statistics
    
    Returns:
        StatsResponse with index information
    """
    try:
        # Get index list to verify
        indexes_response = endee_client.list_indexes()
        indexes = indexes_response.get('indexes', [])
        
        # Find our index
        our_index = None
        for idx in indexes:
            if idx.get('name') == INDEX_NAME:
                our_index = idx
                break
        
        if not our_index:
            raise HTTPException(status_code=404, detail=f"Index '{INDEX_NAME}' not found")
        
        return StatsResponse(
            total_remedies=688,  # Known from ingestion
            index_name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            status="active"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Run with: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
