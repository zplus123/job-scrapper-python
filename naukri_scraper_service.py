from fastapi import FastAPI
from bs4 import BeautifulSoup
import requests

app = FastAPI()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

@app.get("/scrape/")
def scrape_data(keyword: str):
    try:
        all_jobs = []

        # --- Naukri ---
        naukri_jobs = []
        naukri_url = f"https://www.naukri.com/{keyword.replace(' ', '-').lower()}-jobs?k={keyword.replace(' ', '%20')}"
        r = requests.get(naukri_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for job in soup.select('.srp-jobtuple-wrapper, .jobTuple.bgWhite.br4.mb-8'):
            title_tag = job.select_one('a.title, a.title.fw500.ellipsis')
            company_tag = job.select_one('a.comp-name, a.compName')
            location_tag = job.select_one('span.locWdth, span.fleft.grey-text.br2.placeHolderLi.location')
            exp_tag = job.select_one('span.expwdth, li.experience')
            apply_link = title_tag['href'] if title_tag and title_tag.has_attr('href') else ''
            naukri_jobs.append({
                'jobTitle': title_tag.text.strip() if title_tag else '',
                'company': company_tag.text.strip() if company_tag else '',
                'location': location_tag.text.strip() if location_tag else '',
                'experience': exp_tag.text.strip() if exp_tag else '',
                'applyLink': apply_link,
                'platform': 'Naukri'
            })
        all_jobs.extend(naukri_jobs)

        # --- Glassdoor ---
        glassdoor_jobs = []
        glassdoor_url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={keyword.replace(' ', '%20')}"
        r = requests.get(glassdoor_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for job in soup.select('li[data-test="jobListing"]'):
            title_tag = job.select_one('a.JobCard_jobTitle__GLyJ1[data-test="job-title"]')
            company_tag = job.select_one('span.EmployerProfile_compactEmployerName__9MGcV')
            location_tag = job.select_one('div.JobCard_location__Ds1fM[data-test="emp-location"]')
            glassdoor_jobs.append({
                'jobTitle': title_tag.text.strip() if title_tag else '',
                'company': company_tag.text.strip() if company_tag else '',
                'location': location_tag.text.strip() if location_tag else '',
                'experience': '',
                'applyLink': title_tag['href'] if title_tag and title_tag.has_attr('href') else '',
                'platform': 'Glassdoor'
            })
        all_jobs.extend(glassdoor_jobs)

        # --- Foundit ---
        foundit_jobs = []
        foundit_url = f"https://www.foundit.in/srp/results?query={keyword.replace(' ', '%20')}"
        r = requests.get(foundit_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for job in soup.select('div.cardContainer'):
            title_tag = job.select_one('div.jobTitle')
            company_tag = job.select_one('div.companyName')
            location_tag = job.select_one('div.details.location')
            exp_tag = job.select_one('div.experienceSalary')

            job_desc_link = ''
            link_tag = job.select_one('a[href]')
            if link_tag:
                job_desc_link = link_tag['href']
                if job_desc_link.startswith('/'):
                    job_desc_link = 'https://www.foundit.in' + job_desc_link

            foundit_jobs.append({
                'jobTitle': title_tag.text.strip() if title_tag else '',
                'company': company_tag.text.strip() if company_tag else '',
                'location': location_tag.text.strip() if location_tag else '',
                'experience': exp_tag.text.strip() if exp_tag else '',
                'applyLink': job_desc_link,
                'platform': 'Foundit'
            })
        all_jobs.extend(foundit_jobs)

        # --- LinkedIn (⚠️ requires login; scraping limited) ---
        linkedin_jobs = []
        linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}"
        r = requests.get(linkedin_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for job in soup.select('div.base-card, li.jobs-search-results__list-item'):
            title_tag = job.select_one('h3')
            company_tag = job.select_one('h4')
            location_tag = job.select_one('span.job-search-card__location')
            link_tag = job.select_one('a[href]')
            linkedin_jobs.append({
                'jobTitle': title_tag.text.strip() if title_tag else '',
                'company': company_tag.text.strip() if company_tag else '',
                'location': location_tag.text.strip() if location_tag else '',
                'experience': '',
                'applyLink': link_tag['href'] if link_tag else '',
                'platform': 'LinkedIn'
            })
        all_jobs.extend(linkedin_jobs)

        return all_jobs

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
