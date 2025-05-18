import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Base URL for the WebKnobMan gallery
    WEBKNOBMAN_GALLERY_URL: str = "https://www.g200kg.com/en/webknobman/gallery.php"
    
    # Directory to store downloaded knobs
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", os.path.join(os.path.expanduser("~"), "KnobGallery")))
    
    # Create download directory if it doesn't exist
    def __init__(self):
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

settings = Settings()