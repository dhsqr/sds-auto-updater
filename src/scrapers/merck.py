"""
Merck (MilliporeSigma) SDS scraper.
Uses Selenium due to dynamic JavaScript content.
"""

import time
import logging
from typing import Optional
from urllib.parse import quote

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base_scraper import BaseScraper
from ..config import SCRAPE_DELAY_SECONDS

logger = logging.getLogger(__name__)


class MerckScraper(BaseScraper):
    """Scraper for Merck / MilliporeSigma."""
    
    def __init__(self):
        super().__init__(
            supplier_name="merck",
            base_url="https://www.merckmillipore.com",
            use_selenium=True
        )
        self.country = "IN"
        self.language = "en"
    
    def search_chemical(self, chemical_name: str, cas_number: str) -> Optional[str]:
        """
        Search for a chemical on Merck.
        """
        try:
            self._init_selenium()
            
            # Search by CAS number (more reliable)
            search_term = cas_number if cas_number else chemical_name
            search_url = f"{self.base_url}/{self.country}/{self.language}/search/{quote(search_term)}"
            
            logger.info(f"Searching Merck: {search_url}")
            self.driver.get(search_url)
            time.sleep(SCRAPE_DELAY_SECONDS * 2)
            
            # Handle cookie consent
            self._handle_cookie_consent()
            
            try:
                # Wait for search results
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/product/'], .product-card, .search-result"))
                )
                
                # Look for product links
                product_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
                
                if product_links:
                    product_url = product_links[0].get_attribute("href")
                    logger.info(f"Found Merck product page: {product_url}")
                    return product_url
                
            except TimeoutException:
                logger.warning(f"Timeout waiting for Merck search results for {chemical_name}")
                
                # Try alternative search URL
                alt_url = f"https://www.sigmaaldrich.com/IN/en/search/{quote(search_term)}?focus=products"
                self.driver.get(alt_url)
                time.sleep(SCRAPE_DELAY_SECONDS * 2)
                
                product_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
                if product_links:
                    return product_links[0].get_attribute("href")
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Merck for {chemical_name}: {e}")
            return None
    
    def get_sds_download_url(self, product_url: str) -> Optional[str]:
        """
        Get the SDS download URL from a Merck product page.
        """
        try:
            if not self.driver:
                self._init_selenium()
            
            logger.info(f"Getting SDS from Merck product page: {product_url}")
            self.driver.get(product_url)
            time.sleep(SCRAPE_DELAY_SECONDS * 2)
            
            # Handle cookie consent
            self._handle_cookie_consent()
            
            # Look for SDS links
            sds_selectors = [
                "a[href*='sds']",
                "a[href*='SDS']",
                "a[href*='safety-data-sheet']",
                "a[href*='msds']",
                "[data-testid*='sds']",
                "button:contains('SDS')"
            ]
            
            for selector in sds_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        href = elem.get_attribute("href")
                        if href:
                            logger.info(f"Found Merck SDS link: {href}")
                            return href
                except Exception:
                    continue
            
            # Try clicking on Documents tab
            try:
                doc_tabs = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "[data-testid*='document'], button[class*='document'], a[class*='document']"
                )
                for tab in doc_tabs:
                    if tab.is_displayed():
                        tab.click()
                        time.sleep(SCRAPE_DELAY_SECONDS)
                        
                        # Look for SDS after clicking
                        sds_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='sds'], a[href*='SDS']")
                        if sds_links:
                            return sds_links[0].get_attribute("href")
            except Exception:
                pass
            
            logger.warning("Could not find SDS link on Merck product page")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Merck SDS URL: {e}")
            return None
    
    def _handle_cookie_consent(self):
        """Handle cookie consent popup."""
        try:
            consent_buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[id*='accept'], button[class*='accept'], #onetrust-accept-btn-handler"
            )
            for button in consent_buttons:
                if button.is_displayed():
                    button.click()
                    time.sleep(1)
                    break
        except Exception:
            pass
