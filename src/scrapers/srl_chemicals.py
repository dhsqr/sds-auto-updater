"""
SRL Chemicals SDS scraper.
Indian chemical supplier - uses simpler HTML structure.
"""

import time
import logging
from typing import Optional
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base_scraper import BaseScraper
from ..config import SCRAPE_DELAY_SECONDS

logger = logging.getLogger(__name__)


class SRLChemicalsScraper(BaseScraper):
    """Scraper for SRL Chemicals (Indian supplier)."""
    
    def __init__(self):
        super().__init__(
            supplier_name="srl_chemicals",
            base_url="https://www.srlchem.com",
            use_selenium=False  # Try requests first
        )
    
    def search_chemical(self, chemical_name: str, cas_number: str) -> Optional[str]:
        """
        Search for a chemical on SRL Chemicals.
        """
        try:
            # Search by CAS number first
            search_term = cas_number if cas_number else chemical_name
            search_url = f"{self.base_url}/search/?q={quote(search_term)}"
            
            logger.info(f"Searching SRL Chemicals: {search_url}")
            
            # Try with requests first
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Look for product links in search results
            product_links = soup.select("a[href*='/product/'], a[href*='/products/'], .product-link")
            
            if product_links:
                href = product_links[0].get("href")
                product_url = urljoin(self.base_url, href)
                logger.info(f"Found SRL product page: {product_url}")
                return product_url
            
            # Try alternative search pattern
            product_cards = soup.select(".product-card, .product-item, .search-result-item")
            
            for card in product_cards:
                link = card.find("a", href=True)
                if link:
                    product_url = urljoin(self.base_url, link["href"])
                    logger.info(f"Found SRL product page: {product_url}")
                    return product_url
            
            # If requests didn't work, try with Selenium
            return self._search_with_selenium(chemical_name, cas_number)
            
        except Exception as e:
            logger.error(f"Error searching SRL for {chemical_name}: {e}")
            return self._search_with_selenium(chemical_name, cas_number)
    
    def _search_with_selenium(self, chemical_name: str, cas_number: str) -> Optional[str]:
        """Fallback search using Selenium."""
        try:
            self._init_selenium()
            
            search_term = cas_number if cas_number else chemical_name
            search_url = f"{self.base_url}/search/?q={quote(search_term)}"
            
            self.driver.get(search_url)
            time.sleep(SCRAPE_DELAY_SECONDS * 2)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/product']"))
                )
                
                product_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/product']")
                if product_links:
                    return product_links[0].get_attribute("href")
                    
            except TimeoutException:
                logger.warning("Timeout in Selenium search for SRL")
            
            return None
            
        except Exception as e:
            logger.error(f"Selenium search failed for SRL: {e}")
            return None
    
    def get_sds_download_url(self, product_url: str) -> Optional[str]:
        """
        Get the SDS download URL from an SRL product page.
        """
        try:
            logger.info(f"Getting SDS from SRL product page: {product_url}")
            
            response = self.session.get(product_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Look for SDS/MSDS download links
            sds_patterns = [
                "a[href*='sds']",
                "a[href*='SDS']",
                "a[href*='msds']",
                "a[href*='MSDS']",
                "a[href*='safety-data']",
                "a[href*='.pdf']"
            ]
            
            for pattern in sds_patterns:
                links = soup.select(pattern)
                for link in links:
                    href = link.get("href", "")
                    text = link.get_text().lower()
                    
                    # Check if it's actually an SDS link
                    if any(kw in href.lower() or kw in text for kw in ["sds", "msds", "safety"]):
                        download_url = urljoin(self.base_url, href)
                        logger.info(f"Found SRL SDS link: {download_url}")
                        return download_url
            
            # Try looking for download buttons
            download_buttons = soup.select("a.download, button.download, [class*='download']")
            for btn in download_buttons:
                href = btn.get("href")
                if href and ".pdf" in href.lower():
                    return urljoin(self.base_url, href)
            
            # Fallback: Try with Selenium
            return self._get_sds_url_with_selenium(product_url)
            
        except Exception as e:
            logger.error(f"Error getting SRL SDS URL: {e}")
            return self._get_sds_url_with_selenium(product_url)
    
    def _get_sds_url_with_selenium(self, product_url: str) -> Optional[str]:
        """Fallback method to get SDS URL using Selenium."""
        try:
            self._init_selenium()
            
            self.driver.get(product_url)
            time.sleep(SCRAPE_DELAY_SECONDS * 2)
            
            # Look for SDS links
            sds_links = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a[href*='sds'], a[href*='SDS'], a[href*='msds'], a[href*='.pdf']"
            )
            
            for link in sds_links:
                href = link.get_attribute("href")
                text = link.text.lower()
                
                if any(kw in (href or "").lower() or kw in text for kw in ["sds", "msds", "safety"]):
                    logger.info(f"Found SRL SDS link via Selenium: {href}")
                    return href
            
            return None
            
        except Exception as e:
            logger.error(f"Selenium fallback failed for SRL: {e}")
            return None
