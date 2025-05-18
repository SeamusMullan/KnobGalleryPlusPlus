import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Base URL for the WebKnobMan gallery
    WEBKNOBMAN_GALLERY_URL: str = "https://www.g200kg.com/en/webknobman/gallery.php"
    
    # Directory to store downloaded knobs
    # on windows this will be set to C:\Users\<username>\KnobGallery
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", os.path.join(os.path.expanduser("~"), "KnobGallery")))
      # Multithreaded download settings
    MAX_DOWNLOAD_WORKERS: int = int(os.getenv("MAX_DOWNLOAD_WORKERS", (os.cpu_count() or 4) * 4))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 10))
    DOWNLOAD_BATCH_SIZE: int = int(os.getenv("DOWNLOAD_BATCH_SIZE", 20))
    DOWNLOAD_RETRY_ATTEMPTS: int = int(os.getenv("DOWNLOAD_RETRY_ATTEMPTS", 3))
    
    # Create download directory if it doesn't exist
    def __init__(self):
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

settings = Settings()