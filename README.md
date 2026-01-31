# 🧪 SDS Auto-Updater

An AI-powered automation system that monitors chemical supplier websites for Safety Data Sheet (SDS) updates, detects changes, and sends intelligent alerts.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)

## 🎯 Problem

Chemical manufacturing companies must maintain up-to-date Safety Data Sheets for compliance:
- Manual checking of 100-500+ suppliers takes **15-20 hours/month**
- Using outdated SDS = compliance violation = **₹5-10L+ fines**
- No automated solution exists for small-medium companies

## ✨ Solution

**SDS Auto-Updater** automatically:
1. 🔍 **Monitors** supplier websites daily for SDS updates
2. 📥 **Downloads** new versions when changes detected
3. 🤖 **Analyzes** changes using AI 
4. 🚨 **Alerts** you with severity-based notifications
5. 📊 **Tracks** all versions in a searchable database

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Chrome browser (for Selenium)
- Google Gemini API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sds-auto-updater.git
cd sds-auto-updater

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` file:

```env
# Required
GOOGLE_API_KEY=your-google-api-key-here

# Email Alerts (optional but recommended)
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
ALERT_RECIPIENTS=ehs@company.com,safety@company.com
```

### Usage

```bash
# Import your chemicals
python main.py --import-csv data/chemicals.csv

# Check all chemicals for updates
python main.py --check-all

# Check a specific chemical
python main.py --check --cas 1310-73-2

# Start the web dashboard
streamlit run app.py

# Start the background scheduler (runs daily at 6 AM)
python main.py --scheduler
```

## 📊 Web Dashboard

Launch with `streamlit run app.py` and open http://localhost:8501

Features:
- **Dashboard** - Overview of chemicals and recent changes
- **Chemicals** - Searchable inventory
- **Changes** - Full change history with severity filters
- **Upload** - Import chemicals from CSV
- **Settings** - Configure email and view stats

## 🏗️ Project Structure

```
sds-auto-updater/
├── app.py                    # Streamlit dashboard
├── main.py                   # CLI entry point
├── requirements.txt
├── .env.example
├── data/
│   ├── sds_files/           # Downloaded PDFs
│   ├── chemicals.csv        # Sample data
│   └── sds_database.db      # SQLite database
└── src/
    ├── config.py            # Configuration
    ├── database.py          # SQLAlchemy models
    ├── pdf_processor.py     # PDF extraction + AI
    ├── change_detector.py   # Change analysis + AI
    ├── scheduler.py         # Daily automation
    ├── scrapers/
    │   ├── base_scraper.py
    │   ├── sigma_aldrich.py
    │   ├── merck.py
    │   └── srl_chemicals.py
    └── alerts/
        ├── email_alerts.py
        └── templates.py
```

## 🔔 Alert Severity Levels

| Level | Trigger | Example |
|-------|---------|---------|
| 🔴 **CRITICAL** | Hazard warnings, PPE changes, storage conditions | "Now requires face shield" |
| 🟡 **IMPORTANT** | First aid, disposal, handling changes | "Updated eye wash procedure" |
| 🟢 **MINOR** | Contact info, formatting | "Supplier phone number changed" |


## 📧 Email Alerts

Receive immediate alerts for critical changes and weekly digests:

```
Subject: 🚨 [CRITICAL] SDS Updated: Sodium Hydroxide

CRITICAL CHANGES DETECTED:
- PPE Requirements: Now requires face shield (previously safety glasses)
- Storage: New temperature limit: Store below 25°C

ACTION REQUIRED:
1. Update PPE protocols
2. Verify storage conditions
```

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

## 📄 License

MIT License - see LICENSE for details.

## ⚠️ Disclaimer

This tool is for educational and efficiency purposes. Always verify SDS information with official supplier sources. Web scraping may violate some supplier Terms of Service.
