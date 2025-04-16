#!/usr/bin/env python3
"""
AI Studio - Main FastAPI Application

This is the main entry point for the AI Studio backend, providing a modular
FastAPI application with WebSocket support and structured routers.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import json # Import json
import random # Import random for proxy selection
from transformers import pipeline, AutoTokenizer # <<< ADD IMPORT
import sys # Import sys for sys.stdout

# Load environment variables
load_dotenv()

# Configure logging
os.makedirs("memory/logs", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("memory/logs/app.log", encoding='utf-8'),
        logging.StreamHandler(stream=sys.stdout)
    ],
    encoding='utf-8'
)

# Optional: For finer control, configure handlers individually
# Get the root logger
root_logger = logging.getLogger()
# Remove existing handlers configured by basicConfig if any
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create file handler with utf-8
file_handler = logging.FileHandler("memory/logs/app.log", encoding='utf-8')
file_handler.setFormatter(formatter)

# Create stream handler with utf-8
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# Add handlers to the root logger
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.DEBUG)

# Example: Get a specific logger (optional, inherits from root)
logger = logging.getLogger("ai_studio")

# Create FastAPI app
app = FastAPI(
    title="AI Studio OS",
    description="Modular AI backend for real-time web tracking and prompt-driven automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
        
    async def broadcast(self, event_type: str, source: str, payload: Dict[str, Any]):
        """
        Broadcast a message to all connected clients
        
        Args:
            event_type: Type of event (log_event, scanner_started, etc.)
            source: Source module or component
            payload: Event data
        """
        message = {
            "type": event_type,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                # Connection might be closed, remove it
                await self.disconnect(connection)

# Create connection manager
manager = ConnectionManager()

# Import routers
from ai_studio_package.web.routes import settings, twitter, prompts, memory
from ai_studio_package.web.routes.twitter_agent import router as twitter_agent_router
from ai_studio_package.web.routes.reddit_agent import router as reddit_agent_router
from ai_studio_package.web.routes import search_agent
from ai_studio_package.infra.db_enhanced import init_db, init_vector_db, get_db_connection

# Register routers
app.include_router(settings.router)
app.include_router(twitter.router)
app.include_router(prompts.router)
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(twitter_agent_router)
app.include_router(reddit_agent_router)
app.include_router(search_agent.router, tags=["Search"])

# WebSocket Manager
manager = ConnectionManager()

# Import necessary components for startup
from ai_studio_package.data.twitter_tracker import TwitterTracker
from ai_studio_package.data.reddit_tracker import RedditTracker
from ai_studio_package.data.browser_manager import BrowserManager
# Import pipeline/tokenizer if not already imported globally
from transformers import pipeline, AutoTokenizer

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Startup event
@app.on_event("startup")
async def startup_event():
    # Create required directories
    os.makedirs("memory/logs", exist_ok=True)
    os.makedirs("memory/prompt_outputs", exist_ok=True)
    logger.info("Directories checked/created.")
    
    # Initialize databases
    init_db()
    init_vector_db()
    logger.info("Databases initialized.")

    # === Initialize AI Pipelines FIRST ===
    # Check for GPU availability
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        gpu_count = torch.cuda.device_count() if cuda_available else 0
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            logger.info(f"🔥 CUDA is available! Found {gpu_count} GPU(s). Using: {gpu_name}")
            # Try to ensure GPU memory is cleared
            if hasattr(torch.cuda, 'empty_cache'):
                torch.cuda.empty_cache()
                logger.info("Cleared CUDA cache to prepare for model loading")
        else:
            logger.warning("⚠️ CUDA is not available. Using CPU for model inference.")
    except Exception as cuda_err:
        logger.error(f"Error checking CUDA availability: {cuda_err}")
        cuda_available = False
        
    # --- Summarization --- 
    try:
        # Using a more specific model name might be needed if multiple types exist
        sum_model_name = "sshleifer/distilbart-cnn-12-6" 
        logger.info(f"Loading summarization pipeline/tokenizer ({sum_model_name})...")
        app.state.summarizer_tokenizer = AutoTokenizer.from_pretrained(sum_model_name)
        try: # Try GPU
             if cuda_available:
                 app.state.summarizer_pipeline = pipeline("summarization", model=sum_model_name, tokenizer=app.state.summarizer_tokenizer, device=0)
                 logger.info(f"✅ Summarization pipeline loaded on GPU.")
             else:
                 raise RuntimeError("CUDA not available")
        except Exception as gpu_err:
             logger.warning(f"Summarizer GPU failed ({gpu_err}), trying CPU...")
             app.state.summarizer_pipeline = pipeline("summarization", model=sum_model_name, tokenizer=app.state.summarizer_tokenizer, device=-1)
             logger.info(f"⚠️ Summarization pipeline loaded on CPU.")
    except Exception as e:
        logger.error(f"Failed to load summarization pipeline: {e}", exc_info=True)
        app.state.summarizer_pipeline = None
        app.state.summarizer_tokenizer = None

    # --- Sentiment --- 
    try:
        # Replace with your actual sentiment model name
        sent_model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest" 
        logger.info(f"Loading sentiment pipeline ({sent_model_name})...")
        try: # Try GPU
            if cuda_available:
                app.state.sentiment_pipeline = pipeline("sentiment-analysis", model=sent_model_name, device=0)
                logger.info(f"✅ Sentiment pipeline loaded on GPU.")
            else:
                raise RuntimeError("CUDA not available")
        except Exception as gpu_err:
            logger.warning(f"Sentiment GPU failed ({gpu_err}), trying CPU...")
            app.state.sentiment_pipeline = pipeline("sentiment-analysis", model=sent_model_name, device=-1)
            logger.info(f"⚠️ Sentiment pipeline loaded on CPU.")
    except Exception as e:
        logger.error(f"Failed to load sentiment pipeline: {e}", exc_info=True)
        app.state.sentiment_pipeline = None

    # --- NER --- 
    try:
        # Replace with your actual NER model name
        ner_model_name = "dslim/bert-base-NER" 
        logger.info(f"Loading NER pipeline ({ner_model_name})...")
        try: # Try GPU
             if cuda_available:
                 app.state.ner_pipeline = pipeline("ner", model=ner_model_name, grouped_entities=True, device=0)
                 logger.info(f"✅ NER pipeline loaded on GPU.")
             else:
                 raise RuntimeError("CUDA not available")
        except Exception as gpu_err:
             logger.warning(f"NER GPU failed ({gpu_err}), trying CPU...")
             app.state.ner_pipeline = pipeline("ner", model=ner_model_name, grouped_entities=True, device=-1)
             logger.info(f"⚠️ NER pipeline loaded on CPU.")
    except Exception as e:
        logger.error(f"Failed to load NER pipeline: {e}", exc_info=True)
        app.state.ner_pipeline = None
    # === End AI Pipeline Initialization ===

    # === Initialize Trackers (AFTER pipelines) ===
    # --- Twitter Tracker --- 
    try:
        logger.info("Initializing TwitterTracker...")
        browser_manager = BrowserManager(headless=True, proxy=None)
        # Pass pipelines if TwitterTracker needs them (modify its __init__ if necessary)
        twitter_tracker_instance = TwitterTracker(
            browser_manager=browser_manager
            # sentiment_pipeline=app.state.sentiment_pipeline, # Example
            # ner_pipeline=app.state.ner_pipeline          # Example
        )
        app.state.twitter_scanner = twitter_tracker_instance
        # ... (rest of twitter loading logic) ...
        logger.info("TwitterTracker initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize TwitterTracker: {e}", exc_info=True)
        app.state.twitter_scanner = None

    # --- Reddit Tracker --- 
    try:
        logger.info("Initializing RedditTracker...")
        sentiment_pipeline = app.state.sentiment_pipeline if hasattr(app.state, 'sentiment_pipeline') else None
        ner_pipeline = app.state.ner_pipeline if hasattr(app.state, 'ner_pipeline') else None
        reddit_tracker_instance = RedditTracker(
            sentiment_pipeline=sentiment_pipeline,
            ner_pipeline=ner_pipeline
        )
        app.state.reddit_tracker = reddit_tracker_instance
        # Log initialization status based on PRAW client AND pipelines
        if reddit_tracker_instance.reddit and sentiment_pipeline and ner_pipeline:
             logger.info("RedditTracker initialized successfully with PRAW client and AI pipelines.")
        elif reddit_tracker_instance.reddit:
             logger.warning("RedditTracker initialized with PRAW client, but one or more AI pipelines FAILED to load.")
        else:
             logger.error("RedditTracker PRAW client failed to initialize.")
             app.state.reddit_tracker = None # Ensure it's None if PRAW failed

    except Exception as e:
        logger.error(f"Failed to initialize RedditTracker: {e}", exc_info=True)
        app.state.reddit_tracker = None
    # === End Tracker Initialization ===

    logger.info("AI Studio backend startup sequence finished.")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Close any active connections
    for connection in manager.active_connections:
        await connection.close()
    
    logger.info("AI Studio backend shutting down")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for consistent error responses
    """
    status_code = 500
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
    
    error_detail = str(exc)
    error_type = exc.__class__.__name__
    
    # Log the error
    logger.error(f"Error processing request: {error_detail}", exc_info=True)
    
    # Broadcast error event via WebSocket if it's a server error
    if status_code >= 500:
        await manager.broadcast(
            event_type="error_event",
            source="server",
            payload={
                "error": error_detail,
                "code": status_code,
                "type": error_type,
                "path": request.url.path
            }
        )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_detail,
            "code": status_code,
            "type": error_type
        }
    )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "source": "server",
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "message": "Connected to AI Studio WebSocket server",
                "client_id": id(websocket),
                "supported_events": [
                    "prompt_result",
                    "memory_added",
                    "scanner_started",
                    "scanner_stopped",
                    "log_event",
                    "error_event"
                ]
            }
        })
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket))
        
        # Listen for messages from client
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            
            # Handle different event types
            if event_type == "prompt_request":
                # Forward to prompt router
                asyncio.create_task(handle_prompt_request(data))
            elif event_type == "scanner_control":
                # Forward to reddit/twitter router
                asyncio.create_task(handle_scanner_control(data))
            elif event_type == "memory_query":
                # Forward to memory router
                asyncio.create_task(handle_memory_query(data))
            
            logger.info(f"Processed WebSocket message: {event_type}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
    finally:
        # Cancel heartbeat task
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()

# Event handlers
async def handle_prompt_request(data: Dict[str, Any]):
    try:
        prompt = data.get("prompt")
        model = data.get("model")
        # TODO: Get other params like use_context, system_prompt from data if needed
        
        if not prompt or not model:
            logger.error("Prompt request missing prompt or model.")
            await manager.broadcast(
                event_type="error_event",
                source="prompt_engine",
                payload={"error": "Prompt request must include 'prompt' and 'model'."}
            )
            return

        # Instantiate controller directly for WebSocket handling
        from ai_studio_package.web.routes.prompts import PromptController # Import class
        controller = PromptController()
        
        # Execute prompt using the controller
        result = await controller.run_prompt(prompt=prompt, model=model)
        
        # Store in memory using the controller
        node_id = await controller.store_in_memory(result)
        
        # Broadcast result
        await manager.broadcast(
            event_type="prompt_result",
            source="prompt_engine",
            payload={
                "result": result,
                "node_id": node_id
            }
        )
    except Exception as e:
        logger.error(f"Error handling prompt request: {e}")
        await manager.broadcast(
            event_type="error_event",
            source="prompt_engine",
            payload={"error": str(e)}
        )

async def handle_scanner_control(data: Dict[str, Any]):
    try:
        scanner_type = data.get("scanner")
        action = data.get("action")
        config = data.get("config", {})
        
        if scanner_type == "reddit":
            from ai_studio_package.web.routes.reddit import control_scanner as reddit_control
            result = await reddit_control(action, config)
        elif scanner_type == "twitter":
            from ai_studio_package.web.routes.twitter import control_scanner as twitter_control
            result = await twitter_control(action, config)
        
        # Broadcast status
        await manager.broadcast(
            event_type=f"scanner_{action}",
            source=scanner_type,
            payload=result
        )
    except Exception as e:
        logger.error(f"Error handling scanner control: {e}")
        await manager.broadcast(
            event_type="error_event",
            source="scanner_control",
            payload={"error": str(e)}
        )

async def handle_memory_query(data: Dict[str, Any]):
    try:
        query_text = data.get("query")
        limit = data.get("limit", 10)
        
        # Search memory
        from ai_studio_package.web.routes.memory import search_memory
        results = await search_memory(query_text, limit)
        
        # Broadcast results
        await manager.broadcast(
            event_type="memory_results",
            source="memory_engine",
            payload={
                "query": query_text,
                "results": results
            }
        )
    except Exception as e:
        logger.error(f"Error handling memory query: {e}")
        await manager.broadcast(
            event_type="error_event",
            source="memory_engine",
            payload={"error": str(e)}
        )

async def send_heartbeat(websocket: WebSocket):
    """Send periodic heartbeat to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            await websocket.send_json({
                "type": "heartbeat",
                "source": "server",
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "server_time": datetime.now().isoformat()
                }
            })
    except asyncio.CancelledError:
        # Task was cancelled, exit gracefully
        pass
    except Exception as e:
        logger.error(f"Error in heartbeat: {e}")

# Serve Frontend Application (Catch-all)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str, request: Request):
    """
    Serve the frontend application for any path not matched by API routes.
    Ensures API paths return 404 if not found, others serve index.html.
    """
    frontend_dir = "web" # Adjust if your frontend build is elsewhere
    index_path = os.path.join(frontend_dir, "index.html")
    file_path = os.path.join(frontend_dir, full_path)
    
    # Prevent directory traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(frontend_dir)):
        # Return 404 for safety, but log it as it shouldn't happen in normal operation
        logger.warning(f"Potential directory traversal attempt blocked: {full_path}")
        raise HTTPException(status_code=404, detail="Not Found")

    # Check if the requested path corresponds to an existing file
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # If it's an API path that wasn't matched by a router, return 404 JSON
    # Check specific prefixes or a general pattern
    # Using startswith("api/") is simple; adjust if your API structure differs
    if full_path.startswith("api/"):
        logger.warning(f"API path not found, returning 404 JSON: /{full_path}")
        raise HTTPException(status_code=404, detail=f"API endpoint not found: /{full_path}")

    # For all other non-file paths, serve the main index.html for SPA routing
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    else:
        # If index.html itself is missing, return a server error
        logger.error(f"Frontend index.html not found at expected path: {index_path}")
        raise HTTPException(status_code=500, detail="Frontend entry point not found.")

# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
