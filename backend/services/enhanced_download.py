"""Enhanced download functionality for KnobGallery++.

This module provides improved multithreaded download capabilities for knob assets.
"""
import os
import httpx
import logging
import threading
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple, Callable, Set
from pathlib import Path

from core.models import KnobAsset, ScrapeStatus
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedDownloader:
    """Enhanced downloader with advanced multithreading capabilities."""
    
    def __init__(self, knobs_dir: Path, thumbnails_dir: Path, retry_attempts: int = 3):
        """Initialize the enhanced downloader.
        
        Args:
            knobs_dir: Directory to store knob files
            thumbnails_dir: Directory to store thumbnail images
            retry_attempts: Number of retry attempts for failed downloads
        """
        self.knobs_dir = knobs_dir
        self.thumbnails_dir = thumbnails_dir
        self.retry_attempts = retry_attempts
        
        # Thread-safe containers for tracking
        self._lock = threading.Lock()
        self._completed_ids: Set[int] = set()
        self._failed_ids: Set[int] = set()
        
        # Status tracking
        self.status = ScrapeStatus()

    def download_thumbnail_with_retry(self, knob: KnobAsset) -> str:
        """Download a thumbnail with retry logic."""
        thumbnail_path = self.thumbnails_dir / f"{knob.id}.png"
        knob.local_thumbnail_path = str(thumbnail_path)
        
        # Skip if already downloaded
        if os.path.exists(thumbnail_path):
            return str(thumbnail_path)
            
        if not knob.thumbnail_url:
            logger.error(f"Thumbnail URL is missing for knob {knob.id}")
            return ""
        
        # Try multiple times
        for attempt in range(1, self.retry_attempts + 1):
            try:
                response = httpx.get(knob.thumbnail_url, timeout=10.0)
                response.raise_for_status()
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                if attempt > 1:
                    logger.info(f"Successfully downloaded thumbnail for knob {knob.id} after {attempt} attempts")
                return str(thumbnail_path)
                
            except Exception as e:
                if attempt < self.retry_attempts:
                    logger.warning(f"Attempt {attempt} failed for thumbnail {knob.id}: {e}")
                else:
                    logger.error(f"All attempts failed for thumbnail {knob.id}: {e}")
                    return ""
        
        return ""  # Should not reach here

    def download_knob_with_retry(self, knob: KnobAsset) -> str:
        """Download a knob file with retry logic."""
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
        
        # Try multiple times
        for attempt in range(1, self.retry_attempts + 1):
            try:
                response = httpx.get(knob.download_url, timeout=15.0)
                response.raise_for_status()
                
                with open(knob_path, 'wb') as f:
                    f.write(response.content)
                
                knob.downloaded = True
                if attempt > 1:
                    logger.info(f"Successfully downloaded knob {knob.id} after {attempt} attempts")
                return str(knob_path)
                
            except Exception as e:
                if attempt < self.retry_attempts:
                    logger.warning(f"Attempt {attempt} failed for knob {knob.id}: {e}")
                else:
                    logger.error(f"All attempts failed for knob {knob.id}: {e}")
                    return ""
        
        return ""  # Should not reach here
    
    def download_knob_complete(self, knob: KnobAsset) -> bool:
        """Download both thumbnail and knob file for a single asset."""
        results = []
        
        # Download thumbnail if needed
        if not knob.local_thumbnail_path or not os.path.exists(knob.local_thumbnail_path):
            thumbnail_result = self.download_thumbnail_with_retry(knob)
            results.append(bool(thumbnail_result))
        
        # Download knob file
        knob_result = self.download_knob_with_retry(knob)
        results.append(bool(knob_result))
        
        success = bool(knob_result)  # We consider it successful if the knob file was downloaded
        
        # Update tracking
        with self._lock:
            if success:
                self._completed_ids.add(knob.id)
                self.status.completed_items = len(self._completed_ids)
            else:
                self._failed_ids.add(knob.id)
        
        return success
    
    def download_assets_in_batches(self, knobs: List[KnobAsset], batch_size: int, 
                                   max_workers: int) -> Tuple[int, int]:
        """Download assets in batches using thread pools.
        
        Args:
            knobs: List of knob assets to download
            batch_size: Number of knobs to process in each batch
            max_workers: Maximum number of worker threads
            
        Returns:
            Tuple of (completed_count, failed_count)
        """
        total = len(knobs)
        
        # Initialize status
        self.status = ScrapeStatus(
            in_progress=True,
            total_items=total,
            completed_items=0,
            message=f"Starting download of {total} assets..."
        )
        
        # Reset tracking
        self._completed_ids.clear()
        self._failed_ids.clear()
        
        # Create batches
        batches = [knobs[i:i+batch_size] for i in range(0, total, batch_size)]
        
        logger.info(f"Starting batch download of {total} assets with {max_workers} workers in {len(batches)} batches")
        
        # Process each batch
        for batch_index, batch in enumerate(batches):
            batch_msg = f"Batch {batch_index+1}/{len(batches)}: Downloading {len(batch)} assets..."
            logger.info(batch_msg)
            
            # Update status
            self.status.message = batch_msg
            
            # Use thread pool for this batch
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all download tasks for this batch
                future_to_knob = {
                    executor.submit(self.download_knob_complete, knob): knob 
                    for knob in batch
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_knob):
                    knob = future_to_knob[future]
                    try:
                        success = future.result()
                        # Status is already updated in download_knob_complete
                        if success:
                            logger.info(f"Downloaded knob {knob.id} ({len(self._completed_ids)}/{total})")
                    except Exception as e:
                        logger.error(f"Unhandled exception for knob {knob.id}: {e}")
                        with self._lock:
                            self._failed_ids.add(knob.id)
            
            # Update batch progress
            self.status.message = f"Completed batch {batch_index+1}/{len(batches)}: {len(self._completed_ids)} downloaded, {len(self._failed_ids)} failed"
        
        # Finalize status
        self.status.in_progress = False
        self.status.success = len(self._completed_ids) > 0
        self.status.message = f"Downloaded {len(self._completed_ids)}/{total} assets. Failed: {len(self._failed_ids)}"
        
        return len(self._completed_ids), len(self._failed_ids)
    
    def download_thumbnails_only(self, knobs: List[KnobAsset]) -> Tuple[int, int]:
        """Download only thumbnails for all knobs.
        
        Args:
            knobs: List of knob assets to download thumbnails for
            
        Returns:
            Tuple of (completed_count, failed_count)
        """
        # Use settings for configuration
        max_workers = settings.MAX_DOWNLOAD_WORKERS
        batch_size = settings.DOWNLOAD_BATCH_SIZE
        
        total = len(knobs)
        completed = 0
        failed = 0
        
        # Initialize status
        self.status = ScrapeStatus(
            in_progress=True,
            total_items=total,
            completed_items=0,
            message=f"Starting download of {total} thumbnails..."
        )
        
        # Reset tracking
        self._completed_ids.clear()
        self._failed_ids.clear()
        
        # Create batches
        batches = [knobs[i:i+batch_size] for i in range(0, total, batch_size)]
        
        for batch_index, batch in enumerate(batches):
            batch_msg = f"Batch {batch_index+1}/{len(batches)}: Downloading {len(batch)} thumbnails..."
            logger.info(batch_msg)
            self.status.message = batch_msg
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_knob = {
                    executor.submit(self.download_thumbnail_with_retry, knob): knob 
                    for knob in batch
                }
                
                for future in concurrent.futures.as_completed(future_to_knob):
                    knob = future_to_knob[future]
                    try:
                        result = future.result()
                        with self._lock:
                            if result:
                                self._completed_ids.add(knob.id)
                                completed += 1
                                self.status.completed_items = completed
                            else:
                                self._failed_ids.add(knob.id)
                                failed += 1
                    except Exception as e:
                        logger.error(f"Exception while downloading thumbnail for knob {knob.id}: {e}")
                        with self._lock:
                            self._failed_ids.add(knob.id)
                            failed += 1
        
        # Finalize status
        self.status.in_progress = False
        self.status.success = completed > 0
        self.status.message = f"Downloaded {completed}/{total} thumbnails. Failed: {failed}"
        
        return completed, failed
