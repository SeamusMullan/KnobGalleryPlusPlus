from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
import os

from services.data_service import knob_gallery_service
from services.enhanced_download import EnhancedDownloader
from core.models import KnobAsset, KnobGalleryResponse, ScrapeStatus
from core.config import settings

router = APIRouter()

@router.get("/")
def data_root():
    return {"message": "Data management endpoint"}

@router.get("/knobs", response_model=KnobGalleryResponse)
async def get_all_knobs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page")
):
    """Get all knobs with pagination."""
    return knob_gallery_service.get_all_knobs(page=page, limit=limit)

@router.get("/knobs/{knob_id}", response_model=KnobAsset)
async def get_knob_by_id(knob_id: int):
    """Get a knob by its ID."""
    knob = knob_gallery_service.get_knob_by_id(knob_id)
    if not knob:
        raise HTTPException(status_code=404, detail=f"Knob with id {knob_id} not found")
    return knob

@router.post("/scrape")
async def scrape_gallery(background_tasks: BackgroundTasks):
    """Start scraping the knob gallery."""
    # Check if scraping is already in progress
    status = knob_gallery_service.get_scrape_status()
    if status.in_progress:
        return {"message": "Scraping is already in progress", "status": status}
    
    # Start scraping in the background
    background_tasks.add_task(knob_gallery_service.scrape_all_knobs)
    
    return {"message": "Started scraping gallery", "status": knob_gallery_service.get_scrape_status()}

@router.get("/scrape/status", response_model=ScrapeStatus)
async def get_scrape_status():
    """Get the current status of scraping operation."""
    return knob_gallery_service.get_scrape_status()

@router.post("/thumbnails/download")
async def download_thumbnails(background_tasks: BackgroundTasks):
    """Start downloading thumbnails for all knobs using enhanced multithreaded download."""
    background_tasks.add_task(knob_gallery_service.download_all_thumbnails)
    return {"message": "Started downloading thumbnails with enhanced multithreaded downloader"}

@router.post("/knobs/{knob_id}/download")
async def download_knob(knob_id: int):
    """Download a specific knob file."""
    success, message = await knob_gallery_service.download_knob(knob_id)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}

@router.post("/knobs/batch-download")
async def download_multiple_knobs(knob_ids: List[int], background_tasks: BackgroundTasks):
    """Download multiple knob files in parallel.
    
    This endpoint accepts a list of knob IDs and downloads them in parallel using
    enhanced multithreaded downloader for improved performance.
    """
    if not knob_ids:
        raise HTTPException(status_code=400, detail="No knob IDs provided")
    
    # Start the batch download in the background
    background_tasks.add_task(knob_gallery_service.download_multiple_knobs, knob_ids)
    
    return {
        "message": f"Started downloading {len(knob_ids)} knobs with enhanced multithreaded downloader",
        "knob_ids": knob_ids
    }

@router.get("/preview/{knob_id}")
async def preview_knob(knob_id: int):
    """Get preview information for a knob."""
    knob = knob_gallery_service.get_knob_by_id(knob_id)
    if not knob:
        raise HTTPException(status_code=404, detail=f"Knob with id {knob_id} not found")
    
    # Get local paths if available
    thumbnail_path = knob.local_thumbnail_path if knob.local_thumbnail_path else None
    knob_file_path = knob.local_path if knob.local_path else None
    
    # Check if files exist
    thumbnail_exists = thumbnail_path and os.path.exists(thumbnail_path)
    knob_file_exists = knob_file_path and os.path.exists(knob_file_path)
    
    return {
        "knob": knob,
        "thumbnail_exists": thumbnail_exists,
        "knob_file_exists": knob_file_exists
    }
