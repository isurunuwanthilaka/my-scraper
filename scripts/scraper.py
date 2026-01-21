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
    """Check if job matches salary, keyword, and location criteria"""
    title = job.get('title', '').lower()
    description = job.get('description', '').lower() or ""
    company = job.get('company', '').lower()
    location = job.get('location', '').lower()
    text = f"{title} {description} {company} {location}"
    
    # Check title
    title_match = any(jt.strip() in title for jt in JOB_TITLES)
    if not title_match:
        return False
    
    # Check keywords (AI related)
    keyword_match = any(kw.strip() in text for kw in KEYWORDS)
    if not keyword_match:
        return False
    
    # Check location (Asia only)
    if REGION.lower() == 'asia':
        location_match = any(loc in location for loc in ASIA_LOCATIONS)
        if not location_match:
            # Also check if location says "remote" without specifying region
            # In that case, skip it as we can't confirm it's Asia
            if 'remote' in location and not any(loc in location for loc in ASIA_LOCATIONS):
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

def scrape_linkedin_api():
    """Scrape LinkedIn jobs using free API options"""
    jobs = []
    try:
        print("🔍 Checking LinkedIn Jobs (via RapidAPI)...")
        
        api_key = os.getenv('RAPIDAPI_KEY')
        if not api_key:
            print("   ⚠️  RAPIDAPI_KEY not set - skipping LinkedIn")
            print("      (Optional: Get free key at https://rapidapi.com/laimoon-laimoon-rest-api/api/jsearch)")
            return jobs
        
        # Using JSearch API from RapidAPI
        job_title = ' '.join(JOB_TITLES).strip()
        
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'jsearch.p.rapidapi.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = 'https://jsearch.p.rapidapi.com/search'
        
        # Search with different location filters
        locations = ['Singapore', 'India', 'Tokyo', 'Bangkok', 'Manila', 'Hanoi']
        
        for location in locations:
            try:
                params = {
                    'query': f'{job_title} AI Machine Learning',
                    'location': location,
                    'page': '1',
                    'num_pages': '1'
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for job in data.get('data', []):
                        try:
                            job_data = {
                                'title': job.get('job_title', ''),
                                'company': job.get('employer_name', ''),
                                'description': job.get('job_description', ''),
                                'location': f"{job.get('job_city', '')}, {job.get('job_country', '')}",
                                'salary': ''
                            }
                            
                            if matches_criteria(job_data):
                                jobs.append({
                                    'title': job.get('job_title', 'N/A'),
                                    'company': job.get('employer_name', 'N/A'),
                                    'location': f"{job.get('job_city', 'Remote')}, {job.get('job_country', '')}",
                                    'url': job.get('job_apply_link', f"https://linkedin.com/jobs/view/{job.get('job_id', '')}"),
                                    'description': clean_text(job.get('job_description', ''))[:300],
                                    'source': 'LinkedIn (JSearch API)',
                                    'salary': job.get('job_salary_min', 'Not specified'),
                                    'posted_date': job.get('job_posted_at_datetime_utc', '')
                                })
                        except Exception as job_err:
                            continue
                        
            except requests.exceptions.Timeout:
                print(f"   ⏱️  Timeout for {location}")
                continue
            except Exception as e:
                print(f"   ⚠️  Error for {location}: {str(e)[:50]}")
                continue
        
        print(f"   Found {len(jobs)} jobs from LinkedIn")
    except Exception as e:
        print(f"⚠️  Error scraping LinkedIn: {e}")
    
    return jobs

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

def scrape_workingnomads():
    """Scrape Working Nomads job board"""
    jobs = []
    try:
        print("🔍 Scraping Working Nomads...")
        # Using proper endpoint with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.workingnomads.co/api/jobs', headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for job in data:
            if isinstance(job, dict) and matches_criteria(job):
                jobs.append({
                    'title': job.get('title', 'N/A'),
                    'company': job.get('company_name', 'N/A'),
                    'location': job.get('location', 'Remote'),
                    'url': job.get('url', ''),
                    'description': clean_text(job.get('description', ''))[:300],
                    'source': 'Working Nomads',
                    'salary': 'Not specified',
                    'posted_date': job.get('pub_date', '')
                })
        print(f"   Found {len(jobs)} jobs from Working Nomads")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"   ⚠️  Working Nomads blocked (403) - trying alternative")
        else:
            print(f"⚠️  Error scraping Working Nomads: {e}")
    except Exception as e:
        print(f"⚠️  Error scraping Working Nomads: {e}")
    
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
    print(f"   Keywords: {', '.join(KEYWORDS)}")
    print(f"   Region: {REGION.upper()}\n")
    
    # Scrape from multiple sources (LinkedIn prioritized if API key available)
    all_jobs = []
    all_jobs.extend(scrape_linkedin_api())  # LinkedIn (optional - requires API key)
    all_jobs.extend(scrape_remoteok())      # Always available
    all_jobs.extend(scrape_workingnomads()) # Backup source
    
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
