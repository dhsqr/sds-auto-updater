"""Web scrapers for various chemical suppliers."""

from .base_scraper import BaseScraper
from .sigma_aldrich import SigmaAldrichScraper
from .merck import MerckScraper
from .srl_chemicals import SRLChemicalsScraper

__all__ = ['BaseScraper', 'SigmaAldrichScraper', 'MerckScraper', 'SRLChemicalsScraper']
