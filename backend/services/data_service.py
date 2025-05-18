# filepath: c:\Users\seamu\Documents\Github\KnobGallery++\backend\services\data_service.py
import os
import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import shutil
from bs4 import BeautifulSoup
from urllib.parse import quote

from core.models import KnobAsset, KnobGalleryResponse, ScrapeStatus, LicenseType
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global state for scrape status
scrape_status = ScrapeStatus()

# Path to store knob metadata JSON
KNOBS_JSON_PATH = settings.DOWNLOAD_DIR / 'knobs.json'

class KnobGalleryScraperService:
    """Service for scraping and managing knob assets from g200kg WebKnobMan gallery."""
    
    def __init__(self):
        self.base_url = settings.WEBKNOBMAN_GALLERY_URL
        self.data_dir = settings.DOWNLOAD_DIR
        
        # Create necessary directories
        self.knobs_dir = self.data_dir / 'knobs'
        self.thumbnails_dir = self.data_dir / 'thumbnails'
        os.makedirs(self.knobs_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
        
        # Initialize knobs cache
        self.knobs: List[KnobAsset] = []
        self._load_cached_knobs()
    
    def _load_cached_knobs(self) -> None:
        """Load knobs from cache if available."""
        if os.path.exists(KNOBS_JSON_PATH):
            try:
                with open(KNOBS_JSON_PATH, 'r') as f:
                    knob_dicts = json.load(f)
                    self.knobs = [KnobAsset(**knob_dict) for knob_dict in knob_dicts]
                    logger.info(f"Loaded {len(self.knobs)} knobs from cache")
            except Exception as e:
                logger.error(f"Error loading knobs from cache: {e}")
                self.knobs = []
    
    def _save_knobs_to_cache(self) -> None:
        """Save knobs to cache."""
        try:
            with open(KNOBS_JSON_PATH, 'w') as f:
                knob_dicts = [knob.to_dict() for knob in self.knobs]
                json.dump(knob_dicts, f, indent=2)
                logger.info(f"Saved {len(self.knobs)} knobs to cache")
        except Exception as e:
            logger.error(f"Error saving knobs to cache: {e}")
    
    def get_all_knobs(self, page: int = 1, limit: int = 100) -> KnobGalleryResponse:
        """Get all knobs with pagination."""
        start = (page - 1) * limit
        end = start + limit
        
        knobs_subset = self.knobs[start:end] if start < len(self.knobs) else []
        total_pages = (len(self.knobs) + limit - 1) // limit if len(self.knobs) > 0 else 1
        
        return KnobGalleryResponse(
            knobs=knobs_subset,
            total=len(self.knobs),
            page=page,
            total_pages=total_pages
        )
    
    def get_knob_by_id(self, knob_id: int) -> Optional[KnobAsset]:
        """Get a knob by its ID."""
        for knob in self.knobs:
            if knob.id == knob_id:
                return knob
        return None
      async def fetch_knob_list(self) -> List[Dict[str, Any]]:
        """Fetch the list of knobs from the gallery."""
        global scrape_status
        scrape_status = ScrapeStatus(in_progress=True)
        
        try:
            async with httpx.AsyncClient() as client:
                # Make the request to the gallery list endpoint
                response = await client.get(f"{self.base_url}?m=list")
                response.raise_for_status()
                
                # Get the response content
                content = response.content
                
                # Clean the content to handle potential encoding issues
                # Remove any invalid UTF-8 sequences
                content_str = content.decode('utf-8', errors='ignore')
                
                # Clean any tab characters that might cause parsing issues
                content_str = content_str.replace('\t', ' ')
                
                # Parse the JSON response safely
                import json
                knob_list = json.loads(content_str)
                logger.info(f"Fetched {len(knob_list)} knobs from gallery")
                
                scrape_status.total_items = len(knob_list)
                return knob_list
                
        except Exception as e:
            error_message = f"Error fetching knob list: {str(e)}"
            logger.error(error_message)
            scrape_status.in_progress = False
            scrape_status.error_message = error_message
            return []
    
    def process_knob_data(self, knob_data: List[Dict[str, Any]]) -> List[KnobAsset]:
        """Process the knob data from the API response into KnobAsset objects."""
        knob_assets = []
        
        for item in knob_data:
            # Construct URLs
            thumbnail_url = f"https://www.g200kg.com/webknobman/data/gal/{item['id']}.png"
            download_url = f"{self.base_url}?m=get&n={item['id']}&t=bin&f={quote(item['file'])}"
            
            # Create KnobAsset
            knob_asset = KnobAsset(
                id=int(item['id']),
                file=item['file'],
                author=item.get('author', ''),
                license=item.get('license', 'CC0'),
                date=item.get('date', ''),
                comment=item.get('comment', ''),
                tags=item.get('tags', ''),
                size=item.get('size', ''),
                thumbnail_url=thumbnail_url,
                download_url=download_url
            )
            knob_assets.append(knob_asset)
            
        return knob_assets
    
    async def download_thumbnail(self, knob: KnobAsset) -> str:
        """Download the thumbnail for a knob asset."""
        thumbnail_path = self.thumbnails_dir / f"{knob.id}.png"
        knob.local_thumbnail_path = str(thumbnail_path)
        
        # Skip if already downloaded
        if os.path.exists(thumbnail_path):
            return str(thumbnail_path)

        if not knob.thumbnail_url:
            logger.error(f"Thumbnail URL is missing for knob {knob.id}")
            return ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(knob.thumbnail_url)
                response.raise_for_status()
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded thumbnail for knob {knob.id}")
                return str(thumbnail_path)
                
        except Exception as e:
            logger.error(f"Error downloading thumbnail for knob {knob.id}: {e}")
            return ""
    
    async def download_knob_file(self, knob: KnobAsset) -> str:
        """Download the knob file."""
        filename = f"{knob.id}_{knob.file}"
        knob_path = self.knobs_dir / filename
        knob.local_path = str(knob_path)
        
        # Skip if already downloaded
        if os.path.exists(knob_path):
            knob.downloaded = True
            return str(knob_path)

        if not knob.download_url:
            logger.error(f"Download URL is missing for knob {knob.id}")
            return ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(knob.download_url)
                response.raise_for_status()
                
                with open(knob_path, 'wb') as f:
                    f.write(response.content)
                
                knob.downloaded = True
                logger.info(f"Downloaded knob file for knob {knob.id}")
                return str(knob_path)
                
        except Exception as e:
            logger.error(f"Error downloading knob file for knob {knob.id}: {e}")
            return ""
    
    async def scrape_all_knobs(self) -> Tuple[bool, str]:
        """Scrape all knobs from the gallery."""
        global scrape_status
        
        try:
            # Fetch the knob list
            knob_data = await self.fetch_knob_list()
            if not knob_data:
                return False, "No knob data retrieved"
            
            # Process the knob data
            knob_assets = self.process_knob_data(knob_data)
            self.knobs = knob_assets
            
            # Save to cache
            self._save_knobs_to_cache()
            
            # Update status
            scrape_status.in_progress = False
            scrape_status.completed_items = len(knob_assets)
            scrape_status.success = True
            
            return True, f"Successfully scraped {len(knob_assets)} knobs"
        
        except Exception as e:
            error_message = f"Error during scraping: {str(e)}"
            logger.error(error_message)
            
            scrape_status.in_progress = False
            scrape_status.success = False
            scrape_status.error_message = error_message
            
            return False, error_message
    
    async def download_all_thumbnails(self) -> Tuple[bool, str]:
        """Download all thumbnails for knobs."""
        total = len(self.knobs)
        completed = 0
        failed = 0
        
        for knob in self.knobs:
            result = await self.download_thumbnail(knob)
            if result:
                completed += 1
            else:
                failed += 1
        
        self._save_knobs_to_cache()
        return True, f"Downloaded {completed}/{total} thumbnails. Failed: {failed}"
    
    async def download_knob(self, knob_id: int) -> Tuple[bool, str]:
        """Download a specific knob by ID."""
        knob = self.get_knob_by_id(knob_id)
        if not knob:
            return False, f"Knob with ID {knob_id} not found"
        
        # Download thumbnail if needed
        if not knob.local_thumbnail_path or not os.path.exists(knob.local_thumbnail_path):
            await self.download_thumbnail(knob)
        
        # Download knob file
        result = await self.download_knob_file(knob)
        
        if result:
            self._save_knobs_to_cache()
            return True, f"Successfully downloaded knob {knob_id}"
        else:
            return False, f"Failed to download knob {knob_id}"
    
    def get_scrape_status(self) -> ScrapeStatus:
        """Get the current status of scraping operation."""
        global scrape_status
        return scrape_status

# Create a singleton instance
knob_gallery_service = KnobGalleryScraperService()