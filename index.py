from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime, timedelta
import json
import time

# Define selectors for different companies
COMPANY_SELECTORS = {
    'Microsoft': {
        'job_card': 'div.job-card-container',
        'company': 'a.app-aware-link',
        'title': 'h1.ember-view',
        'location': 'li.job-card-container__metadata-item',
        'posted_on': 'span.tvm__text.tvm__text--low-emphasis',
        'employment_type': 'span.job-details-jobs-unified-top-card__job-insight-view-model-secondary',
        'seniority_level': 'div.mt2.mb2'
    },
    'Google': {
        'job_card': 'div.job-card-container',
        'company': 'a.app-aware-link',
        'title': 'h1.ember-view',
        'location': 'span.tvm__text.tvm__text--low-emphasis',
        'posted_on': 'span.tvm__text.tvm__text--low-emphasis',
        'employment_type': 'span.job-card-container__metadata-item',
        'seniority_level': 'div.mt2.mb2'
    },
    'Amazon': {
        'job_card': 'div.job-card-container',
        'company': 'a.app-aware-link',
        'title': 'h1.ember-view',
        'location': 'span.tvm__text.tvm__text--low-emphasis',
        'posted_on': 'div.t-black--light.mt2',
        'employment_type': 'span.job-details-jobs-unified-top-card__job-insight-view-model-secondary',
        'seniority_level': 'div.mt2.mb2'
    }
}

def calculate_posted_date(posted_on):
    """Calculate the posted date based on the posted_on text."""
    today = datetime.now()
    if not posted_on:
        return today.strftime('%d-%m-%Y')
    posted_on = posted_on.lower()
    if 'today' in posted_on:
        return today.strftime('%d-%m-%Y')
    elif 'week' in posted_on:
        days_ago = int(posted_on.split()[1])
        return (today - timedelta(days=days_ago * 7)).strftime('%d-%m-%Y')
    elif 'month' in posted_on:
        days_ago = int(posted_on.split()[1]) * 30
        return (today - timedelta(days=days_ago)).strftime('%d-%m-%Y')
    elif 'year' in posted_on:
        days_ago = int(posted_on.split()[1]) * 365
        return (today - timedelta(days=days_ago)).strftime('%d-%m-%Y')
    return today.strftime('%d-%m-%Y')

def parse_job_posting(job_card, company_name):
    """Extract job data from a job card."""
    selectors = COMPANY_SELECTORS[company_name]
    job_data = {
        "company": job_card.query_selector(selectors['company']).inner_text() if job_card.query_selector(selectors['company']) else None,
        "job_title": job_card.query_selector(selectors['title']).inner_text() if job_card.query_selector(selectors['title']) else None,
        "location": job_card.query_selector(selectors['location']).inner_text() if job_card.query_selector(selectors['location']) else None,
        "posted_on": job_card.query_selector(selectors['posted_on']).inner_text() if job_card.query_selector(selectors['posted_on']) else None,
        "Employment type": job_card.query_selector(selectors['employment_type']).inner_text() if job_card.query_selector(selectors['employment_type']) else None,
        "Seniority level": job_card.query_selector(selectors['seniority_level']).inner_text() if job_card.query_selector(selectors['seniority_level']) else None,
    }
    job_data['posted_date'] = calculate_posted_date(job_data['posted_on'])
    return job_data

def scrape_jobs(url, company_name):
    """Scrape job postings from a given URL and company."""
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(5000)  # Wait for page to load
        
        job_cards = page.query_selector_all(COMPANY_SELECTORS[company_name]['job_card'])
        print(f"Found {len(job_cards)} job cards for {company_name}.")
        
        for job_card in job_cards:
            job = parse_job_posting(job_card, company_name)
            if job:
                jobs.append(job)
        
        browser.close()
    
    return jobs

# Define URLs for different companies
company_urls = {
    'Microsoft': 'https://www.linkedin.com/jobs/search?location=India&geoId=102713980&f_C=1035&position=1&pageNum=0',
    'Google': 'https://www.linkedin.com/jobs/search?location=India&geoId=102713980&f_C=1441',
    'Amazon': 'https://www.linkedin.com/jobs/search?location=India&geoId=102713980&f_TPR=r86400&f_C=1586&position=1&pageNum=0'
}

# Main script to scrape jobs and save results
all_jobs = []
for company, url in company_urls.items():
    print(f"Scraping jobs for {company} from {url}...")
    jobs = scrape_jobs(url, company)
    all_jobs.extend(jobs)
    time.sleep(10)  # Delay to avoid rate limiting

# Save data to JSON and CSV
with open('job-json.json', 'w') as json_file:
    json.dump(all_jobs, json_file, indent=4)

df = pd.DataFrame(all_jobs)
df.to_csv('job-csv.csv', index=False)

print("Data scraping completed and saved to job_list.json and job_list.csv")
