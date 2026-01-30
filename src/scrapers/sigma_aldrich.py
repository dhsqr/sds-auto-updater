"""
Sigma-Aldrich SDS scraper.
Uses Selenium due to dynamic JavaScript content.
"""

import re
import time
import logging
from typing import Optional
from urllib.parse import urljoin, quote

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_scraper import BaseScraper
from ..config import SCRAPE_DELAY_SECONDS

logger = logging.getLogger(__name__)


class SigmaAldrichScraper(BaseScraper):
    """Scraper for Sigma-Aldrich (now part of MilliporeSigma)."""
    
    def __init__(self):
        super().__init__(
            supplier_name="sigma_aldrich",
            base_url="https://www.sigmaaldrich.com",
            use_selenium=True
        )
        self.country = "IN"  # Default to India
        self.language = "en"
    
    def search_chemical(self, chemical_name: str, cas_number: str) -> Optional[str]:
        """
        Search for a chemical on Sigma-Aldrich.
        
        Priority: CAS number search (more reliable) > name search
        """
        try:
            self._init_selenium()
            
            # Search by CAS number first (more reliable)
            search_term = cas_number if cas_number else chemical_name
            search_url = f"{self.base_url}/{self.country}/{self.language}/search/{quote(search_term)}?focus=products"
            
            logger.info(f"Searching Sigma-Aldrich: {search_url}")
            self.driver.get(search_url)
            time.sleep(SCRAPE_DELAY_SECONDS * 2)  # Wait for dynamic content
            
            # Handle cookie consent if present
            self._handle_cookie_consent()
            
            # Look for product links in search results
            try:
                # Wait for search results to load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='product-card'], .MuiCard-root, a[href*='/product/']"))
                )
                
                # Try to find product links
                product_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
                
                if product_links:
                    # Get the first product link
                    product_url = product_links[0].get_attribute("href")
                    logger.info(f"Found product page: {product_url}")
                    return product_url
                
                # Alternative: Look for product cards
                product_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='product-card']")
                if product_cards:
                    # Click on the first product card
                    product_cards[0].click()
                    time.sleep(SCRAPE_DELAY_SECONDS)
                    return self.driver.current_url
                    
            except TimeoutException:
                logger.warning(f"Timeout waiting for search results for {chemical_name}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Sigma-Aldrich for {chemical_name}: {e}")
            return None
    
    def get_sds_download_url(self, product_url: str) -> Optional[str]:
        """
        Get the SDS download URL from a Sigma-Aldrich product page.
        """
        try:
            if not self.driver:
                self._init_selenium()
            
            logger.info(f"Getting SDS from product page: {product_url}")
            self.driver.get(product_url)
            time.sleep(SCRAPE_DELAY_SECONDS * 2)
            
            # Handle cookie consent if present
            self._handle_cookie_consent()
            
            # Try multiple approaches to find SDS link
            sds_url = self._find_sds_link_method1()
            if sds_url:
                return sds_url
            
            sds_url = self._find_sds_link_method2()
            if sds_url:
                return sds_url
            
            sds_url = self._find_sds_link_method3()
            if sds_url:
                return sds_url
            
            logger.warning("Could not find SDS download link on product page")
            return None
            
        except Exception as e:
            logger.error(f"Error getting SDS URL: {e}")
            return None
    
    def _handle_cookie_consent(self):
        """Handle cookie consent popup if present."""
        try:
            consent_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "button[id*='accept'], button[class*='accept'], button[data-testid*='accept']"
            )
            for button in consent_buttons:
                if button.is_displayed():
                    button.click()
                    time.sleep(1)
                    break
        except Exception:
            pass  # Consent popup may not be present
    
    def _find_sds_link_method1(self) -> Optional[str]:
        """Method 1: Look for direct SDS/MSDS links."""
        try:
            # Look for links containing "sds" or "msds"
            sds_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a[href*='sds'], a[href*='SDS'], a[href*='msds'], a[href*='MSDS']"
            )
            
            for link in sds_links:
                href = link.get_attribute("href")
                if href and (".pdf" in href.lower() or "sds" in href.lower()):
                    logger.info(f"Found SDS link (method 1): {href}")
                    return href
            
            return None
        except Exception:
            return None
    
    def _find_sds_link_method2(self) -> Optional[str]:
        """Method 2: Look for 'Safety Data Sheet' text links."""
        try:
            # Find links by text content
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            keywords = ["safety data sheet", "sds", "msds", "material safety"]
            for link in links:
                try:
                    text = link.text.lower()
                    if any(kw in text for kw in keywords):
                        href = link.get_attribute("href")
                        if href:
                            logger.info(f"Found SDS link (method 2): {href}")
                            return href
                except Exception:
                    continue
            
            return None
        except Exception:
            return None
    
    def _find_sds_link_method3(self) -> Optional[str]:
        """Method 3: Look in documentation/downloads section."""
        try:
            # Try clicking on documentation tab/section
            doc_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid*='document'], [class*='document'], [id*='document'], button:contains('Documents')"
            )
            
            for elem in doc_elements:
                try:
                    if elem.is_displayed() and elem.is_enabled():
                        elem.click()
                        time.sleep(SCRAPE_DELAY_SECONDS)
                        
                        # Now look for SDS links
                        sds_url = self._find_sds_link_method1() or self._find_sds_link_method2()
                        if sds_url:
                            return sds_url
                except Exception:
                    continue
            
            return None
        except Exception:
            return None
    
    def build_direct_sds_url(self, product_number: str, country: str = "IN", language: str = "en") -> str:
        """
        Build a direct SDS URL if we know the product number.
        This is a fallback method using Sigma-Aldrich's SDS API pattern.
        """
        # Sigma-Aldrich SDS URL pattern (may change)
        return f"https://www.sigmaaldrich.com/IN/en/sds/{product_number}"
