"""
PDF Processing module for extracting and analyzing SDS content.
Uses pdfplumber for text extraction and Google Gemini for intelligent section parsing.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional, List

import pdfplumber
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from .config import GOOGLE_API_KEY, GEMINI_MODEL
from .utils import RateLimiter, retry_on_failure

logger = logging.getLogger(__name__)

# Rate limiter: max 15 API calls per minute (Gemini free tier limit)
api_rate_limiter = RateLimiter(max_calls=15, time_window=60.0)


class SDSSections(BaseModel):
    """Structured output for SDS sections."""
    hazard_statements: str = Field(description="GHS hazard codes and descriptions (H-statements)")
    precautionary_statements: str = Field(description="GHS precautionary statements (P-statements)")
    ppe_requirements: str = Field(description="Required personal protective equipment")
    first_aid_measures: str = Field(description="First aid measures for different exposure types")
    storage_conditions: str = Field(description="Storage temperature, conditions, incompatibilities")
    disposal_requirements: str = Field(description="Disposal methods and considerations")
    handling_precautions: str = Field(description="Safe handling procedures")
    emergency_procedures: str = Field(description="Emergency response procedures")


class PDFProcessor:
    """Process SDS PDFs and extract key safety information."""
    
    def __init__(self):
        self.llm = None
        if GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                temperature=0,
                google_api_key=GOOGLE_API_KEY
            )
        
        self.section_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing Safety Data Sheets (SDS/MSDS) for chemicals.
Extract the following safety-critical information from the SDS text provided.
Be thorough and extract ALL relevant information for each section.
If a section is not found or not applicable, write "Not specified in document".

Return the information in a structured JSON format."""),
            ("human", """Extract the following sections from this SDS document:

1. **Hazard Statements**: All GHS H-codes and their descriptions (e.g., H302 - Harmful if swallowed)
2. **Precautionary Statements**: All GHS P-codes (e.g., P264 - Wash hands thoroughly after handling)
3. **PPE Requirements**: Eye protection, gloves, respiratory protection, protective clothing
4. **First Aid Measures**: For inhalation, skin contact, eye contact, ingestion
5. **Storage Conditions**: Temperature limits, ventilation, incompatibilities, container requirements
6. **Disposal Requirements**: Waste disposal methods, environmental considerations
7. **Handling Precautions**: Safe handling procedures, hygiene measures
8. **Emergency Procedures**: Spill/leak procedures, fire-fighting measures

SDS DOCUMENT TEXT:
{sds_text}

Return a JSON object with these exact keys:
- hazard_statements
- precautionary_statements
- ppe_requirements
- first_aid_measures
- storage_conditions
- disposal_requirements
- handling_precautions
- emergency_procedures""")
        ])
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            full_text = "\n\n".join(text_content)
            logger.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    @api_rate_limiter
    @retry_on_failure(max_retries=2, delay=2.0)
    def extract_sections_with_ai(self, sds_text: str) -> Dict[str, str]:
        """
        Use AI to extract and structure SDS sections.

        Args:
            sds_text: Raw text from SDS PDF

        Returns:
            Dictionary of extracted sections
        """
        if not self.llm:
            logger.warning("Gemini not configured, using regex-based extraction")
            return self._extract_sections_regex(sds_text)

        try:
            # Truncate text if too long (Gemini context limit)
            max_chars = 100000
            if len(sds_text) > max_chars:
                logger.warning(f"SDS text truncated from {len(sds_text)} to {max_chars} characters")
                sds_text = sds_text[:max_chars] + "\n...[truncated]"

            messages = self.section_extraction_prompt.format_messages(sds_text=sds_text)
            response = self.llm.invoke(messages)
            
            # Parse the JSON response
            content = response.content
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            sections = json.loads(content)
            logger.info("Successfully extracted SDS sections with AI")
            return sections
            
        except Exception as e:
            logger.error(f"AI extraction failed: {e}, falling back to regex")
            return self._extract_sections_regex(sds_text)
    
    def _extract_sections_regex(self, sds_text: str) -> Dict[str, str]:
        """
        Fallback: Extract sections using regex patterns.
        Less accurate than AI but works without API.
        """
        sections = {
            "hazard_statements": "",
            "precautionary_statements": "",
            "ppe_requirements": "",
            "first_aid_measures": "",
            "storage_conditions": "",
            "disposal_requirements": "",
            "handling_precautions": "",
            "emergency_procedures": ""
        }
        
        # Pattern for H-statements (hazard)
        h_pattern = r'H\d{3}[A-Za-z]?\s*[-:]\s*[^\n]+'
        h_matches = re.findall(h_pattern, sds_text)
        sections["hazard_statements"] = "\n".join(h_matches) if h_matches else "Not found"
        
        # Pattern for P-statements (precautionary)
        p_pattern = r'P\d{3}[+P\d]*\s*[-:]\s*[^\n]+'
        p_matches = re.findall(p_pattern, sds_text)
        sections["precautionary_statements"] = "\n".join(p_matches) if p_matches else "Not found"
        
        # Extract section 4 (First Aid)
        section4_pattern = r'(?:SECTION\s*4|4\.\s*FIRST[- ]AID).*?(?=SECTION\s*5|5\.\s*FIRE|\Z)'
        section4_match = re.search(section4_pattern, sds_text, re.IGNORECASE | re.DOTALL)
        if section4_match:
            sections["first_aid_measures"] = section4_match.group()[:2000]
        
        # Extract section 7 (Handling and Storage)
        section7_pattern = r'(?:SECTION\s*7|7\.\s*HANDLING).*?(?=SECTION\s*8|8\.\s*EXPOSURE|\Z)'
        section7_match = re.search(section7_pattern, sds_text, re.IGNORECASE | re.DOTALL)
        if section7_match:
            content = section7_match.group()[:2000]
            sections["handling_precautions"] = content
            sections["storage_conditions"] = content
        
        # Extract section 8 (PPE/Exposure Controls)
        section8_pattern = r'(?:SECTION\s*8|8\.\s*EXPOSURE).*?(?=SECTION\s*9|9\.\s*PHYSICAL|\Z)'
        section8_match = re.search(section8_pattern, sds_text, re.IGNORECASE | re.DOTALL)
        if section8_match:
            sections["ppe_requirements"] = section8_match.group()[:2000]
        
        # Extract section 13 (Disposal)
        section13_pattern = r'(?:SECTION\s*13|13\.\s*DISPOSAL).*?(?=SECTION\s*14|14\.\s*TRANSPORT|\Z)'
        section13_match = re.search(section13_pattern, sds_text, re.IGNORECASE | re.DOTALL)
        if section13_match:
            sections["disposal_requirements"] = section13_match.group()[:2000]
        
        return sections
    
    def process_sds(self, pdf_path: str) -> Dict[str, str]:
        """
        Full processing pipeline for an SDS PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with full_text and extracted sections
        """
        # Check if file exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Extract text
        full_text = self.extract_text_from_pdf(pdf_path)
        
        if not full_text:
            logger.warning(f"No text extracted from {pdf_path}")
            return {"full_text": "", "extraction_failed": True}
        
        # Extract sections
        sections = self.extract_sections_with_ai(full_text)
        
        # Combine results
        result = {
            "full_text": full_text,
            **sections
        }
        
        return result
    
    def get_section_summary(self, sections: Dict[str, str]) -> str:
        """
        Generate a brief summary of the key safety information.
        """
        summary_parts = []
        
        if sections.get("hazard_statements") and sections["hazard_statements"] != "Not found":
            summary_parts.append(f"**Hazards**: {sections['hazard_statements'][:200]}...")
        
        if sections.get("ppe_requirements") and sections["ppe_requirements"] != "Not found":
            summary_parts.append(f"**PPE**: {sections['ppe_requirements'][:200]}...")
        
        if sections.get("storage_conditions") and sections["storage_conditions"] != "Not found":
            summary_parts.append(f"**Storage**: {sections['storage_conditions'][:200]}...")
        
        return "\n\n".join(summary_parts) if summary_parts else "No key sections extracted"


# Global instance
pdf_processor = PDFProcessor()
