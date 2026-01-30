# 🚀 SDS Auto-Updater Deployment Guide

Complete guide for deploying the SDS Auto-Updater to production.

**Target Deployment Date: February 1st, 2026**

---

## 📋 Pre-Deployment Checklist

### 1. System Requirements

- [ ] Python 3.10 or higher installed
- [ ] Chrome browser installed (for web scraping)
- [ ] Minimum 2GB RAM
- [ ] Minimum 5GB free disk space
- [ ] Internet connection for API calls

### 2. API Keys & Credentials

- [ ] Google Gemini API key obtained (https://makersuite.google.com/app/apikey)
- [ ] Gmail App Password created (if using email alerts)
  - Go to Google Account → Security → 2-Step Verification → App Passwords
  - Generate app password for "Mail"
- [ ] Alert recipient email addresses collected

### 3. Environment Configuration

- [ ] `.env` file created with all required keys
- [ ] Email configuration tested
- [ ] API rate limits understood (Gemini: 15 requests/minute free tier)

---

## 🛠️ Installation Steps

### Step 1: Clone and Setup

```bash
# Navigate to project directory
cd "/path/to/Safety Guardian Crew"

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
GOOGLE_API_KEY=your-actual-api-key-here
GEMINI_MODEL=gemini-1.5-flash

# Email Alerts (Recommended)
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
ALERT_RECIPIENTS=safety@company.com,ehs@company.com

# Scraping Configuration
SCRAPE_DELAY_SECONDS=2
MAX_RETRIES=3

# Database & Storage
DATABASE_PATH=data/sds_database.db
SDS_STORAGE_PATH=data/sds_files

# Scheduler
DAILY_CHECK_HOUR=6
WEEKLY_DIGEST_DAY=friday
```

### Step 3: Initialize Database

```bash
# Import your chemical inventory
python main.py --import-csv data/chemicals.csv

# Verify database
python main.py --stats
```

### Step 4: Test Configuration

```bash
# Run health check
python main.py --health-check

# Test email (if configured)
python main.py --test-email

# Test single chemical check
python main.py --check --cas 1310-73-2
```

### Step 5: Create Initial Backup

```bash
# Create database backup
python main.py --backup

# Verify backup created
python main.py --list-backups
```

---

## 🌐 Running the Application

### Option 1: Web Dashboard (Recommended)

```bash
# Start Streamlit dashboard
streamlit run app.py
```

Access at: http://localhost:8501

### Option 2: Command Line

```bash
# Check all chemicals for updates
python main.py --check-all

# Check specific chemical
python main.py --check --cas 7647-01-0

# Show statistics
python main.py --stats
```

### Option 3: Automated Scheduler

```bash
# Start background scheduler (runs daily at configured time)
python main.py --scheduler
```

Keep this running in background or set up as a service (see below).

---

## 🔄 Setting Up Automated Scheduler

### Option A: systemd Service (Linux)

Create service file:

```bash
sudo nano /etc/systemd/system/sds-updater.service
```

Content:

```ini
[Unit]
Description=SDS Auto-Updater Scheduler
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Safety Guardian Crew
Environment="PATH=/path/to/Safety Guardian Crew/venv/bin"
ExecStart=/path/to/Safety Guardian Crew/venv/bin/python main.py --scheduler
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sds-updater
sudo systemctl start sds-updater

# Check status
sudo systemctl status sds-updater

# View logs
sudo journalctl -u sds-updater -f
```

### Option B: macOS LaunchAgent

Create plist file:

```bash
nano ~/Library/LaunchAgents/com.sds-updater.plist
```

Content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sds-updater</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/Safety Guardian Crew/venv/bin/python</string>
        <string>/path/to/Safety Guardian Crew/main.py</string>
        <string>--scheduler</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/Safety Guardian Crew</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.sds-updater.plist
launchctl start com.sds-updater
```

### Option C: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "SDS Auto-Updater"
4. Trigger: Daily at 6:00 AM
5. Action: Start a program
6. Program: `C:\path\to\venv\Scripts\python.exe`
7. Arguments: `main.py --check-all`
8. Start in: `C:\path\to\Safety Guardian Crew`

---

## 🔒 Security Best Practices

### 1. Protect API Keys

```bash
# Set restrictive permissions on .env file
chmod 600 .env

# Add .env to .gitignore (already included)
```

### 2. Database Backups

```bash
# Create daily backup cron job
crontab -e

# Add line (runs backup at 2 AM daily):
0 2 * * * cd /path/to/project && /path/to/venv/bin/python main.py --backup
```

### 3. Log Rotation

Create logrotate config:

```bash
sudo nano /etc/logrotate.d/sds-updater
```

Content:

```
/path/to/Safety Guardian Crew/sds_updater.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 username username
}
```

---

## 📊 Monitoring & Maintenance

### Daily Tasks

- Check dashboard for new changes
- Review critical alerts
- Verify scheduler is running

### Weekly Tasks

- Review weekly digest email
- Check system health page
- Verify backup creation

### Monthly Tasks

- Review and clear old SDS files
- Check disk space usage
- Update chemical inventory if needed
- Review API usage and costs

### Health Monitoring

```bash
# Run health check
python main.py --health-check

# Or use the web dashboard: System Health page
streamlit run app.py
# Navigate to "System Health" in sidebar
```

---

## 🐛 Troubleshooting

### Issue: Web scraping fails

**Solution:**
- Check if Chrome browser is installed
- Update ChromeDriver: `pip install --upgrade selenium webdriver-manager`
- Increase `SCRAPE_DELAY_SECONDS` in `.env`

### Issue: API rate limit exceeded

**Solution:**
- Reduce check frequency
- Upgrade to Gemini Pro (paid tier)
- Batch process chemicals with delays

### Issue: Email not sending

**Solution:**
- Verify Gmail App Password (16 characters, no spaces)
- Check 2-Step Verification is enabled
- Test with: `python main.py --test-email`

### Issue: Database locked error

**Solution:**
- Close all connections to database
- Restart the application
- Check file permissions

### Issue: High memory usage

**Solution:**
- Clear old PDF files from `data/sds_files/`
- Vacuum database: `sqlite3 data/sds_database.db "VACUUM;"`
- Reduce number of chemicals checked simultaneously

---

## 📈 Scaling Considerations

### For 100-500 Chemicals:

- Current setup is sufficient
- Daily checks should complete within 1-2 hours
- Monitor Gemini API usage

### For 500-1000 Chemicals:

- Consider Gemini Pro (paid tier)
- Add multiple API keys for rotation
- Implement parallel processing

### For 1000+ Chemicals:

- Split into multiple instances
- Use dedicated server
- Implement queue-based processing
- Consider commercial SDS management solutions

---

## 🔄 Update Procedure

```bash
# Backup database first
python main.py --backup

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Test health
python main.py --health-check

# Restart service
sudo systemctl restart sds-updater  # Linux
# or
launchctl restart com.sds-updater   # macOS
```

---

## 📞 Support & Resources

### Documentation
- README.md - Project overview
- requirements.txt - Dependencies
- .env.example - Configuration template

### Health Check URLs
- Dashboard: http://localhost:8501
- System Health: http://localhost:8501 (Navigate to "System Health")

### Logs
- Application log: `sds_updater.log`
- Streamlit log: `.streamlit/` directory

### Commands Quick Reference

```bash
# Import chemicals
python main.py --import-csv data/chemicals.csv

# Check all
python main.py --check-all

# Check one
python main.py --check --cas 7647-01-0

# Stats
python main.py --stats

# Health check
python main.py --health-check

# Backup
python main.py --backup

# List backups
python main.py --list-backups

# Start scheduler
python main.py --scheduler

# Web dashboard
streamlit run app.py
```

---

## ✅ Final Pre-Deployment Checklist

- [ ] All dependencies installed
- [ ] `.env` file configured with actual credentials
- [ ] Database initialized with chemical inventory
- [ ] Email configuration tested
- [ ] Health check shows all systems healthy
- [ ] Initial backup created
- [ ] Scheduler configured (service/cron)
- [ ] Monitoring plan established
- [ ] Team trained on dashboard usage
- [ ] Emergency contacts documented

---


For issues or questions, check the logs or run health checks first.
