# ⚡ Quick Start Guide

Get the SDS Auto-Updater running in 5 minutes!

## 🎯 Prerequisites

✅ Python 3.10+ installed
✅ Chrome browser installed
✅ Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Installation (3 steps)

### 1. Install Dependencies

```bash
cd "/path/to/Safety Guardian Crew"
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `.env` file and add your Gemini API key:

```env
GOOGLE_API_KEY=your-api-key-here
```

### 3. Initialize Database

```bash
# Import sample chemicals
python main.py --import-csv data/chemicals.csv

# Verify setup
python main.py --stats
```

## 🎨 Launch Dashboard

```bash
streamlit run app.py
```

Open browser to: **http://localhost:8501**

## 🧪 Test the System

### Check Health

```bash
python main.py --health-check
```

Expected output:
```
✅ Overall Status: HEALTHY
✅ Database: healthy
✅ Storage: healthy
⚠️  API Configuration: degraded (email not configured - optional)
✅ System Resources: healthy
```

### Test Single Chemical

```bash
python main.py --check --cas 1310-73-2
```

### Create Backup

```bash
python main.py --backup
```

## 📧 Optional: Email Alerts

To enable email alerts:

1. Enable 2-Step Verification on your Gmail account
2. Generate App Password: [Google Account → Security → App Passwords](https://myaccount.google.com/apppasswords)
3. Add to `.env`:

```env
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
ALERT_RECIPIENTS=safety@company.com
```

4. Test:

```bash
python main.py --test-email
```

## 🎓 Next Steps

1. **Add your chemicals**: Use the Upload page in dashboard or CSV import
2. **Set up automation**: See `DEPLOYMENT.md` for scheduler setup
3. **Monitor changes**: Check the Changes page regularly
4. **System health**: Visit System Health page weekly

## 📚 Key Commands

```bash
# Import chemicals from CSV
python main.py --import-csv your_file.csv

# Check all chemicals
python main.py --check-all

# Check specific chemical
python main.py --check --cas 7647-01-0

# Show statistics
python main.py --stats

# Health check
python main.py --health-check

# Create backup
python main.py --backup

# Start scheduler (runs daily)
python main.py --scheduler

# Launch web dashboard
streamlit run app.py
```

## ⚠️ Common Issues

### "ModuleNotFoundError"
→ Make sure virtual environment is activated: `source venv/bin/activate`

### "Database not found"
→ Run: `python main.py --import-csv data/chemicals.csv`

### "API key invalid"
→ Check `.env` file has correct `GOOGLE_API_KEY`

### "Chrome driver not found"
→ Run: `pip install --upgrade selenium webdriver-manager`

## 🆘 Get Help

- Check `README.md` for detailed information

- Review logs in `sds_updater.log`
- Run health check: `python main.py --health-check`


