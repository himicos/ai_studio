# ai_studio_package/web/routes/search_agent.py
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

# Import the search function from your infra layer
from ai_studio_package.infra.db_enhanced import search_similar_nodes

logger = logging.getLogger(__name__)
router = APIRouter()

class SemanticSearchRequest(BaseModel):
    query_text: str = Field(..., description="The text query for semantic search.")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to return (1-100).")
    node_type: Optional[str] = Field(None, description="Optional filter by node type (e.g., 'reddit_post', 'tweet').")
    min_similarity: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score (0.0 to 1.0).")

class SemanticSearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="List of similar memory nodes found, including a 'similarity' score.")

@router.post(
    "/api/search/semantic", 
    response_model=SemanticSearchResponse,
    summary="Perform Semantic Search on Memory Nodes",
    description="Searches memory nodes based on semantic similarity to the query text using vector embeddings."
)
async def semantic_search(request: SemanticSearchRequest = Body(...)):
    """
    Performs semantic search over stored memory node embeddings based on cosine similarity.
    Filters results by minimum similarity score and optionally by node type.
    """
    try:
        # Basic input validation (although Pydantic handles some)
        if not request.query_text.strip():
            raise HTTPException(status_code=400, detail="Query text cannot be empty.")
            
        logger.info(f"Received semantic search request: query='{request.query_text[:50]}...', limit={request.limit}, min_similarity={request.min_similarity}, node_type={request.node_type}")
        
        # Call the backend function
        similar_nodes = search_similar_nodes(
            query_text=request.query_text,
            limit=request.limit,
            node_type=request.node_type,
            min_similarity=request.min_similarity
        )
        
        logger.info(f"Semantic search returned {len(similar_nodes)} results.")
        return SemanticSearchResponse(results=similar_nodes)
        
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly
        raise http_exc
    except Exception as e:
        logger.error(f"Error during semantic search endpoint execution: {e}", exc_info=True)
        # Provide a generic error message to the client
        raise HTTPException(status_code=500, detail="An unexpected error occurred during semantic search.")

# Example Usage (Testing):
# You would typically call this endpoint using a POST request tool (like curl, Postman, or frontend JS)
# with a JSON body like:
# {
#   "query_text": "recent developments in AI",
#   "limit": 5,
#   "min_similarity": 0.75,
#   "node_type": "reddit_post" 
# } 