"""
Settings Router

This module provides API endpoints for managing system settings.
Handles GET/POST operations for runtime configuration including:
- Proxy settings
- Scanner intervals
- Twitter/Reddit tracking configuration
- Model selection
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from dotenv import load_dotenv, set_key
from pathlib import Path

# Configure logging
logger = logging.getLogger("ai_studio.settings")

# Create router
router = APIRouter()

# Models
class ProxyConfig(BaseModel):
    """Proxy configuration model"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class TwitterConfig(BaseModel):
    """Twitter tracking configuration"""
    accounts: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    scan_interval: int = 300  # seconds

class RedditConfig(BaseModel):
    """Reddit tracking configuration"""
    subreddits: List[str] = Field(default_factory=list)
    scan_interval: int = 300  # seconds

class ModelConfig(BaseModel):
    """AI model configuration"""
    default_model: str = "gpt4o"
    available_models: List[str] = ["gpt4o", "claude", "grok", "manus"]

class SystemConfig(BaseModel):
    """System-wide configuration"""
    bump_prompts: bool = False
    scan_interval: int = 300
    log_level: str = "INFO"

class Settings(BaseModel):
    """Complete settings model"""
    proxies: List[ProxyConfig] = Field(default_factory=list)
    twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    reddit: RedditConfig = Field(default_factory=RedditConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)

# Settings file path
SETTINGS_FILE = os.path.join("memory", "settings.json")

# Helper functions
def load_settings() -> Settings:
    """Load settings from file or create default"""
    try:
        if os.path.exists(SETTINGS_FILE) and os.path.getsize(SETTINGS_FILE) > 0: # Check if file exists and is not empty
            with open(SETTINGS_FILE, "r") as f:
                try:
                    data = json.load(f)
                    return Settings(**data)
                except json.JSONDecodeError as json_e:
                    logger.warning(f"Error decoding settings file {SETTINGS_FILE}: {json_e}. Falling back to default settings.")
                    # If decoding fails, proceed to create/save default settings
                    pass # Fall through to default settings creation
        
        # Create and save default settings if file doesn't exist, is empty, or decoding failed
        logger.info(f"Settings file {SETTINGS_FILE} not found, empty, or invalid. Creating default settings.")
        settings = Settings()
        if save_settings(settings): # Use the updated save_settings
            logger.info(f"Default settings saved to {SETTINGS_FILE}")
        else:
            logger.error(f"Failed to save default settings to {SETTINGS_FILE}")
        return settings

    except Exception as e:
        logger.error(f"Unexpected error loading settings: {e}")
        # Return default settings on unexpected error
        return Settings()

def save_settings(settings: Settings) -> bool:
    """Save settings to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        
        with open(SETTINGS_FILE, "w") as f:
            # Use model_dump_json for Pydantic V2 compatibility
            f.write(settings.model_dump_json(indent=2))
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False

def update_env_from_settings(settings: Settings) -> bool:
    """Update .env file from settings"""
    try:
        env_path = Path(".env")
        
        # Update environment variables
        if settings.system.bump_prompts:
            set_key(env_path, "BUMP_PROMPTS", "true")
        else:
            set_key(env_path, "BUMP_PROMPTS", "false")
            
        set_key(env_path, "SCAN_INTERVAL", str(settings.system.scan_interval))
        set_key(env_path, "LOG_LEVEL", settings.system.log_level)
        set_key(env_path, "DEFAULT_MODEL", settings.models.default_model)
        
        # Reload environment variables
        load_dotenv(override=True)
        
        return True
    except Exception as e:
        logger.error(f"Error updating environment variables: {e}")
        return False

# Routes
@router.get("/settings", response_model=Settings)
async def get_settings():
    """
    Get current system settings
    
    Returns:
        Settings: Complete settings object
    """
    try:
        settings = load_settings()
        return settings
    except Exception as e:
        logger.error(f"Error retrieving settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving settings: {str(e)}")

@router.post("/settings", response_model=Settings)
async def update_settings(settings: Settings, background_tasks: BackgroundTasks):
    """
    Update system settings
    
    Args:
        settings: Complete settings object
        
    Returns:
        Settings: Updated settings object
    """
    try:
        # Save settings to file
        success = save_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save settings")
        
        # Update environment variables in background
        background_tasks.add_task(update_env_from_settings, settings)
        
        logger.info("Settings updated successfully")
        return settings
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

@router.get("/settings/twitter", response_model=TwitterConfig)
async def get_twitter_settings():
    """
    Get Twitter-specific settings
    
    Returns:
        TwitterConfig: Twitter configuration
    """
    try:
        settings = load_settings()
        return settings.twitter
    except Exception as e:
        logger.error(f"Error retrieving Twitter settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving Twitter settings: {str(e)}")

@router.post("/settings/twitter", response_model=TwitterConfig)
async def update_twitter_settings(twitter_config: TwitterConfig):
    """
    Update Twitter-specific settings
    
    Args:
        twitter_config: Twitter configuration
        
    Returns:
        TwitterConfig: Updated Twitter configuration
    """
    try:
        settings = load_settings()
        settings.twitter = twitter_config
        success = save_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save Twitter settings")
        
        logger.info("Twitter settings updated successfully")
        return settings.twitter
    except Exception as e:
        logger.error(f"Error updating Twitter settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating Twitter settings: {str(e)}")

@router.get("/settings/reddit", response_model=RedditConfig)
async def get_reddit_settings():
    """
    Get Reddit-specific settings
    
    Returns:
        RedditConfig: Reddit configuration
    """
    try:
        settings = load_settings()
        return settings.reddit
    except Exception as e:
        logger.error(f"Error retrieving Reddit settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving Reddit settings: {str(e)}")

@router.post("/settings/reddit", response_model=RedditConfig)
async def update_reddit_settings(reddit_config: RedditConfig):
    """
    Update Reddit-specific settings
    
    Args:
        reddit_config: Reddit configuration
        
    Returns:
        RedditConfig: Updated Reddit configuration
    """
    try:
        settings = load_settings()
        settings.reddit = reddit_config
        success = save_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save Reddit settings")
        
        logger.info("Reddit settings updated successfully")
        return settings.reddit
    except Exception as e:
        logger.error(f"Error updating Reddit settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating Reddit settings: {str(e)}")

@router.get("/settings/proxies", response_model=List[ProxyConfig])
async def get_proxies():
    """
    Get proxy configurations
    
    Returns:
        List[ProxyConfig]: List of proxy configurations
    """
    try:
        settings = load_settings()
        return settings.proxies
    except Exception as e:
        logger.error(f"Error retrieving proxies: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving proxies: {str(e)}")

@router.post("/settings/proxies", response_model=List[ProxyConfig])
async def update_proxies(proxies: List[ProxyConfig]):
    """
    Update proxy configurations
    
    Args:
        proxies: List of proxy configurations
        
    Returns:
        List[ProxyConfig]: Updated list of proxy configurations
    """
    try:
        settings = load_settings()
        settings.proxies = proxies
        success = save_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save proxy settings")
        
        logger.info("Proxy settings updated successfully")
        return settings.proxies
    except Exception as e:
        logger.error(f"Error updating proxies: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating proxies: {str(e)}")

@router.get("/settings/models", response_model=ModelConfig)
async def get_model_settings():
    """
    Get AI model settings
    
    Returns:
        ModelConfig: Model configuration
    """
    try:
        settings = load_settings()
        return settings.models
    except Exception as e:
        logger.error(f"Error retrieving model settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving model settings: {str(e)}")

@router.post("/settings/models", response_model=ModelConfig)
async def update_model_settings(model_config: ModelConfig, background_tasks: BackgroundTasks):
    """
    Update AI model settings
    
    Args:
        model_config: Model configuration
        
    Returns:
        ModelConfig: Updated model configuration
    """
    try:
        settings = load_settings()
        settings.models = model_config
        success = save_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save model settings")
        
        # Update environment variables in background
        background_tasks.add_task(update_env_from_settings, settings)
        
        logger.info("Model settings updated successfully")
        return settings.models
    except Exception as e:
        logger.error(f"Error updating model settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating model settings: {str(e)}")

@router.get("/settings/system", response_model=SystemConfig)
async def get_system_settings():
    """
    Get system-wide settings
    
    Returns:
        SystemConfig: System configuration
    """
    try:
        settings = load_settings()
        return settings.system
    except Exception as e:
        logger.error(f"Error retrieving system settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving system settings: {str(e)}")

@router.put("/system", response_model=SystemConfig)
async def update_system_settings(system_config: SystemConfig, background_tasks: BackgroundTasks):
    """
    Update system-wide settings
    
    Args:
        system_config: System configuration
        
    Returns:
        SystemConfig: Updated system configuration
    """
    try:
        settings = load_settings()
        settings.system = system_config
        success = save_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save system settings")
        
        # Update environment variables in background
        background_tasks.add_task(update_env_from_settings, settings)
        
        logger.info("System settings updated successfully")
        return settings.system
    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating system settings: {str(e)}")
