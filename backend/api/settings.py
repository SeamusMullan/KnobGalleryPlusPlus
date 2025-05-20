from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
from pathlib import Path

from core.config import settings

router = APIRouter()

class SettingsUpdate(BaseModel):
    """Model for updating settings"""
    download_dir: str = None
    max_download_workers: int = None
    max_concurrent_downloads: int = None
    download_batch_size: int = None
    download_retry_attempts: int = None


@router.get("/", summary="Get Settings", description="Returns current application settings.")
def get_settings():
    """Get current application settings"""
    return {
        "download_dir": str(settings.DOWNLOAD_DIR),
        "max_download_workers": settings.MAX_DOWNLOAD_WORKERS,
        "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS,
        "download_batch_size": settings.DOWNLOAD_BATCH_SIZE,
        "download_retry_attempts": settings.DOWNLOAD_RETRY_ATTEMPTS,
    }


@router.post("/update", summary="Update Settings", description="Update application settings.")
def update_settings(settings_update: SettingsUpdate):
    """Update application settings"""
    # Store the current .env content
    env_file = ".env"
    env_content = {}
    
    # Read existing .env if it exists
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_content[key] = value
    
    # Update with new values if provided
    if settings_update.download_dir:
        env_content["DOWNLOAD_DIR"] = settings_update.download_dir
        
    if settings_update.max_download_workers:
        env_content["MAX_DOWNLOAD_WORKERS"] = str(settings_update.max_download_workers)
        
    if settings_update.max_concurrent_downloads:
        env_content["MAX_CONCURRENT_DOWNLOADS"] = str(settings_update.max_concurrent_downloads)
        
    if settings_update.download_batch_size:
        env_content["DOWNLOAD_BATCH_SIZE"] = str(settings_update.download_batch_size)
        
    if settings_update.download_retry_attempts:
        env_content["DOWNLOAD_RETRY_ATTEMPTS"] = str(settings_update.download_retry_attempts)
    
    # Write back to .env file
    with open(env_file, "w") as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    # For immediate effect, update the settings object directly
    if settings_update.download_dir:
        new_dir = Path(settings_update.download_dir)
        if settings.DOWNLOAD_DIR != new_dir:
            settings.DOWNLOAD_DIR = new_dir
            os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
            
            # Create subdirectories
            thumbnails_dir = settings.DOWNLOAD_DIR / "thumbnails"
            knobs_dir = settings.DOWNLOAD_DIR / "knobs"
            os.makedirs(thumbnails_dir, exist_ok=True)
            os.makedirs(knobs_dir, exist_ok=True)
    
    if settings_update.max_download_workers:
        settings.MAX_DOWNLOAD_WORKERS = settings_update.max_download_workers
        
    if settings_update.max_concurrent_downloads:
        settings.MAX_CONCURRENT_DOWNLOADS = settings_update.max_concurrent_downloads
        
    if settings_update.download_batch_size:
        settings.DOWNLOAD_BATCH_SIZE = settings_update.download_batch_size
        
    if settings_update.download_retry_attempts:
        settings.DOWNLOAD_RETRY_ATTEMPTS = settings_update.download_retry_attempts
    
    # Return the updated settings
    return get_settings()


@router.get("/defaults", summary="Get Default Settings", description="Returns default application settings.")
def get_default_settings():
    """Get default application settings"""
    return {
        "download_dir": os.path.join(os.path.expanduser("~"), "KnobGallery"),
        "max_download_workers": (os.cpu_count() or 4) * 4,
        "max_concurrent_downloads": 10,
        "download_batch_size": 20,
        "download_retry_attempts": 3
    }
