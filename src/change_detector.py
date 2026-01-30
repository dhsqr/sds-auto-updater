"""
Change Detection module for comparing SDS versions.
Uses AI for intelligent change analysis and severity classification.
"""

import json
import logging
import difflib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from .config import GOOGLE_API_KEY, GEMINI_MODEL, SEVERITY_LEVELS

logger = logging.getLogger(__name__)


@dataclass
class Change:
    """Represents a single change between SDS versions."""
    section: str
    old_value: str
    new_value: str
    severity: str  # CRITICAL, IMPORTANT, MINOR
    summary: str
    action_required: str


class ChangeDetector:
    """Detect and analyze changes between SDS versions."""
    
    def __init__(self):
        self.llm = None
        if GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                temperature=0,
                google_api_key=GOOGLE_API_KEY
            )
        
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a chemical safety expert analyzing changes between two versions of a Safety Data Sheet (SDS).

Your task is to:
1. Identify what specifically changed
2. Explain why this change matters for workplace safety
3. Determine the severity level
4. Recommend specific actions

SEVERITY LEVELS:
- CRITICAL: Changes to hazard warnings, PPE requirements, or storage conditions that could directly impact worker safety
- IMPORTANT: Changes to first aid measures, disposal methods, or handling precautions
- MINOR: Contact information updates, formatting changes, or clarifications that don't affect safety protocols

Be specific and actionable in your analysis."""),
            ("human", """Compare these two SDS versions and analyze the changes:

CHEMICAL: {chemical_name}
SECTION: {section_name}

OLD VERSION:
{old_content}

NEW VERSION:
{new_content}

Provide your analysis as JSON with these fields:
- "changes_found": boolean (true if meaningful changes detected)
- "severity": "CRITICAL" | "IMPORTANT" | "MINOR"
- "summary": Brief description of what changed (1-2 sentences)
- "safety_impact": Why this matters for safety (1-2 sentences)
- "action_required": Specific action the company should take (1-2 sentences)
- "key_differences": List of specific differences found""")
        ])
    
    def compare_file_hashes(self, old_hash: str, new_hash: str) -> bool:
        """
        Quick check if files are different using hashes.
        
        Returns:
            True if files are different, False if identical
        """
        return old_hash != new_hash
    
    def compare_sections(self, old_sections: Dict[str, str], new_sections: Dict[str, str], 
                         chemical_name: str) -> List[Change]:
        """
        Compare sections between two SDS versions.
        
        Args:
            old_sections: Dictionary of sections from old SDS
            new_sections: Dictionary of sections from new SDS
            chemical_name: Name of the chemical
            
        Returns:
            List of Change objects for detected changes
        """
        changes = []
        
        # Sections to compare in priority order
        sections_to_compare = [
            ("hazard_statements", "Hazard Statements"),
            ("ppe_requirements", "PPE Requirements"),
            ("storage_conditions", "Storage Conditions"),
            ("first_aid_measures", "First Aid Measures"),
            ("handling_precautions", "Handling Precautions"),
            ("disposal_requirements", "Disposal Requirements"),
            ("precautionary_statements", "Precautionary Statements"),
            ("emergency_procedures", "Emergency Procedures")
        ]
        
        for section_key, section_name in sections_to_compare:
            old_content = old_sections.get(section_key, "")
            new_content = new_sections.get(section_key, "")
            
            # Skip if both are empty or identical
            if not old_content and not new_content:
                continue
            if self._normalize_text(old_content) == self._normalize_text(new_content):
                continue
            
            # Analyze the change
            change = self._analyze_change(
                section_key=section_key,
                section_name=section_name,
                old_content=old_content,
                new_content=new_content,
                chemical_name=chemical_name
            )
            
            if change:
                changes.append(change)
        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "IMPORTANT": 1, "MINOR": 2}
        changes.sort(key=lambda c: severity_order.get(c.severity, 3))
        
        return changes
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (remove extra whitespace, lowercase)."""
        if not text:
            return ""
        return " ".join(text.lower().split())
    
    def _analyze_change(self, section_key: str, section_name: str,
                       old_content: str, new_content: str, 
                       chemical_name: str) -> Optional[Change]:
        """
        Analyze a specific change using AI or rule-based logic.
        """
        if self.llm:
            return self._analyze_with_ai(
                section_key, section_name, old_content, new_content, chemical_name
            )
        else:
            return self._analyze_with_rules(
                section_key, section_name, old_content, new_content, chemical_name
            )
    
    def _analyze_with_ai(self, section_key: str, section_name: str,
                        old_content: str, new_content: str,
                        chemical_name: str) -> Optional[Change]:
        """Use AI to analyze changes."""
        try:
            # Truncate content if too long
            max_chars = 3000
            old_truncated = old_content[:max_chars] if old_content else "[Empty]"
            new_truncated = new_content[:max_chars] if new_content else "[Empty]"
            
            messages = self.analysis_prompt.format_messages(
                chemical_name=chemical_name,
                section_name=section_name,
                old_content=old_truncated,
                new_content=new_truncated
            )
            
            response = self.llm.invoke(messages)
            content = response.content
            
            # Parse JSON response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            analysis = json.loads(content)
            
            if not analysis.get("changes_found", True):
                return None
            
            return Change(
                section=section_name,
                old_value=old_content[:500],
                new_value=new_content[:500],
                severity=analysis.get("severity", "IMPORTANT"),
                summary=analysis.get("summary", "Changes detected"),
                action_required=analysis.get("action_required", "Review changes")
            )
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._analyze_with_rules(
                section_key, section_name, old_content, new_content, chemical_name
            )
    
    def _analyze_with_rules(self, section_key: str, section_name: str,
                           old_content: str, new_content: str,
                           chemical_name: str) -> Optional[Change]:
        """Rule-based change analysis (fallback)."""
        # Determine severity based on section
        critical_sections = ["hazard_statements", "ppe_requirements", "storage_conditions"]
        important_sections = ["first_aid_measures", "handling_precautions", "disposal_requirements"]
        
        if section_key in critical_sections:
            severity = "CRITICAL"
        elif section_key in important_sections:
            severity = "IMPORTANT"
        else:
            severity = "MINOR"
        
        # Generate diff
        diff = self._generate_diff(old_content, new_content)
        
        # Create change
        return Change(
            section=section_name,
            old_value=old_content[:500],
            new_value=new_content[:500],
            severity=severity,
            summary=f"Changes detected in {section_name}",
            action_required=f"Review the updated {section_name} and update internal documentation"
        )
    
    def _generate_diff(self, old_text: str, new_text: str) -> str:
        """Generate a unified diff between two texts."""
        old_lines = old_text.splitlines() if old_text else []
        new_lines = new_text.splitlines() if new_text else []
        
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile='Previous Version',
            tofile='New Version',
            lineterm=''
        )
        
        return '\n'.join(diff)
    
    def get_diff_html(self, old_text: str, new_text: str) -> str:
        """Generate an HTML diff for display in the UI."""
        old_lines = old_text.splitlines() if old_text else []
        new_lines = new_text.splitlines() if new_text else []
        
        differ = difflib.HtmlDiff()
        return differ.make_table(
            old_lines, new_lines,
            fromdesc='Previous Version',
            todesc='New Version'
        )
    
    def generate_change_summary(self, changes: List[Change], chemical_name: str) -> str:
        """
        Generate a human-readable summary of all changes.
        """
        if not changes:
            return f"No significant changes detected for {chemical_name}"
        
        critical = [c for c in changes if c.severity == "CRITICAL"]
        important = [c for c in changes if c.severity == "IMPORTANT"]
        minor = [c for c in changes if c.severity == "MINOR"]
        
        summary_parts = [f"# SDS Changes for {chemical_name}\n"]
        
        if critical:
            summary_parts.append("## 🔴 CRITICAL Changes")
            for c in critical:
                summary_parts.append(f"- **{c.section}**: {c.summary}")
                summary_parts.append(f"  - Action Required: {c.action_required}")
        
        if important:
            summary_parts.append("\n## 🟡 IMPORTANT Changes")
            for c in important:
                summary_parts.append(f"- **{c.section}**: {c.summary}")
        
        if minor:
            summary_parts.append("\n## 🟢 MINOR Changes")
            for c in minor:
                summary_parts.append(f"- **{c.section}**: {c.summary}")
        
        return "\n".join(summary_parts)


# Global instance
change_detector = ChangeDetector()
