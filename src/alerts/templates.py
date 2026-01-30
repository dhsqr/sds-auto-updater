"""
Email alert templates for SDS change notifications.
Provides HTML and plain text templates for different alert types.
"""

from typing import List, Dict
from datetime import datetime


class AlertTemplates:
    """Templates for email alerts."""
    
    @staticmethod
    def critical_change_html(chemical_name: str, cas_number: str, supplier: str,
                            changes: List[Dict], dashboard_url: str = "#") -> str:
        """Generate HTML email for critical SDS changes."""
        
        changes_html = ""
        for change in changes:
            severity_color = {
                "CRITICAL": "#dc2626",
                "IMPORTANT": "#d97706", 
                "MINOR": "#16a34a"
            }.get(change.get("severity", "IMPORTANT"), "#6b7280")
            
            changes_html += f"""
            <div style="border-left: 4px solid {severity_color}; padding-left: 16px; margin-bottom: 16px;">
                <p style="font-weight: bold; color: {severity_color}; margin: 0;">
                    [{change.get("severity", "CHANGE")}] {change.get("section", "Unknown Section")}
                </p>
                <p style="margin: 8px 0; color: #374151;">{change.get("summary", "Changes detected")}</p>
                <div style="background: #fef2f2; padding: 12px; border-radius: 4px; font-size: 14px;">
                    <strong>Action Required:</strong> {change.get("action_required", "Review changes")}
                </div>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 20px;">
            🚨 CRITICAL SDS UPDATE
        </h1>
        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">
            Immediate action may be required
        </p>
    </div>
    
    <!-- Chemical Info -->
    <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px 0;"><strong>Chemical:</strong></td>
                <td style="padding: 8px 0;">{chemical_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0;"><strong>CAS Number:</strong></td>
                <td style="padding: 8px 0;">{cas_number}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0;"><strong>Supplier:</strong></td>
                <td style="padding: 8px 0;">{supplier}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0;"><strong>Updated:</strong></td>
                <td style="padding: 8px 0;">{datetime.now().strftime("%B %d, %Y at %I:%M %p")}</td>
            </tr>
        </table>
    </div>
    
    <!-- Changes -->
    <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
        <h2 style="color: #111827; margin-top: 0; font-size: 18px;">Changes Detected</h2>
        {changes_html}
    </div>
    
    <!-- Action Buttons -->
    <div style="padding: 20px; background: #f9fafb; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; text-align: center;">
        <a href="{dashboard_url}" style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500; margin-right: 8px;">
            View Full Comparison
        </a>
        <a href="{dashboard_url}/download" style="display: inline-block; background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500;">
            Download New SDS
        </a>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 16px; color: #6b7280; font-size: 12px;">
        <p style="margin: 0;">This alert was generated automatically by SDS Auto-Updater</p>
        <p style="margin: 4px 0 0 0;">To update your preferences, visit your dashboard settings.</p>
    </div>
    
</body>
</html>
"""
    
    @staticmethod
    def critical_change_text(chemical_name: str, cas_number: str, supplier: str,
                            changes: List[Dict], dashboard_url: str = "#") -> str:
        """Generate plain text email for critical SDS changes."""
        
        changes_text = ""
        for change in changes:
            changes_text += f"""
[{change.get("severity", "CHANGE")}] {change.get("section", "Unknown Section")}
{change.get("summary", "Changes detected")}
Action Required: {change.get("action_required", "Review changes")}
---
"""
        
        return f"""
🚨 CRITICAL SDS UPDATE - Immediate Action Required

Chemical: {chemical_name}
CAS Number: {cas_number}
Supplier: {supplier}
Updated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

========================================
CHANGES DETECTED
========================================
{changes_text}

View full comparison: {dashboard_url}

---
This alert was generated automatically by SDS Auto-Updater
"""
    
    @staticmethod
    def weekly_digest_html(changes_summary: Dict, week_start: str, week_end: str,
                          dashboard_url: str = "#") -> str:
        """Generate HTML email for weekly digest."""
        
        chemicals_updated = changes_summary.get("chemicals_updated", [])
        critical_count = changes_summary.get("critical_count", 0)
        important_count = changes_summary.get("important_count", 0)
        minor_count = changes_summary.get("minor_count", 0)
        
        chemicals_list = ""
        for chem in chemicals_updated:
            severity_badge = {
                "CRITICAL": '<span style="background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">CRITICAL</span>',
                "IMPORTANT": '<span style="background: #d97706; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">IMPORTANT</span>',
                "MINOR": '<span style="background: #16a34a; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">MINOR</span>'
            }.get(chem.get("max_severity", "MINOR"), "")
            
            chemicals_list += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{chem.get("name", "Unknown")}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{chem.get("cas", "N/A")}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{severity_badge}</td>
            </tr>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 20px;">
            📊 Weekly SDS Update Digest
        </h1>
        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">
            {week_start} - {week_end}
        </p>
    </div>
    
    <!-- Summary Stats -->
    <div style="display: flex; background: #f9fafb; border: 1px solid #e5e7eb; border-top: none;">
        <div style="flex: 1; padding: 16px; text-align: center; border-right: 1px solid #e5e7eb;">
            <div style="font-size: 24px; font-weight: bold; color: #dc2626;">{critical_count}</div>
            <div style="font-size: 14px; color: #6b7280;">Critical</div>
        </div>
        <div style="flex: 1; padding: 16px; text-align: center; border-right: 1px solid #e5e7eb;">
            <div style="font-size: 24px; font-weight: bold; color: #d97706;">{important_count}</div>
            <div style="font-size: 14px; color: #6b7280;">Important</div>
        </div>
        <div style="flex: 1; padding: 16px; text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #16a34a;">{minor_count}</div>
            <div style="font-size: 14px; color: #6b7280;">Minor</div>
        </div>
    </div>
    
    <!-- Chemicals List -->
    <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
        <h2 style="color: #111827; margin-top: 0; font-size: 18px;">Updated Chemicals</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f3f4f6;">
                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Chemical</th>
                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">CAS</th>
                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Severity</th>
                </tr>
            </thead>
            <tbody>
                {chemicals_list}
            </tbody>
        </table>
    </div>
    
    <!-- Action Button -->
    <div style="padding: 20px; background: #f9fafb; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; text-align: center;">
        <a href="{dashboard_url}" style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500;">
            View All Updates in Dashboard
        </a>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 16px; color: #6b7280; font-size: 12px;">
        <p style="margin: 0;">This digest was generated automatically by SDS Auto-Updater</p>
    </div>
    
</body>
</html>
"""
    
    @staticmethod
    def test_email_html() -> str:
        """Generate a test email to verify email configuration."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #10b981; padding: 24px; border-radius: 8px; text-align: center;">
        <h1 style="color: white; margin: 0;">✅ Email Configuration Successful!</h1>
    </div>
    <div style="padding: 20px; text-align: center;">
        <p>Your SDS Auto-Updater email alerts are configured correctly.</p>
        <p><strong>Sent at:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>
</body>
</html>
"""
