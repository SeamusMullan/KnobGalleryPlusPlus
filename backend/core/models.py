from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime
from enum import Enum

class LicenseType(str, Enum):
    CC0 = "CC0"
    PD = "PD"
    CC_BY = "CC-BY"
    CC_BY_SA = "CC-BY-SA"
    CC_BY_ND = "CC-BY-ND"
    CC_BY_NC = "CC-BY-NC"
    CC_BY_NC_SA = "CC-BY-NC-SA"
    CC_BY_NC_ND = "CC-BY-NC-ND"
    CC_BY_4_0 = "CC-BY-4.0"
    CC_BY_SA_4_0 = "CC-BY-SA-4.0"
    CC_BY_ND_4_0 = "CC-BY-ND-4.0"
    CC_BY_NC_4_0 = "CC-BY-NC-4.0"
    CC_BY_NC_SA_4_0 = "CC-BY-NC-SA-4.0"
    CC_BY_NC_ND_4_0 = "CC-BY-NC-ND-4.0"

class KnobAsset(BaseModel):
    """Model representing a knob asset from g200kg WebKnobMan gallery."""
    id: int
    file: str
    author: Optional[str] = None
    license: LicenseType
    date: str
    comment: Optional[str] = ""
    tags: str = ""
    size: Optional[str] = None
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    local_path: Optional[str] = None
    local_thumbnail_path: Optional[str] = None
    downloaded: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file": self.file,
            "author": self.author,
            "license": self.license,
            "date": self.date,
            "comment": self.comment,
            "tags": self.tags,
            "size": self.size,
            "thumbnail_url": self.thumbnail_url,
            "download_url": self.download_url,
            "local_path": self.local_path,
            "local_thumbnail_path": self.local_thumbnail_path,
            "downloaded": self.downloaded
        }
    
class KnobGalleryResponse(BaseModel):
    """Model representing a response containing knob assets."""
    knobs: List[KnobAsset]
    total: int
    page: int = 1
    total_pages: int = 1

class ScrapeStatus(BaseModel):
    """Model representing the status of a scraping operation."""
    in_progress: bool = False
    total_items: int = 0
    completed_items: int = 0
    success: bool = False
    error_message: Optional[str] = None