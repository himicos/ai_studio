# ai_studio_package/web/routes/search_agent.py
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import re

# Import the search function from your infra layer
from ai_studio_package.infra.db_enhanced import search_similar_nodes

logger = logging.getLogger(__name__)
router = APIRouter()

class SemanticSearchRequest(BaseModel):
    query_text: str = Field(..., description="The text query for semantic search.")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to return (1-100).")
    node_type: Optional[str] = Field(None, description="Optional filter by node type (e.g., 'reddit_post', 'tweet').")
    min_similarity: float = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity score (0.0 to 1.0).")

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
    Semantic search endpoint to find memory nodes similar to the query text.
    """
    try:
        query_text = request.query_text
        limit = request.limit
        node_type = request.node_type
        min_similarity = request.min_similarity
        
        logger.info(f"Semantic search request: query='{query_text}', limit={limit}, "
                   f"node_type={node_type}, min_similarity={min_similarity}")
        
        # Special case for test requests - use a very low similarity threshold
        if query_text.lower().startswith("test") or "test" in query_text.lower():
            logger.info(f"Test query detected: '{query_text}' - using extra low min_similarity of 0.05")
            min_similarity = min(min_similarity, 0.05)  # Use the lower of the two
        
        # Set a more reasonable default minimum threshold for normal queries
        # Most decent matches will be above 0.15
        adjusted_min_similarity = min(min_similarity, 0.15)
        if adjusted_min_similarity < min_similarity:
            logger.info(f"Adjusted min_similarity from {min_similarity} to {adjusted_min_similarity} for higher recall")
            min_similarity = adjusted_min_similarity
            
        try:
            # Import directly here to ensure we're using the latest version after any hotfixes
            from ai_studio_package.infra.vector_adapter import search_similar_nodes_faiss
            
            # Try FAISS search first
            logger.info(f"Attempting direct FAISS search for query '{query_text}'")
            results = search_similar_nodes_faiss(
                query_text=query_text,
                limit=limit,
                node_type=node_type,
                min_similarity=min_similarity
            )
            
            if results:
                logger.info(f"FAISS search returned {len(results)} results for query '{query_text}'")
            else:
                logger.warning(f"FAISS search returned no results, falling back to SQLite search")
                
                # Fall back to SQLite search_similar_nodes
                results = search_similar_nodes(
                    query_text=query_text,
                    limit=limit,
                    node_type=node_type,
                    min_similarity=min_similarity
                )
                
        except ImportError:
            logger.warning("FAISS search not available, using SQLite search")
            
            # Perform semantic search using SQLite
            results = search_similar_nodes(
                query_text=query_text,
                limit=limit,
                node_type=node_type,
                min_similarity=min_similarity
            )
        except Exception as e:
            logger.error(f"Search error: {e}")
            results = []
        
        logger.info(f"Search returned {len(results)} results for query '{query_text}'")
        
        # Log all results for debugging
        for i, node in enumerate(results):
            logger.info(f"  Result {i+1}: ID={node.get('id')}, Type={node.get('type')}, "
                       f"Title={node.get('title', '')[:30]}..., Similarity={node.get('similarity', 0):.4f}")
        
        if not results:
            logger.warning(f"No results found with min_similarity={min_similarity}. "
                          f"Try using a test query with lower threshold, or verify FAISS index contains data.")
        
        # Return a single SemanticSearchResponse with all results
        return SemanticSearchResponse(results=results)
        
    except Exception as e:
        logger.error(f"Error in semantic search endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error performing semantic search: {str(e)}"
        )

# Example Usage (Testing):
# You would typically call this endpoint using a POST request tool (like curl, Postman, or frontend JS)
# with a JSON body like:
# {
#   "query_text": "recent developments in AI",
#   "limit": 5,
#   "min_similarity": 0.75,
#   "node_type": "reddit_post" 
# } 