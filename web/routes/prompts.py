"""
Prompts Router

This module provides API endpoints for managing prompt execution, scoring, and history.
Handles routing prompts to appropriate AI models and storing results.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from datetime import datetime

# Import controllers
# In a real implementation, these would be imported from actual controller modules
# For now, we'll create placeholder classes
class PromptController:
    """Controller for prompt operations"""
    
    def __init__(self):
        self.available_models = ["gpt4o", "claude", "grok", "manus"]
        
    async def run_prompt(self, prompt: str, model: str) -> Dict[str, Any]:
        """Run a prompt through the specified model"""
        # This would normally send the prompt to the actual model
        # For now, return a placeholder
        return {
            "id": f"prompt_{datetime.now().timestamp()}",
            "prompt": prompt,
            "model": model,
            "output": f"This is a placeholder response from {model} for: {prompt}",
            "created_at": datetime.now().timestamp(),
            "tokens": {
                "prompt": len(prompt.split()),
                "completion": 20,
                "total": len(prompt.split()) + 20
            }
        }
        
    def score_prompt(self, prompt_id: str, score: float) -> bool:
        """Score a prompt result"""
        # This would normally update the score in the database
        # For now, return success
        return True
        
    def get_history(self, limit: int = 50, offset: int = 0, model: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get prompt history from the database"""
        # This would normally query the database
        # For now, return placeholders
        return [
            {
                "id": "placeholder_prompt_1",
                "prompt": "What is the meaning of life?",
                "model": "gpt4o",
                "output": "The meaning of life is 42.",
                "score": 0.8,
                "created_at": datetime.now().timestamp() - 3600,
                "tokens": {
                    "prompt": 7,
                    "completion": 6,
                    "total": 13
                }
            },
            {
                "id": "placeholder_prompt_2",
                "prompt": "How does quantum computing work?",
                "model": "claude",
                "output": "Quantum computing leverages quantum mechanics principles...",
                "score": 0.9,
                "created_at": datetime.now().timestamp() - 7200,
                "tokens": {
                    "prompt": 5,
                    "completion": 8,
                    "total": 13
                }
            }
        ]
        
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available AI models"""
        return [
            {"id": "gpt4o", "name": "GPT-4o", "provider": "OpenAI", "max_tokens": 8192},
            {"id": "claude", "name": "Claude 3 Opus", "provider": "Anthropic", "max_tokens": 100000},
            {"id": "grok", "name": "Grok-1", "provider": "xAI", "max_tokens": 8192},
            {"id": "manus", "name": "Manus", "provider": "Manus", "max_tokens": 32768}
        ]

# Configure logging
logger = logging.getLogger("ai_studio.prompts")

# Create router
router = APIRouter()

# Models
class PromptRequest(BaseModel):
    """Prompt execution request"""
    prompt: str = Field(..., description="The prompt text to execute")
    model: str = Field(..., description="The AI model to use")
    use_context: bool = Field(False, description="Whether to use context for prompt execution")
    context_query: Optional[str] = Field(None, description="Context query text")
    context_limit: int = Field(5, description="Number of context nodes to fetch")

class PromptResponse(BaseModel):
    """Prompt execution response"""
    id: str
    prompt: str
    model: str
    output: str
    created_at: float
    tokens: Dict[str, int]

class PromptScoreRequest(BaseModel):
    """Prompt scoring request"""
    prompt_id: str = Field(..., description="ID of the prompt to score")
    score: float = Field(..., description="Score value (0.0 to 1.0)", ge=0.0, le=1.0)

class PromptHistoryItem(BaseModel):
    """Prompt history item"""
    id: str
    prompt: str
    model: str
    output: str
    score: Optional[float] = None
    created_at: float
    tokens: Dict[str, int]

class AIModel(BaseModel):
    """AI model information"""
    id: str
    name: str
    provider: str
    max_tokens: int

# Dependency to get controller
def get_prompt_controller():
    """Dependency to get the prompt controller"""
    # In a real implementation, this would be a singleton or retrieved from a dependency injection system
    return PromptController()

# Routes
@router.post("/run", response_model=PromptResponse)
async def run_prompt(
    prompt_request: PromptRequest,
    controller: PromptController = Depends(get_prompt_controller)
):
    """
    Execute a prompt using the specified AI model
    
    Args:
        prompt_request: The prompt execution request
        
    Returns:
        PromptResponse: The prompt execution result
    """
    logger.info("Debug: Incoming Prompt Request: %s", prompt_request.dict())
    try:
        # Validate model
        available_models = controller.get_available_models()
        model_ids = [m["id"] for m in available_models]
        if prompt_request.model not in model_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid model: {prompt_request.model}. Available models are: {model_ids}"
            )

        # Check if context is to be used
        context_content = ""
        if prompt_request.use_context:
            logger.info("Using context for prompt execution")
            from ai_studio_package.infra.db_enhanced import search_similar_nodes
            # Fetch similar nodes based on context_query or prompt if query is empty
            query_text = prompt_request.context_query or prompt_request.prompt
            similar_nodes = await search_similar_nodes(
                query_text=query_text,
                node_type=None,  # Any type for now
                limit=prompt_request.context_limit
            )
            if similar_nodes:
                context_content = "Context Information:\n"
                for idx, node in enumerate(similar_nodes, 1):
                    content = node.get('content', '')
                    if isinstance(content, dict):
                        content = content.get('text', '')
                    context_content += f"{idx}. {content}\n"
                logger.info("Context fetched: %s nodes included", len(similar_nodes))
            else:
                logger.info("No relevant context nodes found")

        # Combine context with prompt if context exists
        final_prompt = prompt_request.prompt
        if context_content:
            final_prompt = f"{context_content}\nPrompt: {prompt_request.prompt}"

        result = await controller.run_prompt(final_prompt, prompt_request.model)
        # Temporarily bypass any storage operations to avoid errors
        # Comment out or skip storage calls for testing purposes
        # if you need to store, ensure it's mocked in tests
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error executing prompt: {str(e)}\nTraceback: {traceback.format_exc()}"
        logger.error(error_detail)
        print(error_detail)  # Print for test debugging
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/score", response_model=dict)
async def score_prompt(
    score_request: PromptScoreRequest,
    controller: PromptController = Depends(get_prompt_controller)
):
    """
    Score a prompt result
    
    Args:
        score_request: The prompt scoring request
        
    Returns:
        dict: Success status
    """
    try:
        success = controller.score_prompt(score_request.prompt_id, score_request.score)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to score prompt")
        
        logger.info(f"Scored prompt {score_request.prompt_id} with score {score_request.score}")
        return {"success": True, "prompt_id": score_request.prompt_id, "score": score_request.score}
    except Exception as e:
        logger.error(f"Error scoring prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Error scoring prompt: {str(e)}")

@router.get("/history", response_model=List[PromptHistoryItem])
async def get_history(
    limit: int = 50,
    offset: int = 0,
    model: Optional[str] = None,
    controller: PromptController = Depends(get_prompt_controller)
):
    """
    Get prompt execution history
    
    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip
        model: Filter by AI model
        
    Returns:
        List[PromptHistoryItem]: List of prompt history items
    """
    try:
        history = controller.get_history(limit=limit, offset=offset, model=model)
        return history
    except Exception as e:
        logger.error(f"Error getting prompt history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting prompt history: {str(e)}")

@router.get("/models", response_model=List[AIModel])
async def get_models(controller: PromptController = Depends(get_prompt_controller)):
    """
    Get available AI models
    
    Returns:
        List[AIModel]: List of available AI models
    """
    try:
        models = controller.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")
