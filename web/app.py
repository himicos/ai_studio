"""
Web interface for AI Studio
"""
import os
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, WebSocket, Request, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("memory/logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_studio")

# Import AI Studio components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.prompt_router import PromptRouter
from tools.content_scorer import ContentScorer
from tools.burner_manager import BurnerManager
from tools.telegram_handler import TelegramHandler

# Import routers from package
package_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ai_studio_package')
sys.path.append(package_path)

from ai_studio_package.web.routes.settings import router as settings_router
from ai_studio_package.web.routes.memory import router as memory_router, MemoryController
from ai_studio_package.web.routes.prompts import router as prompts_router
from ai_studio_package.web.routes.reddit import router as reddit_router
from ai_studio_package.web.routes.twitter import router as twitter_router

app = FastAPI(title="AI Studio Web Interface")

# Include routers
app.include_router(settings_router, prefix="/api", tags=["settings"])
app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
app.include_router(prompts_router, prefix="/api/prompts", tags=["prompts"])
app.include_router(reddit_router, prefix="/api/reddit", tags=["reddit"])
app.include_router(twitter_router, prefix="/api/twitter", tags=["twitter"])

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
prompt_router = PromptRouter()
memory_controller = MemoryController()  # Initialize the memory controller from the package
content_scorer = ContentScorer()
burner_manager = BurnerManager()
reddit_scanner = None  # Will be initialized when needed
twitter_scanner = None  # Will be initialized when needed

# Models
class PromptRequest(BaseModel):
    prompt: str
    bump_prompts: Optional[bool] = True

class ProxyInfo(BaseModel):
    proxy: Dict[str, str]
    user_agent: str
    
class MemoryFilter(BaseModel):
    topics: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    search_query: Optional[str] = None

# Serve Vite frontend
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str, request: Request):
    frontend_path = "web/frontend/dist"
    
    # Default to index.html for the root path
    if not full_path:
        full_path = "index.html"
    
    file_path = os.path.join(frontend_path, full_path)
    
    # If file doesn't exist, serve index.html for client-side routing
    if not os.path.exists(file_path):
        file_path = os.path.join(frontend_path, "index.html")
    
    return FileResponse(file_path)

# API Routes
@app.get("/api/status")
async def get_status():
    """Get system status"""
    try:
        memory_stats = memory_controller.get_stats()
        return {
            "status": "running",
            "proxy": {
                "total": len(burner_manager.proxies),
                "working": len(burner_manager.working_proxies),
                "failed": len(burner_manager.failed_proxies)
            },
            "memory": {
                "total_nodes": memory_stats["total_nodes"],
                "total_edges": memory_stats["total_edges"],
                "node_types": memory_stats["node_types"]
            },
            "scanners": {
                "reddit": reddit_scanner.get_status() if reddit_scanner else {"status": "not_initialized"},
                "twitter": twitter_scanner.get_status() if twitter_scanner else {"status": "not_initialized"}
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prompt")
async def process_prompt(request: PromptRequest):
    """Process a prompt through the AI Studio system"""
    try:
        # Get a proxy for the request
        proxy, user_agent = burner_manager.get_identity()
        
        # Process the prompt
        response = await prompt_router.process(request.prompt)
        
        # Store in memory
        memory_handler.store_insight(
            topic="prompt_response",
            content=response,
            metadata={
                "prompt": request.prompt,
                "timestamp": datetime.now().timestamp()
            }
        )
        
        return {
            "status": "success",
            "prompt": request.prompt,
            "response": response,
            "proxy_used": proxy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proxies/current")
async def get_current_proxy():
    """Get current proxy information"""
    proxy, user_agent = burner_manager.get_identity()
    return {
        "proxy": proxy,
        "user_agent": user_agent
    }

@app.get("/api/proxies/stats")
async def get_proxy_stats():
    """Get proxy statistics"""
    return {
        "total_proxies": len(burner_manager.proxies),
        "working_proxies": len(burner_manager.working_proxies),
        "failed_proxies": len(burner_manager.failed_proxies),
        "locations": burner_manager.get_proxy_locations()
    }

@app.post("/api/memory/insights")
async def get_insights(filter: MemoryFilter):
    """Get stored insights with filtering"""
    insights = memory_handler.get_insights(
        topics=filter.topics,
        start_date=filter.start_date,
        end_date=filter.end_date,
        search_query=filter.search_query
    )
    return {"insights": insights}

@app.get("/api/memory/topics")
async def get_memory_topics():
    """Get list of available memory topics"""
    return {"topics": memory_handler.get_topics()}

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory statistics"""
    return {
        "total_insights": len(memory_handler.get_insights()),
        "topics": memory_handler.get_topic_counts(),
        "recent_activity": memory_handler.get_recent_activity()
    }

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, event_type: str, source: str, payload: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": event_type,
                    "source": source,
                    "payload": payload,
                    "timestamp": int(datetime.now().timestamp())
                })
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                await self.disconnect(connection)

# Initialize connection manager
manager = ConnectionManager()

# WebSocket for real-time updates
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
            # Send system updates every 5 seconds
            proxy, ua = burner_manager.get_identity()
            await websocket.send_json({
                "type": "system_update",
                "source": "server",
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "proxy": {
                        "current": proxy,
                        "user_agent": ua,
                        "stats": {
                            "total": len(burner_manager.proxies),
                            "working": len(burner_manager.working_proxies),
                            "failed": len(burner_manager.failed_proxies)
                        }
                    },
                    "memory": memory_controller.get_stats(),
                    "reddit": reddit_scanner.get_status(),
                    "twitter": twitter_scanner.get_status()
                }
            })
            await asyncio.sleep(5)
            
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

# Application startup event
@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts
    """
    logger.info("AI Studio backend starting up")
    # Initialize components, load settings, etc.

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the application shuts down
    """
    logger.info("AI Studio backend shutting down")
    # Clean up resources, close connections, etc.

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
