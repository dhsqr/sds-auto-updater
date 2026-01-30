"""
Configuration management for SDS Auto-Updater.
Loads environment variables and provides centralized config access.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SDS_STORAGE_PATH = Path(os.getenv("SDS_STORAGE_PATH", DATA_DIR / "sds_files"))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", DATA_DIR / "sds_database.db"))

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SDS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Email Configuration
GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
ALERT_RECIPIENTS = [
    email.strip() 
    for email in os.getenv("ALERT_RECIPIENTS", "").split(",") 
    if email.strip()
]

# Scraping Configuration
SCRAPE_DELAY_SECONDS = int(os.getenv("SCRAPE_DELAY_SECONDS", "2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Scheduler Configuration
DAILY_CHECK_HOUR = int(os.getenv("DAILY_CHECK_HOUR", "6"))  # 6 AM
WEEKLY_DIGEST_DAY = os.getenv("WEEKLY_DIGEST_DAY", "friday")

# Severity Thresholds
SEVERITY_LEVELS = {
    "CRITICAL": 3,  # Highest priority
    "IMPORTANT": 2,
    "MINOR": 1
}

# Sections to extract from SDS
SDS_SECTIONS = [
    "hazard_statements",
    "ppe_requirements", 
    "first_aid_measures",
    "storage_conditions",
    "disposal_requirements",
    "handling_precautions"
]

# Supplier configurations
SUPPLIERS = {
    "sigma_aldrich": {
        "name": "Sigma-Aldrich",
        "base_url": "https://www.sigmaaldrich.com",
        "requires_selenium": True
    },
    "merck": {
        "name": "Merck",
        "base_url": "https://www.merckmillipore.com",
        "requires_selenium": True
    },
    "srl_chemicals": {
        "name": "SRL Chemicals",
        "base_url": "https://www.srlchem.com",
        "requires_selenium": False
    }
}


def validate_config():
    """Validate that required configuration is present."""
    import sys

    errors = []
    warnings = []

    # Critical requirements
    if not GOOGLE_API_KEY:
        errors.append("❌ GOOGLE_API_KEY is not set (REQUIRED for AI features)")
    elif len(GOOGLE_API_KEY) < 20:
        errors.append("❌ GOOGLE_API_KEY appears invalid (too short)")

    # Optional but recommended
    if not GMAIL_SENDER_EMAIL or not GMAIL_APP_PASSWORD:
        warnings.append("⚠️  Email alerts not configured (optional)")

    if not ALERT_RECIPIENTS:
        warnings.append("⚠️  No alert recipients configured")

    # Path validations
    if not DATA_DIR.exists():
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created data directory: {DATA_DIR}")
        except Exception as e:
            errors.append(f"❌ Cannot create data directory: {e}")

    if not SDS_STORAGE_PATH.exists():
        try:
            SDS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created SDS storage directory: {SDS_STORAGE_PATH}")
        except Exception as e:
            errors.append(f"❌ Cannot create SDS storage directory: {e}")

    # Print results
    if errors:
        print("\n🔴 Configuration Errors:")
        for error in errors:
            print(f"  {error}")
        print("\n💡 Please check your .env file and fix the errors above.")
        return False

    if warnings:
        print("\n🟡 Configuration Warnings:")
        for warning in warnings:
            print(f"  {warning}")

    if not errors and not warnings:
        print("✅ Configuration validated successfully")

    return len(errors) == 0


def get_supplier_config(supplier_key: str) -> dict:
    """Get configuration for a specific supplier."""
    return SUPPLIERS.get(supplier_key, {})
