# Job Scraper GitHub Actions Setup

## Overview
This GitHub Actions workflow automatically scrapes job listings for AI-related Software Engineer roles with salary >$4000/month and sends you notifications.

**Cost: Completely FREE** ✅
- GitHub Actions: Free 2000 minutes/month for public repos
- Job APIs: All free endpoints
- Email: Gmail SMTP free tier

## Setup Instructions

### 1. Add GitHub Secrets
Go to your repository → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:
- `EMAIL_USERNAME`: Your Gmail address (e.g., yourname@gmail.com)
- `EMAIL_PASSWORD`: Gmail app-specific password (see below)
- `EMAIL_TO`: Recipient email address

#### How to get Gmail app-specific password:
1. Enable 2-Factor Authentication on your Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer" (or any device)
4. Copy the generated 16-character password
5. Use this as `EMAIL_PASSWORD` secret

### 2. Alternative: GitHub Issues Notification
The workflow also creates GitHub Issues automatically when jobs are found.
- No setup needed! Issues will appear in your repo
- Enable Notifications for your repo to get notified

### 3. Manual Trigger
To test the workflow immediately:
1. Go to **Actions** tab in your repo
2. Select "Job Scraper & Notifier" workflow
3. Click **Run workflow**

### 4. Customize Search Criteria
Edit `.github/workflows/job-scraper.yml`:

```yaml
env:
  MIN_SALARY: 4000           # Change to your minimum salary (USD/month)
  JOB_TITLES: "software engineer,senior software engineer"  # Job titles to search
  KEYWORDS: "AI,artificial intelligence,machine learning"   # Keywords to include
```

## Features

✅ **Multiple Job Sources:**
- RemoteOK (free API)
- GitHub Jobs (free API)
- JSONFeed aggregators

✅ **Smart Filtering:**
- Job title matching (Software Engineer, Senior Software Engineer)
- Salary threshold ($4000+ USD/month)
- AI/ML keyword filtering
- Duplicate removal

✅ **Notifications:**
- 📧 Email via Gmail SMTP (free)
- 🐙 GitHub Issues (free, automatic)
- 📦 Artifact storage (7 days)

✅ **Scheduling:**
- Runs every weekday at 9 AM UTC
- Manual trigger available
- Completely free

## Workflow Schedule

Default: **Monday-Friday at 9:00 AM UTC**

To change the schedule, edit the cron expression in `.github/workflows/job-scraper.yml`:
```yaml
schedule:
  - cron: '0 9 * * MON-FRI'  # Format: minute hour day month weekday
```

Common examples:
- `0 9 * * *` → Daily at 9 AM
- `0 9 * * MON,WED,FRI` → Mon/Wed/Fri at 9 AM
- `*/2 * * * *` → Every 2 hours

## Files Explained

- `.github/workflows/job-scraper.yml` - GitHub Actions workflow definition
- `scripts/scraper.py` - Python scraper script
- `requirements.txt` - Python dependencies
- `jobs_found.json` - Results artifact (saved for 7 days)

## Troubleshooting

### Email not received
1. Check "Spam" folder in Gmail
2. Verify `EMAIL_USERNAME` and `EMAIL_PASSWORD` are correct
3. Ensure you're using an app-specific password (not your main Gmail password)
4. Check workflow logs in Actions tab for errors

### No jobs found
1. Check if job sites are up (test manually)
2. Verify filtering criteria are not too strict
3. Check the artifact `jobs_found.json` for details
4. Review workflow logs for errors

### Workflow not running
1. Check repository is public (required for free tier)
2. Verify GitHub Actions is enabled in Settings
3. Check workflow syntax in `.github/workflows/job-scraper.yml`

## Advanced: Customize Further

### Add more job sources
Edit `scripts/scraper.py` and add new scraping functions:
```python
def scrape_custom_api():
    # Add your own API here
    pass

# Then call it in main()
all_jobs.extend(scrape_custom_api())
```

### Add Slack/Discord notification
Install action in workflow:
```yaml
- name: Send Slack notification
  uses: 8398a7/action-slack@v3
  with:
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    text: 'New jobs found!'
```

### Filter by timezone
Modify the cron expression or add timezone-aware filtering in Python.

## License & Attribution

This uses:
- RemoteOK API (free)
- GitHub Jobs API (free)
- GitHub Actions (free tier)
- Gmail SMTP (free tier)

No API keys or premium services required! 🎉
