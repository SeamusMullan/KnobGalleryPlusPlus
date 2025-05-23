"""Data service for KnobGallery++.

This module provides the data service for the KnobGallery++ application,
including scraping, downloading, and managing knob assets.
"""

import os
import json
import httpx
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple, Callable
import logging
from pathlib import Path
import shutil
from bs4 import BeautifulSoup
from urllib.parse import quote
import threading

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
                try:
                    knob_list = json.loads(content_str)
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, log the first 100 characters to diagnose
                    preview = content_str[:100] + "..." if len(content_str) > 100 else content_str
                    logger.error(f"JSON parsing error: {str(e)}, Content preview: {preview}")
                    
                    # Save the problematic content to a file for debugging
                    debug_path = self.data_dir / "debug_response.txt"
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(content_str)
                    logger.info(f"Saved problematic response to {debug_path}")
                    
                    raise
                
                logger.info(f"Fetched {len(knob_list)} knobs from gallery")
                
                scrape_status.total_items = len(knob_list)
                return knob_list
                
        except Exception as e:
            error_message = f"Error fetching knob list: {str(e)}"
            logger.error(error_message)
            scrape_status.in_progress = False
            scrape_status.error_message = error_message
            return []
    
    async def scrape_gallery_html(self) -> List[Dict[str, Any]]:
        """Fallback method to scrape the gallery using HTML parsing.
        This is used when the JSON endpoint fails."""
        try:
            async with httpx.AsyncClient() as client:
                # Make the request to the gallery page
                response = await client.get(self.base_url)
                response.raise_for_status()
                
                # Parse the HTML
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                knob_list = []
                # Find all knob panels (based on the class names from the PHP code)
                knob_panels = soup.select('div.itempanel')
                
                for panel in knob_panels:
                    try:
                        # Extract the ID from the panel
                        knob_id = panel.attrs.get('id')
                        if not knob_id:
                            continue
                            
                        # Extract filename
                        filename_elem = panel.select_one('div.itemfile')
                        filename = filename_elem.get_text().strip() if filename_elem else f"knob_{knob_id}"
                        
                        # Extract author
                        author_elem = panel.select_one('div.itemauth')
                        author = author_elem.get_text().strip().replace("by ", "") if author_elem else ""
                        
                        # Extract date
                        date_elem = panel.select_one('div.itemdate')
                        date = date_elem.get_text().strip() if date_elem else ""
                        
                        # Extract comment
                        comment_elem = panel.select_one('div.itemcom')
                        comment = comment_elem.get_text().strip().replace("* ", "") if comment_elem else ""
                        
                        # Extract license
                        license_img = panel.select_one('img.itemlic')
                        license_type = "CC0"  # Default
                        if license_img and license_img.attrs.get('src'):
                            license_src = str(license_img.attrs['src'])
                            license_type = license_src.split('/')[-1].split('.')[0]
                        
                        # Create knob data
                        knob_data = {
                            'id': knob_id,
                            'file': filename,
                            'author': author,
                            'license': license_type,
                            'date': date,
                            'comment': comment,
                            'tags': '',  # Tags not directly visible in the gallery view
                            'size': ''   # Size not directly visible in the gallery view
                        }
                        
                        knob_list.append(knob_data)
                        
                    except Exception as e:
                        logger.error(f"Error parsing knob panel: {str(e)}")
                
                logger.info(f"HTML Fallback: Scraped {len(knob_list)} knobs from gallery")
                return knob_list
                
        except Exception as e:
            error_message = f"Error in HTML fallback scraping: {str(e)}"
            logger.error(error_message)
            return []
    
    def process_knob_data(self, knob_data: List[Dict[str, Any]]) -> List[KnobAsset]:
        """Process the knob data from the API response into KnobAsset objects."""
        knob_assets = []
        
        for item in knob_data:
            try:
                # Convert ID to int if it's a string
                knob_id = int(item['id']) if isinstance(item['id'], str) else item['id']
                
                # Construct URLs
                thumbnail_url = f"https://www.g200kg.com/en/webknobman/data/gal/{knob_id}.png"
                download_url = f"{self.base_url}?m=get&n={knob_id}&t=bin&f={quote(item['file'])}"
                
                # Create KnobAsset
                knob_asset = KnobAsset(
                    id=knob_id,
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
            except Exception as e:
                logger.error(f"Error processing knob data: {str(e)} - Item: {item}")
        
        return knob_assets
    
    async def download_thumbnail(self, knob: KnobAsset) -> str:
        """Download the thumbnail for a knob asset asynchronously."""
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
    
    def download_thumbnail_sync(self, knob: KnobAsset) -> str:
        """Synchronous version of thumbnail download for use in thread pools."""
        thumbnail_path = self.thumbnails_dir / f"{knob.id}.png"
        knob.local_thumbnail_path = str(thumbnail_path)
        
        # Skip if already downloaded
        if os.path.exists(thumbnail_path):
            return str(thumbnail_path)

        if not knob.thumbnail_url:
            logger.error(f"Thumbnail URL is missing for knob {knob.id}")
            return ""
        
        try:
            response = httpx.get(knob.thumbnail_url)
            response.raise_for_status()
            
            with open(thumbnail_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded thumbnail for knob {knob.id}")
            return str(thumbnail_path)
                
        except Exception as e:
            logger.error(f"Error downloading thumbnail for knob {knob.id}: {e}")
            return ""
    
    async def download_knob_file(self, knob: KnobAsset) -> str:
        """Download the knob file asynchronously."""
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
    
    def download_knob_file_sync(self, knob: KnobAsset) -> str:
        """Synchronous version of knob file download for use in thread pools."""
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
            response = httpx.get(knob.download_url)
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
            # First try fetching using the JSON API
            try:
                knob_data = await self.fetch_knob_list()
            except Exception as e:
                logger.warning(f"JSON API fetch failed, falling back to HTML parsing: {str(e)}")
                knob_data = await self.scrape_gallery_html()
            
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
        """Download all thumbnails for knobs using a thread pool for parallel downloads."""
        total = len(self.knobs)
        completed = 0
        failed = 0
        
        # Create a thread-safe counter for progress tracking
        lock = threading.Lock()
        counter = {'completed': 0, 'failed': 0}
        
        def process_result(result: str, knob_id: int) -> None:
            """Process result from thread pool and update counter."""
            with lock:
                if result:
                    counter['completed'] += 1
                    logger.info(f"Thumbnail {counter['completed']}/{total} downloaded for knob {knob_id}")
                else:
                    counter['failed'] += 1
                    logger.warning(f"Failed to download thumbnail for knob {knob_id}")
        
        # Maximum workers - use a reasonable number based on CPU cores, network capacity
        max_workers = min(32, (os.cpu_count() or 4) * 4)
        logger.info(f"Starting parallel thumbnail downloads with {max_workers} workers")
        
        # Use a thread pool to download thumbnails in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Start the download tasks
            future_to_knob = {
                executor.submit(self.download_thumbnail_sync, knob): knob 
                for knob in self.knobs
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_knob):
                knob = future_to_knob[future]
                try:
                    result = future.result()
                    process_result(result, knob.id)
                except Exception as e:
                    logger.error(f"Exception while downloading thumbnail for knob {knob.id}: {e}")
                    with lock:
                        counter['failed'] += 1
        
        # Update final counts
        completed = counter['completed']
        failed = counter['failed']
        
        self._save_knobs_to_cache()
        return True, f"Downloaded {completed}/{total} thumbnails in parallel. Failed: {failed}"
    
    async def download_knob(self, knob_id: int) -> Tuple[bool, str]:
        """Download a specific knob by ID using parallel downloads for thumbnail and knob file."""
        knob = self.get_knob_by_id(knob_id)
        if not knob:
            return False, f"Knob with ID {knob_id} not found"
        
        # Use ThreadPoolExecutor to download both thumbnail and knob file in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Create tasks for thumbnail and knob file download
            futures = []
            
            # Only download thumbnail if needed
            if not knob.local_thumbnail_path or not os.path.exists(knob.local_thumbnail_path):
                futures.append(executor.submit(self.download_thumbnail_sync, knob))
            
            # Always try to download the knob file
            futures.append(executor.submit(self.download_knob_file_sync, knob))
            
            # Wait for all downloads to complete
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Error during parallel download for knob {knob_id}: {e}")
                    results.append("")
        
        # Check if knob file was downloaded successfully (the last result should be the knob file)
        if any(results) and knob.downloaded:
            self._save_knobs_to_cache()
            return True, f"Successfully downloaded knob {knob_id}"
        else:
            return False, f"Failed to download knob {knob_id}"
    
    async def download_multiple_knobs(self, knob_ids: List[int]) -> Tuple[bool, str]:
        """Download multiple knob files in parallel using threading.
        
        Args:
            knob_ids: List of knob IDs to download
            
        Returns:
            Tuple of (success, message)
        """
        # Filter out invalid knob IDs
        valid_knobs = []
        for knob_id in knob_ids:
            knob = self.get_knob_by_id(knob_id)
            if knob:
                valid_knobs.append(knob)
        
        if not valid_knobs:
            return False, "No valid knobs to download"
        
        total = len(valid_knobs)
        lock = threading.Lock()
        counter = {'completed': 0, 'failed': 0}
        
        # Maximum workers - adjust based on system capabilities
        max_workers = min(20, (os.cpu_count() or 2) * 2)
        logger.info(f"Starting parallel download of {total} knobs with {max_workers} workers")
        
        def download_knob_complete(knob: KnobAsset) -> bool:
            """Download both thumbnail and knob file for a single knob."""
            results = []
            
            # Download thumbnail if needed
            if not knob.local_thumbnail_path or not os.path.exists(knob.local_thumbnail_path):
                thumbnail_result = self.download_thumbnail_sync(knob)
                results.append(bool(thumbnail_result))
            
            # Download knob file
            knob_result = self.download_knob_file_sync(knob)
            results.append(bool(knob_result))
            
            # Return True only if both operations succeeded or if the knob file was downloaded
            return bool(knob_result)
        
        # Use a thread pool to download knobs in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_knob = {
                executor.submit(download_knob_complete, knob): knob 
                for knob in valid_knobs
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_knob):
                knob = future_to_knob[future]
                try:
                    success = future.result()
                    with lock:
                        if success:
                            counter['completed'] += 1
                            logger.info(f"Downloaded knob {knob.id} ({counter['completed']}/{total})")
                        else:
                            counter['failed'] += 1
                            logger.warning(f"Failed to download knob {knob.id}")
                except Exception as e:
                    logger.error(f"Exception while downloading knob {knob.id}: {e}")
                    with lock:
                        counter['failed'] += 1
        
        # Save updated knob data to cache
        self._save_knobs_to_cache()
        
        # Return results
        return (counter['completed'] > 0, 
                f"Downloaded {counter['completed']}/{total} knobs in parallel. Failed: {counter['failed']}")
    
    def get_scrape_status(self) -> ScrapeStatus:
        """Get the current status of scraping operation."""
        global scrape_status
        return scrape_status

# Create a singleton instance
knob_gallery_service = KnobGalleryScraperService()
