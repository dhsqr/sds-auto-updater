"""
Simulate a supplier SDS update and trigger email notification.
Run this script to test the email notification system.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import db, Chemical
from src.alerts.email_alerts import email_service

def simulate_sds_change():
    """Simulate an SDS change for a chemical and send notification."""
    
    # First, reload chemicals from CSV to get the new ones
    print("📥 Reloading chemicals from CSV...")
    count = db.import_chemicals_from_csv("data/chemicals.csv")
    print(f"   Imported {count} new chemicals")
    
    # Get a chemical to simulate a change
    session = db.get_session()
    try:
        chemical = session.query(Chemical).filter(
            Chemical.chemical_name == "Sodium Hydroxide"
        ).first()
        
        if not chemical:
            print("❌ Chemical not found")
            return False
        
        print(f"\n🧪 Simulating SDS update for: {chemical.chemical_name}")
        print(f"   CAS Number: {chemical.cas_number}")
        print(f"   Supplier: {chemical.supplier}")
        
        # Create a simulated change
        simulated_changes = [
            {
                "section": "hazard_statements",
                "severity": "IMPORTANT",
                "summary": "Updated hazard classification: Added H314 (Causes severe skin burns and eye damage)",
                "action_required": "Update PPE requirements for handling procedures"
            },
            {
                "section": "ppe_requirements",
                "severity": "CRITICAL",
                "summary": "PPE change: Face shield now required in addition to safety goggles",
                "action_required": "Ensure all lab personnel have access to face shields"
            }
        ]
        
        # Add change to database
        print("\n📝 Recording change in database...")
        change_id = db.add_change(
            chemical_id=chemical.id,
            old_version_id=None,
            new_version_id=None,
            severity="CRITICAL",
            section="ppe_requirements",
            old_value="Safety goggles, chemical resistant gloves, lab coat",
            new_value="Face shield AND safety goggles, chemical resistant gloves, lab coat",
            ai_summary="PPE requirements updated: Face shield now mandatory in addition to safety goggles due to updated hazard classification"
        )
        print(f"   Change recorded with ID: {change_id}")
        
        # Send the email notification
        print("\n📧 Sending email notification...")
        success = email_service.send_change_alert(chemical, simulated_changes)
        
        if success:
            print("✅ Email notification sent successfully!")
            return True
        else:
            print("❌ Failed to send email notification")
            return False
            
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("SDS Change Simulation Script")
    print("=" * 60)
    
    if email_service.is_configured():
        print(f"✅ Email configured: {email_service.sender_email}")
        print(f"   Recipients: {email_service.recipients}")
    else:
        print("❌ Email not configured! Check your .env file")
        sys.exit(1)
    
    print()
    simulate_sds_change()
    print()
    print("=" * 60)
    print("Check your inbox for the change notification!")
    print("=" * 60)
