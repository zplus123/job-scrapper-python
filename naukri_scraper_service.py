from fastapi import FastAPI
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time

app = FastAPI()

@app.get("/scrape/")
def scrape_data(keyword: str):
    try:
        # Always initialize all job lists to avoid NameError
        naukri_jobs = []
        glassdoor_jobs = []
        foundit_jobs = []
        linkedin_jobs = []

        options = uc.ChromeOptions()
        # options.add_argument('--headless')  # Uncomment for headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')

        # Explicitly specify ChromeDriver version 138 to match Chrome browser version
        driver = uc.Chrome(options=options, version_main=138)

        # --- Naukri Scraping ---
        naukri_url = f"https://www.naukri.com/{keyword.replace(' ', '-').lower()}-jobs?k={keyword.replace(' ', '%20')}"
        try:
            print("Navigating to Naukri...")
            driver.get(naukri_url)
            print("Navigated to Naukri.")
        except Exception as e:
            print("Error navigating to Naukri:", e)
        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
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

        # --- Glassdoor Scraping ---
        glassdoor_url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={keyword.replace(' ', '%20')}"
        try:
            print("Navigating to Glassdoor...")
            driver.get(glassdoor_url)
            print("Navigated to Glassdoor.")
        except Exception as e:
            print("Error navigating to Glassdoor:", e)
        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_cards = soup.select('li[data-test="jobListing"]')
        for job in job_cards:
            title_tag = job.select_one('a.JobCard_jobTitle__GLyJ1[data-test="job-title"]')
            company_tag = job.select_one('span.EmployerProfile_compactEmployerName__9MGcV')
            location_tag = job.select_one('div.JobCard_location__Ds1fM[data-test="emp-location"]')
            apply_link_tag = title_tag
            glassdoor_jobs.append({
                'jobTitle': title_tag.text.strip() if title_tag else '',
                'company': company_tag.text.strip() if company_tag else '',
                'location': location_tag.text.strip() if location_tag else '',
                'experience': '',
                'applyLink': apply_link_tag['href'] if apply_link_tag and apply_link_tag.has_attr('href') else '',
                'platform': 'Glassdoor'
            })

        # --- Foundit Scraping ---
        foundit_url = f"https://www.foundit.in/srp/results?query={keyword.replace(' ', '%20')}"
        try:
            print("Navigating to Foundit...")
            driver.get(foundit_url)
            print("Navigated to Foundit.")
        except Exception as e:
            print("Error navigating to Foundit:", e)
        time.sleep(5)
        # Try scrolling multiple times to trigger lazy loading
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-tuple, div.srp-jobtuple-wrapper"))
            )
        except Exception as e:
            print("Timeout waiting for Foundit job cards:", e)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        print("All div classes in body:")
        for div in soup.body.find_all('div'):
            print(div.get('class'))
        job_cards = soup.select('div.cardContainer')
        if not job_cards:
            print("No Foundit job cards found with div.cardContainer")
        else:
            print("First Foundit job card HTML:")
            print(job_cards[0].prettify()[:2000])
        for job in job_cards:
            title_tag = job.select_one('div.jobTitle')
            company_tag = job.select_one('div.companyName')
            location_tag = job.select_one('div.details.location')
            exp_tag = job.select_one('div.experienceSalary')

            # Try to get the job description/apply link
            job_desc_link = ''
            title_link_tag = job.select_one('div.jobTitle a')
            if title_link_tag and title_link_tag.has_attr('href'):
                job_desc_link = title_link_tag['href']
            else:
                # Try anchor with /job- in href
                for a in job.find_all('a', href=True):
                    if '/job-' in a['href']:
                        job_desc_link = a['href']
                        break
                # Fallback: any anchor with href
                if not job_desc_link:
                    a = job.find('a', href=True)
                    if a:
                        job_desc_link = a['href']
            if job_desc_link and job_desc_link.startswith('/'):
                job_desc_link = 'https://www.foundit.in' + job_desc_link
            if not job_desc_link:
                # Fallback to search results page for the keyword
                job_desc_link = f"https://www.foundit.in/srp/results?query={keyword.replace(' ', '%20')}"

            foundit_jobs.append({
                'jobTitle': title_tag.text.strip() if title_tag else '',
                'company': company_tag.text.strip() if company_tag else '',
                'location': location_tag.text.strip() if location_tag else '',
                'experience': exp_tag.text.strip() if exp_tag else '',
                'applyLink': job_desc_link,
                'platform': 'Foundit'
            })
        print(f"Foundit jobs found: {len(foundit_jobs)}")
        driver.quit()

        # --- LinkedIn Scraping (use a fresh driver) ---
        try:
            linkedin_options = uc.ChromeOptions()
            linkedin_options.add_argument('--headless')
            linkedin_options.add_argument('--no-sandbox')
            linkedin_options.add_argument('--disable-dev-shm-usage')
            linkedin_options.add_argument('--window-size=1920,1080')
            linkedin_options.add_argument('--disable-gpu')
            linkedin_options.add_argument('--disable-infobars')
            linkedin_options.add_argument('--disable-extensions')
            linkedin_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')

            # Explicitly specify ChromeDriver version 138 to match Chrome browser version
            linkedin_driver = uc.Chrome(options=linkedin_options, version_main=138)
            linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}"
            try:
                print("Navigating to LinkedIn...")
                linkedin_driver.get(linkedin_url)
                print("Navigated to LinkedIn.")
            except Exception as e:
                print("Error navigating to LinkedIn:", e)
            time.sleep(5)
            if "login" in linkedin_driver.current_url:
                print("Please log in to LinkedIn in the opened browser window, then press Enter here to continue...")
                input()
                linkedin_driver.get(linkedin_url)
                time.sleep(5)
            print("LinkedIn page source:")
            print(linkedin_driver.page_source[:4000])
            soup = BeautifulSoup(linkedin_driver.page_source, 'html.parser')
            job_cards = soup.select('div.base-card')
            if not job_cards:
                job_cards = soup.select('li.jobs-search-results__list-item')
            if not job_cards:
                print("No LinkedIn job cards found with known selectors.")
            else:
                print("First LinkedIn job card HTML:")
                print(job_cards[0].prettify()[:2000])
            for job in job_cards:
                title_tag = job.select_one('h3.base-search-card__title, h3')
                company_tag = job.select_one('h4.base-search-card__subtitle, h4')
                location_tag = job.select_one('span.job-search-card__location, span')
                link_tag = job.select_one('a.base-card__full-link, a')
                linkedin_jobs.append({
                    'jobTitle': title_tag.text.strip() if title_tag else '',
                    'company': company_tag.text.strip() if company_tag else '',
                    'location': location_tag.text.strip() if location_tag else '',
                    'experience': '',
                    'applyLink': link_tag['href'] if link_tag and link_tag.has_attr('href') else '',
                    'platform': 'LinkedIn'
                })
            print(f"LinkedIn jobs found: {len(linkedin_jobs)}")
            linkedin_driver.quit()
        except Exception as e:
            print("Error scraping LinkedIn:", e)

        all_jobs = naukri_jobs + glassdoor_jobs + foundit_jobs + linkedin_jobs
        return all_jobs
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}