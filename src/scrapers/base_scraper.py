"""
Base scraper class for SDS downloads.
All supplier-specific scrapers inherit from this class.
"""

import os
import time
import hashlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from ..config import SDS_STORAGE_PATH, SCRAPE_DELAY_SECONDS, MAX_RETRIES, REQUEST_TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for SDS scrapers."""
    
    def __init__(self, supplier_name: str, base_url: str, use_selenium: bool = False):
        self.supplier_name = supplier_name
        self.base_url = base_url
        self.use_selenium = use_selenium
        self.driver = None
        self.session = requests.Session()
        
        # Set up request headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.session.headers.update(self.headers)
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver with Chrome."""
        if self.driver is not None:
            return
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
        
        # Set download preferences
        prefs = {
            "download.default_directory": str(SDS_STORAGE_PATH),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(REQUEST_TIMEOUT)
    
    def _close_selenium(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    @abstractmethod
    def search_chemical(self, chemical_name: str, cas_number: str) -> Optional[str]:
        """
        Search for a chemical and return the product page URL.
        
        Args:
            chemical_name: Name of the chemical
            cas_number: CAS registry number
            
        Returns:
            URL of the product page, or None if not found
        """
        pass
    
    @abstractmethod
    def get_sds_download_url(self, product_url: str) -> Optional[str]:
        """
        Get the direct download URL for the SDS PDF.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Direct download URL for the SDS PDF, or None if not found
        """
        pass
    
    def download_sds(self, chemical_name: str, cas_number: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Download the SDS for a chemical.
        
        Args:
            chemical_name: Name of the chemical
            cas_number: CAS registry number
            
        Returns:
            Tuple of (file_path, file_hash) or (None, None) if download failed
        """
        try:
            logger.info(f"Searching for {chemical_name} (CAS: {cas_number}) on {self.supplier_name}")
            
            # Search for the chemical
            product_url = self.search_chemical(chemical_name, cas_number)
            if not product_url:
                logger.warning(f"Could not find {chemical_name} on {self.supplier_name}")
                return None, None
            
            time.sleep(SCRAPE_DELAY_SECONDS)
            
            # Get download URL
            download_url = self.get_sds_download_url(product_url)
            if not download_url:
                logger.warning(f"Could not find SDS download link for {chemical_name}")
                return None, None
            
            time.sleep(SCRAPE_DELAY_SECONDS)
            
            # Download the PDF
            file_path = self._download_pdf(download_url, chemical_name, cas_number)
            if file_path:
                file_hash = self._calculate_hash(file_path)
                logger.info(f"Successfully downloaded SDS for {chemical_name}")
                return file_path, file_hash
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error downloading SDS for {chemical_name}: {e}")
            return None, None
        finally:
            if self.use_selenium:
                self._close_selenium()
    
    def _download_pdf(self, url: str, chemical_name: str, cas_number: str) -> Optional[str]:
        """Download a PDF from a URL."""
        for attempt in range(MAX_RETRIES):
            try:
                # Clean chemical name for filename
                safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in chemical_name)
                safe_cas = cas_number.replace("-", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                filename = f"{safe_name}_{safe_cas}_{self.supplier_name}_{timestamp}.pdf"
                file_path = SDS_STORAGE_PATH / filename
                
                response = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
                response.raise_for_status()
                
                # Check if it's actually a PDF
                content_type = response.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
                    logger.warning(f"Response may not be a PDF: {content_type}")
                
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify the file is a valid PDF
                with open(file_path, "rb") as f:
                    header = f.read(5)
                    if header != b"%PDF-":
                        logger.warning(f"Downloaded file is not a valid PDF")
                        os.remove(file_path)
                        return None
                
                return str(file_path)
                
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                time.sleep(SCRAPE_DELAY_SECONDS * (attempt + 1))
        
        return None
    
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Wait for an element to be present in Selenium."""
        if not self.driver:
            self._init_selenium()
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def wait_for_clickable(self, by: By, value: str, timeout: int = 10):
        """Wait for an element to be clickable in Selenium."""
        if not self.driver:
            self._init_selenium()
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
