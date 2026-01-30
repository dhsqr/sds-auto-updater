"""
Email alert service for SDS change notifications.
Uses Gmail SMTP for sending emails.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..config import GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD, ALERT_RECIPIENTS
from ..database import db, Change, Chemical
from .templates import AlertTemplates

logger = logging.getLogger(__name__)


class EmailAlertService:
    """Service for sending email alerts about SDS changes."""
    
    def __init__(self):
        self.sender_email = GMAIL_SENDER_EMAIL
        self.app_password = GMAIL_APP_PASSWORD
        self.recipients = ALERT_RECIPIENTS
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.sender_email and self.app_password)
    
    def send_email(self, to_emails: List[str], subject: str, 
                   html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Send an email to multiple recipients.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)
            
        Returns:
            True if email sent successfully
        """
        if not self.is_configured():
            logger.warning("Email not configured. Set GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(to_emails)
            
            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, to_emails, msg.as_string())
            
            logger.info(f"Email sent to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_change_alert(self, chemical: Chemical, changes: List[Dict],
                         dashboard_url: str = "http://localhost:8501") -> bool:
        """
        Send an alert about SDS changes for a chemical.
        
        Args:
            chemical: Chemical object
            changes: List of change dictionaries
            dashboard_url: URL to the dashboard
            
        Returns:
            True if alert sent successfully
        """
        if not changes:
            return True
        
        # Determine severity for subject line
        max_severity = "MINOR"
        for change in changes:
            if change.get("severity") == "CRITICAL":
                max_severity = "CRITICAL"
                break
            elif change.get("severity") == "IMPORTANT":
                max_severity = "IMPORTANT"
        
        # Create subject line
        severity_emoji = {
            "CRITICAL": "🚨",
            "IMPORTANT": "⚠️",
            "MINOR": "ℹ️"
        }.get(max_severity, "📋")
        
        subject = f"{severity_emoji} [{max_severity}] SDS Updated: {chemical.chemical_name}"
        
        # Generate email content
        html_content = AlertTemplates.critical_change_html(
            chemical_name=chemical.chemical_name,
            cas_number=chemical.cas_number,
            supplier=chemical.supplier,
            changes=changes,
            dashboard_url=dashboard_url
        )
        
        text_content = AlertTemplates.critical_change_text(
            chemical_name=chemical.chemical_name,
            cas_number=chemical.cas_number,
            supplier=chemical.supplier,
            changes=changes,
            dashboard_url=dashboard_url
        )
        
        # Send to all recipients
        success = self.send_email(
            to_emails=self.recipients if self.recipients else [self.sender_email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        return success
    
    def send_weekly_digest(self, dashboard_url: str = "http://localhost:8501") -> bool:
        """
        Send a weekly digest of all SDS changes.
        
        Args:
            dashboard_url: URL to the dashboard
            
        Returns:
            True if digest sent successfully
        """
        try:
            # Get changes from the last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            changes = db.get_changes_since(week_ago)
            
            if not changes:
                logger.info("No changes in the past week, skipping digest")
                return True
            
            # Aggregate changes by chemical
            chemicals_updated = {}
            critical_count = 0
            important_count = 0
            minor_count = 0
            
            session = db.get_session()
            try:
                for change in changes:
                    chemical = session.query(Chemical).filter(
                        Chemical.id == change.chemical_id
                    ).first()
                    
                    if not chemical:
                        continue
                    
                    # Count by severity
                    if change.severity == "CRITICAL":
                        critical_count += 1
                    elif change.severity == "IMPORTANT":
                        important_count += 1
                    else:
                        minor_count += 1
                    
                    # Track chemicals
                    if chemical.cas_number not in chemicals_updated:
                        chemicals_updated[chemical.cas_number] = {
                            "name": chemical.chemical_name,
                            "cas": chemical.cas_number,
                            "max_severity": change.severity
                        }
                    else:
                        # Update max severity
                        current = chemicals_updated[chemical.cas_number]["max_severity"]
                        if change.severity == "CRITICAL":
                            chemicals_updated[chemical.cas_number]["max_severity"] = "CRITICAL"
                        elif change.severity == "IMPORTANT" and current != "CRITICAL":
                            chemicals_updated[chemical.cas_number]["max_severity"] = "IMPORTANT"
            finally:
                session.close()
            
            # Create digest
            changes_summary = {
                "chemicals_updated": list(chemicals_updated.values()),
                "critical_count": critical_count,
                "important_count": important_count,
                "minor_count": minor_count
            }
            
            week_start = week_ago.strftime("%B %d, %Y")
            week_end = datetime.utcnow().strftime("%B %d, %Y")
            
            html_content = AlertTemplates.weekly_digest_html(
                changes_summary=changes_summary,
                week_start=week_start,
                week_end=week_end,
                dashboard_url=dashboard_url
            )
            
            subject = f"📊 Weekly SDS Digest: {len(chemicals_updated)} chemicals updated"
            
            return self.send_email(
                to_emails=self.recipients if self.recipients else [self.sender_email],
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send weekly digest: {e}")
            return False
    
    def send_test_email(self, to_email: Optional[str] = None) -> bool:
        """
        Send a test email to verify configuration.
        
        Args:
            to_email: Optional specific recipient (defaults to sender)
            
        Returns:
            True if test email sent successfully
        """
        recipient = to_email or self.sender_email
        
        html_content = AlertTemplates.test_email_html()
        subject = "✅ SDS Auto-Updater - Test Email"
        
        return self.send_email(
            to_emails=[recipient],
            subject=subject,
            html_content=html_content
        )


# Global instance
email_service = EmailAlertService()
