# ✅ Pre-Deployment Checklist for February 1st, 2026

Use this checklist to ensure everything is ready before deploying to production.

---

## 📅 Timeline

**Target Date**: February 1st, 2026
**Recommended Start**: January 29th, 2026 (2 days before)

---

## 🔍 Day 1: Testing & Validation (January 29th)

### Morning: System Tests

- [ ] Run automated test suite
  ```bash
  python test_deployment.py
  ```
  **Expected**: 7/7 tests pass

- [ ] Run health check
  ```bash
  python main.py --health-check
  ```
  **Expected**: Overall status "healthy" or "degraded"

- [ ] Verify database
  ```bash
  python main.py --stats
  ```
  **Expected**: Shows correct number of chemicals

- [ ] Test CSV import with sample data
  ```bash
  python main.py --import-csv data/chemicals.csv
  ```
  **Expected**: Imports successfully (or reports existing entries)

### Afternoon: Configuration

- [ ] Verify `.env` file has production credentials
  - [ ] `GOOGLE_API_KEY` is set and valid
  - [ ] `GEMINI_MODEL` is correct (gemini-1.5-flash)
  - [ ] `GMAIL_SENDER_EMAIL` configured (if using email)
  - [ ] `GMAIL_APP_PASSWORD` configured (if using email)
  - [ ] `ALERT_RECIPIENTS` has correct email addresses
  - [ ] `DAILY_CHECK_HOUR` set to desired time (default: 6 AM)

- [ ] Test email configuration (if configured)
  ```bash
  python main.py --test-email
  ```
  **Expected**: Test email received

- [ ] Create initial backup
  ```bash
  python main.py --backup
  ```
  **Expected**: Backup file created in data/backups/

### Evening: Documentation Review

- [ ] Read `QUICKSTART.md`
- [ ] Read `DEPLOYMENT.md`
- [ ] Review `IMPROVEMENTS_SUMMARY.md`
- [ ] Bookmark important commands

---

## 🛠️ Day 2: Installation & Setup (January 30th)

### Morning: Server Setup

- [ ] Production server/machine identified
- [ ] Python 3.10+ installed
  ```bash
  python3 --version
  ```
  **Expected**: 3.10.0 or higher

- [ ] Chrome browser installed (for Selenium)
  ```bash
  google-chrome --version  # Linux
  # or check manually on Mac/Windows
  ```

- [ ] Sufficient disk space available
  ```bash
  df -h
  ```
  **Expected**: At least 5GB free

- [ ] Project files copied to production location

### Afternoon: Environment Setup

- [ ] Virtual environment created
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] Dependencies installed
  ```bash
  pip install -r requirements.txt
  ```
  **Expected**: All packages install without errors

- [ ] `.env` file configured with production values

- [ ] Database initialized
  ```bash
  python main.py --import-csv data/your_chemicals.csv
  ```

- [ ] Initial backup created
  ```bash
  python main.py --backup
  ```

### Evening: Scheduler Configuration

Choose ONE of the following:

#### Option A: systemd (Linux)
- [ ] Service file created in `/etc/systemd/system/sds-updater.service`
- [ ] Service enabled: `sudo systemctl enable sds-updater`
- [ ] Service started: `sudo systemctl start sds-updater`
- [ ] Service status checked: `sudo systemctl status sds-updater`

#### Option B: cron (Linux/Mac)
- [ ] Crontab entry added: `crontab -e`
- [ ] Daily check scheduled (e.g., `0 6 * * * cd /path && ./venv/bin/python main.py --check-all`)
- [ ] Backup cron added (e.g., `0 2 * * * cd /path && ./venv/bin/python main.py --backup`)

#### Option C: Task Scheduler (Windows)
- [ ] Task created in Task Scheduler
- [ ] Daily trigger configured
- [ ] Task tested manually

---

## 🚀 Deployment Day: February 1st, 2026

### Early Morning (Before 6 AM)

- [ ] **6:00 AM - 7:00 AM**: Final system check
  ```bash
  python main.py --health-check
  ```
  **Expected**: All systems healthy

- [ ] Create pre-launch backup
  ```bash
  python main.py --backup --description pre_launch
  ```

- [ ] Verify scheduler is running
  ```bash
  # Linux systemd
  sudo systemctl status sds-updater

  # Or check logs
  tail -f sds_updater.log
  ```

- [ ] Test manual chemical check
  ```bash
  python main.py --check --cas 1310-73-2
  ```
  **Expected**: Completes successfully

### Morning (9 AM - 12 PM)

- [ ] Launch web dashboard
  ```bash
  streamlit run app.py
  ```
  **Expected**: Opens at http://localhost:8501

- [ ] Verify dashboard pages load:
  - [ ] Dashboard page
  - [ ] Chemicals page
  - [ ] Changes page
  - [ ] Upload page
  - [ ] Settings page
  - [ ] System Health page

- [ ] Test manual check from dashboard
  - [ ] Click "Run Manual Check"
  - [ ] Observe any errors or warnings

- [ ] Review initial statistics
  - [ ] Number of chemicals tracked
  - [ ] SDS versions in database
  - [ ] Any pending changes

### Afternoon (1 PM - 5 PM)

- [ ] Monitor first automated check (if scheduled)
  ```bash
  tail -f sds_updater.log
  ```

- [ ] Review any alerts generated
  - [ ] Check email inbox (if configured)
  - [ ] Review Changes page in dashboard

- [ ] Verify email alerts (if changes detected)
  - [ ] Alert email received
  - [ ] Correct severity level
  - [ ] Actionable information included

- [ ] Check system resources
  - [ ] CPU usage normal
  - [ ] Memory usage acceptable
  - [ ] Disk space sufficient

### End of Day (5 PM - 6 PM)

- [ ] Create end-of-day backup
  ```bash
  python main.py --backup --description end_of_day_1
  ```

- [ ] Review logs for errors
  ```bash
  cat sds_updater.log | grep ERROR
  ```

- [ ] Document any issues encountered

- [ ] Update team on deployment status

---

## 📊 Success Criteria

### ✅ System is considered successfully deployed if:

1. **Health Check**: All systems show "healthy" or "degraded"
2. **Automated Checks**: Scheduler runs checks automatically
3. **Dashboard**: Web interface accessible and functional
4. **Alerts**: Email alerts sent for changes (if configured)
5. **No Critical Errors**: No ERROR level logs in application
6. **Backups**: Automatic backups being created
7. **Resources**: System resources within normal range

### ⚠️ Issues to watch for:

- API rate limit errors (too many Gemini calls)
- Web scraping failures (supplier website changes)
- Email delivery failures
- Disk space warnings
- High memory/CPU usage
- Database connection errors

---

## 🆘 Emergency Procedures

### If something goes wrong:

1. **Stop the scheduler immediately**
   ```bash
   # systemd
   sudo systemctl stop sds-updater

   # Or kill process
   ps aux | grep "python main.py"
   kill <PID>
   ```

2. **Check logs for errors**
   ```bash
   tail -100 sds_updater.log
   ```

3. **Run health check**
   ```bash
   python main.py --health-check
   ```

4. **Restore from backup if needed**
   ```bash
   python main.py --list-backups
   python main.py --restore-backup <backup_file>
   ```

5. **Contact support/review documentation**
   - Check `DEPLOYMENT.md` Troubleshooting section
   - Review logs for specific error messages
   - Verify configuration in `.env`

---

## 📞 Post-Deployment Tasks (Week 1)

### Daily (Days 2-7)

- [ ] Check dashboard for new changes
- [ ] Review critical alerts
- [ ] Monitor system health page
- [ ] Verify scheduler is running

### End of Week 1

- [ ] Review weekly digest email
- [ ] Check all backups created successfully
- [ ] Review overall system performance
- [ ] Document any issues or improvements needed
- [ ] Train team on using the system

---

## 📝 Notes Section

Use this space for deployment-specific notes:

### Issues Encountered:
```
[Document any issues and their resolutions]
```

### Configuration Changes:
```
[Note any changes made to default config]
```

### Team Feedback:
```
[Collect feedback from users]
```

---

## ✨ Congratulations!

Once all items are checked off, your SDS Auto-Updater is successfully deployed!

**Remember**:
- Check System Health page weekly
- Review weekly digest emails
- Keep backups for at least 30 days
- Monitor API usage to avoid rate limits
- Update chemical inventory as needed

---

**Deployment Date**: _____________

**Deployed By**: _____________

**Sign-off**: _____________
