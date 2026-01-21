#!/usr/bin/env python3
import os
import json
import requests
import sys
from datetime import datetime, timedelta

MIN_SALARY = int(os.getenv('MIN_SALARY', 4000))
JOB_TITLES = os.getenv('JOB_TITLES', 'software engineer').lower().split(',')
KEYWORDS = os.getenv('KEYWORDS', 'AI').lower().split(',')
REGION = os.getenv('REGION', 'asia').lower()  # Filter by region

# Asia-related location keywords
ASIA_LOCATIONS = [
    'singapore', 'india', 'japan', 'south korea', 'korea', 'thailand',
    'vietnam', 'malaysia', 'indonesia', 'philippines', 'pakistan',
    'bangladesh', 'sri lanka', 'hong kong', 'china', 'taiwan',
    'asia', 'asiapac', 'apac', 'sg', 'jp', 'in', 'th', 'vn', 'my'
]

def clean_text(text):
    """Remove extra whitespace and HTML tags"""
    if not text:
        return ""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove HTML tags if any
    import re
    text = re.sub(r'<[^>]+>', '', text)
    return text

def matches_criteria(job):
    """Check if job matches salary and keyword criteria"""
    title = job.get('title', '').lower()
    description = job.get('description', '').lower() or ""
    company = job.get('company', '').lower()
    text = f"{title} {description} {company}"
    
    # Check title
    title_match = any(jt.strip() in title for jt in JOB_TITLES)
    if not title_match:
        return False
    
    # Check keywords (AI related)
    keyword_match = any(kw.strip() in text for kw in KEYWORDS)
    if not keyword_match:
        return False
    
    # Check salary if available
    salary_str = job.get('salary', '')
    if salary_str and salary_str.lower() != 'not specified':
        try:
            # Try to extract minimum salary
            numbers = [int(s) for s in salary_str.replace('$', '').replace(',', '').split() if s.isdigit()]
            if numbers:
                salary_num = min(numbers)
                # If it looks like annual salary divided by 12
                if salary_num > 100000:
                    salary_num = salary_num / 12
                if salary_num < MIN_SALARY:
                    return False
        except (ValueError, IndexError):
            pass  # If can't parse, include it
    
    return True

def scrape_remoteok():
    """Scrape RemoteOK API (free, no authentication needed)"""
    jobs = []
    try:
        print("🔍 Scraping RemoteOK...")
        response = requests.get('https://remoteok.com/api', timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for job in data:
            if isinstance(job, dict) and matches_criteria(job):
                jobs.append({
                    'title': job.get('title', 'N/A'),
                    'company': job.get('company', 'N/A'),
                    'location': job.get('location', 'Remote'),
                    'url': job.get('url', ''),
                    'description': clean_text(job.get('description', ''))[:300],
                    'source': 'RemoteOK',
                    'salary': job.get('salary', 'Not specified'),
                    'posted_date': job.get('date', '')
                })
        print(f"   Found {len(jobs)} jobs from RemoteOK")
    except Exception as e:
        print(f"⚠️  Error scraping RemoteOK: {e}")
    
    return jobs

def scrape_github_jobs():
    """Scrape GitHub Jobs (free API)"""
    jobs = []
    try:
        print("🔍 Scraping GitHub Jobs...")
        params = {
            'description': 'AI',
            'full_time': 'true',
            'markdown': 'true'
        }
        response = requests.get(
            'https://jobs.github.com/positions.json',
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        for job in data:
            if matches_criteria(job):
                jobs.append({
                    'title': job.get('title', 'N/A'),
                    'company': job.get('company', 'N/A'),
                    'location': job.get('location', 'Remote'),
                    'url': job.get('url', ''),
                    'description': clean_text(job.get('description', ''))[:300],
                    'source': 'GitHub Jobs',
                    'salary': 'Not specified',
                    'posted_date': job.get('created_at', '')
                })
        print(f"   Found {len(jobs)} jobs from GitHub Jobs")
    except Exception as e:
        print(f"⚠️  Error scraping GitHub Jobs: {e}")
    
    return jobs

def scrape_jsonfeed_jobs():
    """Scrape job feeds from JSON endpoints"""
    jobs = []
    try:
        print("🔍 Scraping JSONFeed sources...")
        # Using a free jobs API aggregator
        endpoints = [
            'https://www.thefirehose.dev/jobs.json',  # Tech jobs feed
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                jobs_list = data if isinstance(data, list) else data.get('jobs', [])
                
                for job in jobs_list:
                    if matches_criteria(job):
                        jobs.append({
                            'title': job.get('title', 'N/A'),
                            'company': job.get('company', 'N/A'),
                            'location': job.get('location', 'Remote'),
                            'url': job.get('url', ''),
                            'description': clean_text(job.get('description', ''))[:300],
                            'source': endpoint.split('/')[2],
                            'salary': job.get('salary', 'Not specified'),
                            'posted_date': job.get('posted_date', '')
                        })
            except Exception as e:
                continue
        
        print(f"   Found {len(jobs)} jobs from JSON feeds")
    except Exception as e:
        print(f"⚠️  Error scraping JSON feeds: {e}")
    
    return jobs

def format_email_body(jobs):
    """Format jobs into email body"""
    if not jobs:
        return "No jobs matching your criteria found today."
    
    body = f"# 🎯 Job Opportunities Found!\n\n"
    body += f"Found **{len(jobs)}** matching job(s) on {datetime.now().strftime('%Y-%m-%d')}\n\n"
    body += "---\n\n"
    
    for idx, job in enumerate(jobs, 1):
        body += f"## {idx}. {job['title']}\n"
        body += f"**Company:** {job['company']}\n"
        body += f"**Location:** {job['location']}\n"
        body += f"**Salary:** {job['salary']}\n"
        body += f"**Source:** {job['source']}\n"
        if job.get('posted_date'):
            body += f"**Posted:** {job['posted_date']}\n"
        body += f"**Description:** {job['description']}...\n"
        body += f"**Link:** {job['url']}\n\n"
        body += "---\n\n"
    
    return body

def format_email_body_html(jobs):
    """Format jobs into HTML email body"""
    if not jobs:
        return "<p>No jobs matching your criteria found today.</p>"
    
    html = f"<h1>🎯 Job Opportunities Found!</h1>\n"
    html += f"<p>Found <strong>{len(jobs)}</strong> matching job(s) on {datetime.now().strftime('%Y-%m-%d')}</p>\n"
    html += "<hr>\n"
    
    for idx, job in enumerate(jobs, 1):
        html += f"<h2>{idx}. {job['title']}</h2>\n"
        html += f"<p><strong>Company:</strong> {job['company']}</p>\n"
        html += f"<p><strong>Location:</strong> {job['location']}</p>\n"
        html += f"<p><strong>Salary:</strong> {job['salary']}</p>\n"
        html += f"<p><strong>Source:</strong> {job['source']}</p>\n"
        if job.get('posted_date'):
            html += f"<p><strong>Posted:</strong> {job['posted_date']}</p>\n"
        html += f"<p><strong>Description:</strong> {job['description']}...</p>\n"
        html += f"<p><a href='{job['url']}'>View Full Job</a></p>\n"
        html += "<hr>\n"
    
    return html

def main():
    print("🤖 Starting job scraper...")
    print(f"   Min Salary: ${MIN_SALARY}/month")
    print(f"   Job Titles: {', '.join(JOB_TITLES)}")
    print(f"   Keywords: {', '.join(KEYWORDS)}\n")
    
    # Scrape from multiple sources
    all_jobs = []
    all_jobs.extend(scrape_remoteok())
    all_jobs.extend(scrape_github_jobs())
    all_jobs.extend(scrape_jsonfeed_jobs())
    
    # Remove duplicates by URL
    unique_jobs = {job['url']: job for job in all_jobs if job['url']}.values()
    unique_jobs = list(unique_jobs)
    
    print(f"\n✅ Found {len(unique_jobs)} unique matching job(s)\n")
    
    if unique_jobs:
        email_body = format_email_body(unique_jobs)
        email_body_html = format_email_body_html(unique_jobs)
        
        # Save to file for debugging
        with open('jobs_found.json', 'w') as f:
            json.dump(unique_jobs, f, indent=2)
        
        # Output for GitHub Actions
        # Use GitHub Actions output format
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write(f"found_jobs=true\n")
            # Write multiline output
            f.write(f"email_body<<EOF\n{email_body}\nEOF\n")
            f.write(f"email_body_html<<EOF\n{email_body_html}\nEOF\n")
        
        # Also print for debugging
        print("📧 Email body:")
        print(email_body)
    else:
        print("😴 No matching jobs found today.")
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write(f"found_jobs=false\n")

if __name__ == '__main__':
    main()
