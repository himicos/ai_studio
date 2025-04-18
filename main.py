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
import random # Import random for proxy selection
from transformers import pipeline, AutoTokenizer # Ensure these are imported
import sys # Import sys for sys.stdout
import openai # <<< Import openai library

# Load environment variables
load_dotenv()

# Ensure base directories exist
log_dir = "memory/logs"
memory_dir = "memory"
static_dir = "static"
os.makedirs(log_dir, exist_ok=True)
os.makedirs(memory_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "app.log")),
        logging.StreamHandler()
    ]
)
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
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Initialize connection manager
manager = ConnectionManager()

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

# Import routers and components
from ai_studio_package.web.routes.settings import router as settings_router
from ai_studio_package.web.routes.memory import router as memory_router, MemoryController
from ai_studio_package.infra.db_enhanced import init_db, init_vector_db, get_memory_stats, get_db_connection, get_vector_db_connection
from ai_studio_package.web.routes.twitter import router as twitter_router
from ai_studio_package.web.routes.prompts import router as prompts_router
from ai_studio_package.web.routes.twitter_agent import router as twitter_agent_router
from ai_studio_package.web.routes.reddit_agent import router as reddit_agent_router
from ai_studio_package.web.routes.marketing_agent import router as marketing_agent_router
from ai_studio_package.web.routes.search_agent import router as search_agent_router
from tools.burner_manager import BurnerManager
from ai_studio_package.data.twitter_tracker import TwitterTracker
from ai_studio_package.data.browser_manager import BrowserManager
from data.reddit_tracker import RedditTracker as RedditAgentTracker
# Import Self-Improvement Loop components
from ai_studio_package.infra.execution_logs import init_execution_logs_table, track_execution

# Middleware for tracking API requests
@app.middleware("http")
async def track_api_requests_middleware(request: Request, call_next):
    """
    Middleware to track all API requests for the Self-Improvement Loop
    """
    # Only track API routes
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    
    # Get the route path and method
    path = request.url.path
    method = request.method
    task_name = f"{method}:{path}"
    
    # Record start time
    start_time = datetime.now().timestamp() * 1000
    
    # Default status and response
    status_code = 500
    response = None
    
    try:
        # Process the request
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        # Log any exceptions
        logger.error(f"Error processing request {path}: {str(e)}")
        raise
    finally:
        # Record end time
        end_time = datetime.now().timestamp() * 1000
        latency = (end_time - start_time) / 1000  # in seconds
        
        # Track the execution in the background
        try:
            from ai_studio_package.infra.execution_logs import log_execution
            
            # Log success or error
            status = "success" if status_code < 400 else "error"
            error_msg = None
            if status == "error":
                error_msg = f"HTTP error {status_code}"
            
            # Create metadata
            metadata = {
                "method": method,
                "path": path,
                "status_code": status_code,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
            
            # Log the execution asynchronously
            asyncio.create_task(
                log_execution_async(
                    task=task_name,
                    status=status,
                    start_time=int(start_time),
                    end_time=int(end_time),
                    latency=latency,
                    error=error_msg,
                    metadata=metadata
                )
            )
        except Exception as log_err:
            logger.error(f"Error logging execution: {log_err}")

async def log_execution_async(
    task: str,
    status: str,
    start_time: int,
    end_time: int, 
    latency: float,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Asynchronous wrapper for the synchronous log_execution function"""
    from ai_studio_package.infra.execution_logs import log_execution
    log_execution(
        task=task,
        status=status,
        start_time=start_time,
        end_time=end_time,
        latency=latency,
        error=error,
        metadata=metadata
    )

# Register routers
app.include_router(settings_router, prefix="/api", tags=["settings"])
app.include_router(twitter_router, prefix="/api/twitter", tags=["twitter"])
app.include_router(prompts_router, prefix="/api/prompts", tags=["prompts"])
# --- DEBUG PRINT: Confirm memory router inclusion --- 
print("--- Including memory_router from main.py ---")
# --- END DEBUG PRINT ---
app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
app.include_router(marketing_agent_router, prefix="/api/marketing-agent", tags=["Marketing Agent"])
app.include_router(twitter_agent_router)
app.include_router(reddit_agent_router)
app.include_router(search_agent_router, tags=["Search"])

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
                "client_id": id(websocket)
            }
        })
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket))
        
        # Listen for messages from client
        while True:
            data = await websocket.receive_json()
            # Process client messages if needed
            logger.info(f"Received WebSocket message: {data}")
            
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

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Status endpoint
@app.get("/api/status")
async def get_status():
    """Get system status information"""
    try:
        # Get memory stats
        try:
            memory_stats = get_memory_stats()
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            memory_stats = {
                "total_nodes": 0,
                "total_edges": 0,
                "node_types": {},
                "relation_types": {}
            }
        
        # Get proxy stats
        try:
            proxy_stats = {
                "total": len(app.state.burner_manager.proxies) if hasattr(app.state, 'burner_manager') and app.state.burner_manager else 0,
                "working": len(app.state.burner_manager.working_proxies) if hasattr(app.state, 'burner_manager') and app.state.burner_manager else 0,
                "failed": len(app.state.burner_manager.failed_proxies) if hasattr(app.state, 'burner_manager') and app.state.burner_manager else 0
            }
        except Exception as e:
            logger.error(f"Error getting proxy stats: {e}")
            proxy_stats = {
                "total": 0,
                "working": 0,
                "failed": 0
            }
        
        # Get scanner stats
        try:
            scanner_stats = {
                "reddit": app.state.reddit_scanner.get_status() if hasattr(app.state, 'reddit_scanner') and app.state.reddit_scanner else {"status": "not_initialized"},
                "twitter": app.state.twitter_scanner.get_status() if hasattr(app.state, 'twitter_scanner') and app.state.twitter_scanner else {"status": "not_initialized"}
            }
        except Exception as e:
            logger.error(f"Error getting scanner stats: {e}")
            scanner_stats = {
                "reddit": {"status": "error"},
                "twitter": {"status": "error"}
            }
        
        # Get vector store stats
        try:
            from ai_studio_package.infra.vector_adapter import get_vector_store
            vector_store = get_vector_store()
            vector_stats = vector_store.get_stats() if vector_store else {"vector_count": 0, "metadata_count": 0}
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            vector_stats = {"vector_count": 0, "metadata_count": 0}
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "proxy": proxy_stats,
            "memory": memory_stats,
            "scanners": scanner_stats,
            "vector_store": vector_stats
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Serve frontend for all other routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """
    Serve the frontend application for any path not matched by API routes
    """
    frontend_path = "web/static"
    
    # Default to index.html for the root path
    if not full_path:
        full_path = "index.html"
    
    file_path = os.path.join(frontend_path, full_path)
    
    # If file doesn't exist, serve index.html for client-side routing
    if not os.path.exists(file_path):
        file_path = os.path.join(frontend_path, "index.html")
    
    return FileResponse(file_path)

# Application startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks: initialize database, trackers, etc.
    """
    logger.info("Starting AI Studio application startup sequence...")
    # Initialize main database
    init_db()
    logger.info("Main database initialized.")
    
    # Initialize execution logs table for Self-Improvement Loop
    init_execution_logs_table()
    logger.info("Execution logs table initialized for Self-Improvement Loop.")
    
    # Initialize vector database
    # init_vector_db()
    # logger.info("Vector database initialized.")

    # === Initialize AI Pipelines ===
    # --- Summarization ---
    try:
        sum_model_name = "sshleifer/distilbart-cnn-12-6"
        logger.info(f"Loading summarization pipeline/tokenizer ({sum_model_name})...")
        app.state.summarizer_tokenizer = AutoTokenizer.from_pretrained(sum_model_name)
        try: # Try GPU
             app.state.summarizer_pipeline = pipeline("summarization", model=sum_model_name, tokenizer=app.state.summarizer_tokenizer, device=0)
             logger.info(f"Summarization pipeline loaded on GPU.")
        except Exception as gpu_err:
             logger.warning(f"Summarizer GPU failed ({gpu_err}), trying CPU...")
             app.state.summarizer_pipeline = pipeline("summarization", model=sum_model_name, tokenizer=app.state.summarizer_tokenizer, device=-1)
             logger.info(f"Summarization pipeline loaded on CPU.")
    except Exception as e:
        logger.error(f"Failed to load summarization pipeline: {e}", exc_info=True)
        app.state.summarizer_pipeline = None
        app.state.summarizer_tokenizer = None

    # --- Sentiment ---
    try:
        sent_model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        logger.info(f"Loading sentiment pipeline ({sent_model_name})...")
        try: # Try GPU
            app.state.sentiment_pipeline = pipeline("sentiment-analysis", model=sent_model_name, device=0)
            logger.info(f"Sentiment pipeline loaded on GPU.")
        except Exception as gpu_err:
            logger.warning(f"Sentiment GPU failed ({gpu_err}), trying CPU...")
            app.state.sentiment_pipeline = pipeline("sentiment-analysis", model=sent_model_name, device=-1)
            logger.info(f"Sentiment pipeline loaded on CPU.")
    except Exception as e:
        logger.error(f"Failed to load sentiment pipeline: {e}", exc_info=True)
        app.state.sentiment_pipeline = None

    # --- NER ---
    try:
        ner_model_name = "dslim/bert-base-NER"
        logger.info(f"Loading NER pipeline ({ner_model_name})...")
        try: # Try GPU
             app.state.ner_pipeline = pipeline("ner", model=ner_model_name, grouped_entities=True, device=0)
             logger.info(f"NER pipeline loaded on GPU.")
        except Exception as gpu_err:
             logger.warning(f"NER GPU failed ({gpu_err}), trying CPU...")
             app.state.ner_pipeline = pipeline("ner", model=ner_model_name, grouped_entities=True, device=-1)
             logger.info(f"NER pipeline loaded on CPU.")
    except Exception as e:
        logger.error(f"Failed to load NER pipeline: {e}", exc_info=True)
        app.state.ner_pipeline = None
    # === End AI Pipeline Initialization ===

    # === Initialize OpenAI Client ===
    try:
        logger.info("Initializing OpenAI client...")
        # The client automatically reads OPENAI_API_KEY from env vars
        app.state.openai_client = openai.AsyncOpenAI()
        # Optional: Add a test call to verify the key/connection?
        # models = await app.state.openai_client.models.list()
        # logger.info(f"Successfully connected to OpenAI. Available models (sample): {[m.id for m in models.data[:5]]}")
        logger.info("OpenAI client initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
        app.state.openai_client = None
    # === End OpenAI Client Initialization ===

    # Initialize Trackers/Agents (AFTER pipelines)
    logger.info("Initializing agents...")
    # Initialize browser manager and twitter scanner
    browser_manager = BrowserManager()
    twitter_scanner = TwitterTracker()
    twitter_scanner.set_browser_manager(browser_manager)
    app.state.twitter_scanner = twitter_scanner
    
    # Start the Twitter scanner background task with default scan interval (600 seconds)
    app.state.twitter_scanner_task = asyncio.create_task(twitter_scanner.start())
    
    # Store browser manager in app state for other components
    app.state.browser_manager = browser_manager

    # Initialize Reddit Agent Tracker
    try:
        app.state.reddit_tracker = RedditAgentTracker()
        logger.info("Reddit Agent Tracker initialized.")
        if not app.state.reddit_tracker.reddit:
             logger.warning("Reddit Agent Tracker PRAW client failed to initialize. Check credentials/config.")
    except Exception as e:
        logger.error(f"Failed to initialize Reddit Agent Tracker: {e}", exc_info=True)
        app.state.reddit_tracker = None # Ensure it exists but is None

    # Initialize other services
    # app.state.burner_manager = BurnerManager()
    # logger.info("Burner Manager initialized.")
    
    # Initialize Memory Controller (if needed globally)
    # app.state.memory_controller = MemoryController()
    # logger.info("Memory Controller initialized.")

    # Start background tasks (optional)
    # if app.state.twitter_scanner:
    #     asyncio.create_task(app.state.twitter_scanner.start_tracking())

    logger.info("AI Studio application startup complete.")

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks: cleanup resources.
    """
    logger.info("Starting AI Studio application shutdown sequence...")
    # Cleanup trackers
    if hasattr(app.state, 'twitter_scanner') and app.state.twitter_scanner:
        logger.info("Cleaning up Twitter Scanner...")
        await app.state.twitter_scanner.stop()
        logger.info("Twitter Scanner cleaned up.")

    if hasattr(app.state, 'reddit_tracker') and app.state.reddit_tracker:
        logger.info("Cleaning up Reddit Agent Tracker...")
        # Ensure stop_tracking is called if running
        await app.state.reddit_tracker.stop_tracking()
        logger.info("Reddit Agent Tracker cleaned up.")

    # Add cleanup for other services if needed
    # e.g., close database connections if managed globally

    logger.info("AI Studio application shutdown complete.")

# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn
    # Use port 8001 instead of 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
