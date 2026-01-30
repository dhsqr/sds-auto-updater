"""
Scheduler for automated SDS checking.
Runs daily checks and weekly digest emails.
"""

import logging
import schedule
import time
from datetime import datetime
from typing import Optional

from .config import DAILY_CHECK_HOUR, WEEKLY_DIGEST_DAY
from .database import db, DatabaseManager
from .pdf_processor import pdf_processor
from .change_detector import change_detector
from .alerts.email_alerts import email_service
from .scrapers import SigmaAldrichScraper, MerckScraper, SRLChemicalsScraper

logger = logging.getLogger(__name__)


class SDSScheduler:
    """Scheduler for automated SDS monitoring."""
    
    def __init__(self):
        self.scrapers = {
            "sigma_aldrich": SigmaAldrichScraper(),
            "merck": MerckScraper(),
            "srl_chemicals": SRLChemicalsScraper()
        }
        self.db = db
        self.is_running = False
    
    def check_single_chemical(self, chemical_id: int) -> dict:
        """
        Check a single chemical for SDS updates.
        
        Args:
            chemical_id: ID of the chemical to check
            
        Returns:
            Dictionary with check results
        """
        session = self.db.get_session()
        try:
            from .database import Chemical
            chemical = session.query(Chemical).filter(Chemical.id == chemical_id).first()
            
            if not chemical:
                return {"success": False, "error": "Chemical not found"}
            
            return self._check_chemical(chemical)
        finally:
            session.close()
    
    def _check_chemical(self, chemical) -> dict:
        """Internal method to check a chemical for updates."""
        result = {
            "chemical_name": chemical.chemical_name,
            "cas_number": chemical.cas_number,
            "success": False,
            "changes": [],
            "is_updated": False
        }
        
        try:
            logger.info(f"Checking {chemical.chemical_name} ({chemical.cas_number})")
            
            # Get the appropriate scraper
            scraper = self.scrapers.get(chemical.supplier)
            if not scraper:
                result["error"] = f"No scraper for supplier: {chemical.supplier}"
                return result
            
            # Download SDS
            file_path, file_hash = scraper.download_sds(
                chemical.chemical_name, 
                chemical.cas_number
            )
            
            if not file_path:
                result["error"] = "Failed to download SDS"
                self.db.update_chemical_check_time(chemical.id)
                return result
            
            # Check if this is a new version
            existing_version = self.db.get_latest_sds_version(chemical.id)
            
            if existing_version and existing_version.file_hash == file_hash:
                logger.info(f"No changes for {chemical.chemical_name}")
                self.db.update_chemical_check_time(chemical.id)
                result["success"] = True
                return result
            
            # Process the new PDF
            extracted_data = pdf_processor.process_sds(file_path)
            
            # Save new version
            new_version = self.db.add_sds_version(
                chemical_id=chemical.id,
                file_path=file_path,
                extracted_data=extracted_data
            )
            
            result["is_updated"] = True
            result["success"] = True
            
            # If we have a previous version, detect changes
            if existing_version:
                old_sections = {
                    "hazard_statements": existing_version.hazard_statements or "",
                    "ppe_requirements": existing_version.ppe_requirements or "",
                    "storage_conditions": existing_version.storage_conditions or "",
                    "first_aid_measures": existing_version.first_aid_measures or "",
                    "handling_precautions": existing_version.handling_precautions or "",
                    "disposal_requirements": existing_version.disposal_requirements or "",
                }
                
                new_sections = {
                    "hazard_statements": extracted_data.get("hazard_statements", ""),
                    "ppe_requirements": extracted_data.get("ppe_requirements", ""),
                    "storage_conditions": extracted_data.get("storage_conditions", ""),
                    "first_aid_measures": extracted_data.get("first_aid_measures", ""),
                    "handling_precautions": extracted_data.get("handling_precautions", ""),
                    "disposal_requirements": extracted_data.get("disposal_requirements", ""),
                }
                
                changes = change_detector.compare_sections(
                    old_sections, new_sections, chemical.chemical_name
                )
                
                # Store changes in database
                for change in changes:
                    self.db.add_change(
                        chemical_id=chemical.id,
                        old_version_id=existing_version.id,
                        new_version_id=new_version.id,
                        severity=change.severity,
                        section=change.section,
                        old_value=change.old_value,
                        new_value=change.new_value,
                        ai_summary=change.summary
                    )
                
                result["changes"] = [
                    {
                        "section": c.section,
                        "severity": c.severity,
                        "summary": c.summary,
                        "action_required": c.action_required
                    }
                    for c in changes
                ]
                
                # Send alert if there are changes
                if changes:
                    email_service.send_change_alert(chemical, result["changes"])
            
            self.db.update_chemical_check_time(chemical.id)
            return result
            
        except Exception as e:
            logger.error(f"Error checking {chemical.chemical_name}: {e}")
            result["error"] = str(e)
            return result
    
    def run_daily_check(self):
        """Run the daily check on all chemicals."""
        logger.info("Starting daily SDS check...")
        
        chemicals = self.db.get_all_chemicals()
        results = {
            "total": len(chemicals),
            "checked": 0,
            "updated": 0,
            "errors": 0,
            "chemicals_with_changes": []
        }
        
        for chemical in chemicals:
            try:
                check_result = self._check_chemical(chemical)
                results["checked"] += 1
                
                if check_result.get("is_updated"):
                    results["updated"] += 1
                    if check_result.get("changes"):
                        results["chemicals_with_changes"].append({
                            "name": chemical.chemical_name,
                            "cas": chemical.cas_number,
                            "changes": check_result["changes"]
                        })
                
                if check_result.get("error"):
                    results["errors"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing {chemical.chemical_name}: {e}")
                results["errors"] += 1
        
        logger.info(f"Daily check complete: {results['checked']} checked, "
                   f"{results['updated']} updated, {results['errors']} errors")
        
        return results
    
    def run_weekly_digest(self):
        """Send the weekly digest email."""
        logger.info("Sending weekly digest...")
        success = email_service.send_weekly_digest()
        if success:
            logger.info("Weekly digest sent successfully")
        else:
            logger.error("Failed to send weekly digest")
        return success
    
    def start(self):
        """Start the scheduler."""
        logger.info(f"Starting scheduler - Daily check at {DAILY_CHECK_HOUR}:00")
        
        # Schedule daily check
        schedule.every().day.at(f"{DAILY_CHECK_HOUR:02d}:00").do(self.run_daily_check)
        
        # Schedule weekly digest
        if WEEKLY_DIGEST_DAY.lower() == "friday":
            schedule.every().friday.at("18:00").do(self.run_weekly_digest)
        elif WEEKLY_DIGEST_DAY.lower() == "monday":
            schedule.every().monday.at("09:00").do(self.run_weekly_digest)
        
        self.is_running = True
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        logger.info("Scheduler stopped")


# Global instance
scheduler = SDSScheduler()
