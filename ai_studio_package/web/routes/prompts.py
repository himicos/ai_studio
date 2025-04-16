"""
Prompts Router

This module provides API endpoints for managing prompt execution, scoring, and history.
Handles routing prompts to appropriate AI models and storing results.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Path, Body, Query
from pydantic import BaseModel, Field
from datetime import datetime
import openai
import os
import anthropic

# Import controllers and database functions
from ai_studio_package.web.routes.memory import store_memory_node, search_memory
from ai_studio_package.infra.db_enhanced import (
    create_memory_edge, 
    get_memory_node, 
    update_memory_node_metadata, 
    create_memory_node, 
    generate_embedding_for_node, 
    search_similar_nodes,
    get_prompt_nodes_history # Import history function
)

# --- Pydantic Models (Request/Response Schemas) ---

class PromptRequest(BaseModel):
    """Prompt execution request"""
    prompt: str = Field(..., description="The prompt text to execute")
    model: str = Field(..., description="The AI model to use (e.g., 'gpt4o', 'claude')")
    use_context: bool = Field(False, description="Whether to search memory for context")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to guide the AI model")
    context_query: Optional[str] = Field(None, description="Specific query to use for context search instead of the main prompt")
    context_limit: int = Field(3, description="Maximum number of context items to retrieve from memory")

class PromptResponse(BaseModel):
    """Prompt execution response"""
    id: str = Field(..., description="Unique ID for the prompt execution result")
    prompt: str
    model: str
    output: str
    created_at: float
    tokens: Dict[str, int]

class PromptScoreRequest(BaseModel):
    """Request model for scoring a prompt"""
    score: Union[int, float, str] = Field(..., description="The score assigned to the prompt (e.g., numerical rating, category like 'good'/'bad')")
    notes: Optional[str] = Field(None, description="Optional notes or comments about the score")

class PromptNodeResponse(BaseModel):
    """Response model representing a memory node (simplified)"""
    node_id: str
    node_type: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: float
    updated_at: float

class PromptHistoryItem(BaseModel):
    """Prompt history item"""
    id: str
    prompt: str
    model: str
    output: str
    score: Optional[float] = None # Assuming score might be numerical after processing
    created_at: float
    tokens: Dict[str, int]

class AIModel(BaseModel):
    """AI model information"""
    id: str
    name: str
    provider: str # e.g., 'openai', 'anthropic'
    max_tokens: int # Informational

# --- Controller Class ---

class PromptController:
    """Controller for prompt operations with memory integration"""
    
    def __init__(self):
        self.available_models = ["gpt4o", "claude", "grok", "manus"] # TODO: Make this configurable
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY environment variable not set. OpenAI calls will fail.")
        else:
             openai.api_key = self.openai_api_key # Set it globally for the library upon init
        
        # Load Anthropic API key
        self.anthropic_api_key = os.getenv("CLAUDE_API_KEY")
        if not self.anthropic_api_key:
            logger.warning("CLAUDE_API_KEY environment variable not set. Claude calls will fail.")
        
    async def run_prompt(self, 
                         prompt: str, 
                         model: str, 
                         use_context: bool = False, 
                         context_query: Optional[str] = None, 
                         context_limit: int = 3,
                         system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Run a prompt through the specified model, optionally prepending context from memory"""
        
        final_prompt = prompt
        context_found = ""
        
        # 1. Search for context if requested
        if use_context:
            query_text = context_query if context_query else prompt
            try:
                logger.info(f"Searching memory for context with query: '{query_text[:50]}...' limit: {context_limit}")
                search_results = search_memory(
                    query_text=query_text,
                    limit=context_limit,
                    semantic_search=True # Assuming semantic search is desired for context
                )
                
                if search_results:
                    # Format context (simple concatenation for now, could be more sophisticated)
                    context_items = [f"- {item['content']}" for item in search_results]
                    context_found = "\n\nRelevant Context Found in Memory:\n" + "\n".join(context_items)
                    logger.info(f"Found {len(search_results)} context items.")
                else:
                    logger.info("No relevant context found in memory.")
                    
            except Exception as e:
                 logger.error(f"Error searching memory for context: {e}")
                 # Decide whether to proceed without context or raise error
                 # For now, we'll proceed without context

        # 2. Construct final prompt
        if context_found:
            final_prompt = f"{context_found}\n\n---\n\nUser Prompt:\n{prompt}"
            
        # 3. Execute prompt with model (using final_prompt)
        try:
            output = ""
            tokens = {"prompt": 0, "completion": 0, "total": 0}

            # --- OpenAI Call --- 
            if model == "gpt4o":
                if not self.openai_api_key:
                     raise ValueError("OpenAI API key is not configured.")
                
                # Construct messages list, including system prompt if provided
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                # TODO: Consider how context should interact with system prompts. 
                # Maybe context goes into the system prompt? Or remains part of user prompt?
                # For now, context is prepended to the user prompt content.
                messages.append({"role": "user", "content": final_prompt}) 
                
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=messages, # Use constructed messages list
                    temperature=0.7
                )
                output = response.choices[0].message.content
                tokens = {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                }
            # --- Anthropic (Claude) Call --- 
            elif model == "claude":
                if not self.anthropic_api_key:
                     raise ValueError("Anthropic API key (CLAUDE_API_KEY) is not configured.")
                
                client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
                # Example using Claude 3 Sonnet, adjust model name as needed
                message = await client.messages.create(
                    model="claude-3-sonnet-20240229", 
                    max_tokens=1024, # Example max_tokens
                    system=system_prompt, # Pass system prompt if provided
                    messages=[{
                        "role": "user", 
                        "content": final_prompt # Use final_prompt
                    }]
                )
                # Assuming the response structure gives text content directly
                # Note: Actual response structure might differ slightly, adjust as needed.
                if message.content and isinstance(message.content, list) and len(message.content) > 0:
                     # Access the text content from the first block if it exists
                     output = message.content[0].text if hasattr(message.content[0], 'text') else ""
                else:
                     output = "" # Handle cases where content is empty or not as expected
                
                # Anthropic API usage details might be structured differently
                # This is a placeholder based on common patterns
                tokens = {
                    "prompt": message.usage.input_tokens if hasattr(message.usage, 'input_tokens') else 0,
                    "completion": message.usage.output_tokens if hasattr(message.usage, 'output_tokens') else 0,
                    "total": (message.usage.input_tokens if hasattr(message.usage, 'input_tokens') else 0) + \
                             (message.usage.output_tokens if hasattr(message.usage, 'output_tokens') else 0)
                }

            else:
                # Placeholder for other models
                output = f"This is a placeholder response from {model} for: {final_prompt}" # Use final_prompt
                tokens = {
                    "prompt": len(final_prompt.split()),
                    "completion": 20,
                    "total": len(final_prompt.split()) + 20
                }
            
            # Create result object
            timestamp = datetime.now().timestamp()
            result = {
                "id": f"prompt_{timestamp}",
                "prompt": final_prompt, # Store the final prompt including context
                "system_prompt": system_prompt, # Store system prompt
                "original_prompt": prompt, # Also store the original user prompt
                "context_used": context_found, # Store the context that was injected
                "model": model,
                "output": output,
                "created_at": timestamp,
                "tokens": tokens
            }
            
            # Store in memory
            await self.store_in_memory(result)
            
            return result
        except Exception as e:
            logger.error(f"Error executing prompt: {e}")
            raise
    
    async def store_in_memory(self, result: Dict[str, Any]) -> None:
        """Store prompt result in memory with vector embeddings"""
        try:
            # Create prompt node
            node_id = create_memory_node(
                content=result["prompt"], # Storing the full prompt with context
                node_type="prompt",
                tags=["prompt", result["model"]],
                metadata={
                    "system_prompt": result.get("system_prompt", ""), # Add system prompt to metadata
                    "model": result["model"],
                    "tokens": result["tokens"]["prompt"],
                    "timestamp": result["created_at"],
                    "original_prompt": result.get("original_prompt", ""), # Add original prompt to metadata
                    "context_used": result.get("context_used", "") # Add context used to metadata
                }
            )
            
            # Create response node
            response_node = store_memory_node(
                content=result["output"],
                node_type="response",
                tags=["response", result["model"]],
                metadata={
                    "model": result["model"],
                    "tokens": result["tokens"]["completion"],
                    "timestamp": result["created_at"],
                    "prompt_id": node_id if node_id else None # Link to prompt node
                }
            )
            
            # Link nodes
            create_memory_edge(
                from_node_id=node_id,
                to_node_id=response_node,
                relation_type="generates",
                metadata={
                    "model": result["model"],
                    "tokens": result["tokens"]["total"]
                }
            )
            
            if node_id: # Use the returned node_id directly
                logger.info(f"Successfully stored prompt result in memory with node_id: {node_id}")
            else:
                logger.error("Failed to store prompt result in memory (create_memory_node returned None).")
        except Exception as e:
            logger.error(f"Error storing prompt in memory: {e}")
            raise
        
    async def score_prompt_node(self, prompt_node_id: str, score_data: PromptScoreRequest) -> Optional[Dict[str, Any]]:
        """Updates the metadata of a prompt node with score information."""
        logger.info(f"Attempting to score prompt node {prompt_node_id} with score: {score_data.score}")
        
        metadata_to_update = {
            "score": score_data.score,
            "score_notes": score_data.notes
        }
        
        try:
            updated_node = update_memory_node_metadata(prompt_node_id, metadata_to_update)
            if updated_node:
                 logger.info(f"Successfully updated score for node {prompt_node_id}")
                 return updated_node
            else:
                 logger.error(f"Failed to update score for node {prompt_node_id} (update function returned None)")
                 return None
        except Exception as e:
            logger.error(f"Exception updating score for node {prompt_node_id}: {e}")
            return None

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available AI models"""
        return [
            {"id": "gpt4o", "name": "GPT-4o", "provider": "OpenAI", "max_tokens": 8192},
            {"id": "claude", "name": "Claude 3 Opus", "provider": "Anthropic", "max_tokens": 100000},
            {"id": "grok", "name": "Grok-1", "provider": "xAI", "max_tokens": 8192},
            {"id": "manus", "name": "Manus", "provider": "Manus", "max_tokens": 32768}
        ]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Dependency to get controller
def get_prompt_controller():
    """Dependency to get the prompt controller"""
    # In a real implementation, this would be a singleton or retrieved from a dependency injection system
    return PromptController()

# Routes
@router.post("/run", response_model=PromptResponse)
async def run_prompt_endpoint(
    prompt_request: PromptRequest, 
    controller: PromptController = Depends(get_prompt_controller)
):
    """
    Execute a prompt using the specified AI model, store in memory,
    and optionally inject context from memory search.
    Also allows specifying a system prompt.
    
    Args:
        prompt_request: The prompt execution request
        
    Returns:
        PromptResponse: The prompt execution result
    """
    try:
        # Validate model
        available_models = [model["id"] for model in controller.get_available_models()]
        if prompt_request.model not in available_models:
            raise HTTPException(status_code=400, detail=f"Invalid model: {prompt_request.model}. Available models: {', '.join(available_models)}")
        
        # Check for similar prompts in memory
        similar_prompts = search_memory(
            query_text=prompt_request.prompt,
            limit=3,
            node_type="prompt"
        )
        
        # Run the prompt via the controller
        result = await controller.run_prompt(
            prompt=prompt_request.prompt,
            model=prompt_request.model,
            use_context=prompt_request.use_context,
            context_query=prompt_request.context_query,
            context_limit=prompt_request.context_limit,
            system_prompt=prompt_request.system_prompt # Pass system_prompt
        )
        
        # Reintegrate memory storage with proper error handling
        try:
            from ai_studio_package.infra.db_enhanced import create_memory_node
            node_id = await create_memory_node(
                node_type="prompt_result",
                content=result.get("output", ""),
                tags=["prompt", prompt_request.model],
                metadata={
                    "prompt": prompt_request.prompt,
                    "model": prompt_request.model,
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.info(f"Stored prompt result in memory with node_id: {node_id}")
        except Exception as e:
            logger.error(f"Error storing prompt result in memory: {e}", exc_info=True)
            # Do not raise HTTPException to avoid disrupting the endpoint response
            # The memory storage failure should not affect the user receiving the result

        # Add similar prompts to result
        result["similar_prompts"] = [
            {
                "id": p["id"],
                "prompt": p["content"],
                "similarity": p["similarity_score"]
            } for p in similar_prompts
        ]
        
        logger.info(f"Executed prompt with model {prompt_request.model}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error executing prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing prompt: {str(e)}")

@router.get("/history", response_model=List[PromptNodeResponse], summary="Get Prompt History")
async def get_prompt_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of prompt history items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Retrieve a list of previously executed prompts (prompt nodes) from memory, ordered by creation time descending."""
    try:
        history_nodes = get_prompt_nodes_history(limit=limit, offset=offset)
        # Validate data structure before returning (optional but good practice)
        # Pydantic will handle validation based on the response_model
        return history_nodes
    except Exception as e:
        logger.error(f"Error retrieving prompt history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving prompt history.")

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

@router.put("/score/{prompt_node_id}", response_model=Optional[PromptNodeResponse], summary="Score a Prompt Node")
async def score_prompt(
    prompt_node_id: str = Path(..., description="The unique ID of the prompt memory node to score"),
    score_request: PromptScoreRequest = Body(...),
    controller: PromptController = Depends(get_prompt_controller)
):
    """
    Assign a score and optional notes to a specific prompt memory node.
    Updates the metadata of the node.
    """
    updated_node_data = await controller.score_prompt_node(prompt_node_id, score_request)
    
    if updated_node_data is None:
        raise HTTPException(status_code=404, detail=f"Prompt node with ID {prompt_node_id} not found or error updating score.")
    
    # Check if the returned data is usable for the response model
    # The PromptNodeResponse model expects certain fields.
    # Ensure the data returned by get_memory_node (called within update_memory_node_metadata)
    # matches the structure expected by PromptNodeResponse.
    try:
        # Map database fields (snake_case) to model fields (snake_case here too, so direct mapping)
        # Ensure all required fields for PromptNodeResponse are present in updated_node_data
        required_fields = ["node_id", "node_type", "content", "metadata", "tags", "created_at", "updated_at"]
        if not all(field in updated_node_data for field in required_fields):
             logger.error(f"Updated node data for {prompt_node_id} is missing required fields for PromptNodeResponse.")
             # Decide how to handle: maybe return a simpler response or raise 500
             raise HTTPException(status_code=500, detail="Internal server error: Updated node data structure mismatch.")

        return PromptNodeResponse(**updated_node_data) 
    except Exception as e:
        # Catch potential Pydantic validation errors or other issues
        logger.error(f"Error constructing PromptNodeResponse for {prompt_node_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing updated node data.")

# Placeholder for GET /prompts/{prompt_id} # Maybe useful?
# @router.get("/prompts/{prompt_id}")
# async def get_prompt_details(prompt_id: str):
#     return {"message": f"Details for prompt {prompt_id} not implemented yet."}
