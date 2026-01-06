import copy
import json
import os
import csv
import signal
import sys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup

class MySchemeScraper:
    def __init__(self):
        self.myscheme_url = 'https://rules.myscheme.in/'
        self.scraped_scheme_details = []
        self.last_scraped_index_file = 'last_scraped_index.txt'

        # Set up Firefox to run in headless mode
        options = Options()
        options.headless = True  # Run in headless mode to avoid opening a window
        self.driver = webdriver.Firefox(options=options)

    def signal_handler(self, signal, frame):
        print("Saving current scraped data before exiting...")
        self.save_to_json(self.scraped_scheme_details, 'myschemes_scraped.json')
        self.save_to_csv(self.scraped_scheme_details, 'myschemes_scraped.csv')
        sys.exit(0)

    def get_scheme_links(self):
        self.driver.get(self.myscheme_url)
        WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.ID, "__next")))
        result_elements = self.driver.find_element(By.ID, '__next').find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        scheme_links = []

        for result_element in result_elements:
            table_rows = result_element.find_elements(By.TAG_NAME, 'td')
            result_details_dict = {
                'sr_no': table_rows[0].text,
                'scheme_name': table_rows[1].text.replace('\nCheck Eligibility', ''),
                'scheme_link': table_rows[2].find_element(By.TAG_NAME, 'a').get_attribute('href')
            }
            scheme_links.append(result_details_dict)

        return scheme_links[2000: ]  # Get only the first 10 links

    def get_scheme_details(self, scheme_links):
        for idx, scheme in enumerate(scheme_links):
            self.driver.get(scheme['scheme_link'])
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.ID, "__next")))
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            scheme['details'] = soup.find('div', id='details').text if soup.find('div', id='details') else ''
            scheme['benefits'] = soup.find('div', id='benefits').text if soup.find('div', id='benefits') else ''
            scheme['eligibility'] = soup.find('div', id='eligibility').text if soup.find('div', id='eligibility') else ''
            scheme['application_process'] = soup.find('div', id='application-process').text if soup.find('div', id='application-process') else ''
            scheme['documents_required'] = soup.find('div', id='documents-required').text if soup.find('div', id='documents-required') else ''

            self.scraped_scheme_details.append(scheme)
            print(f"Scraped scheme {idx + 1}: {scheme['scheme_name']}")  # Display increment count in console

            # Save progress in case of manual stop
            self.save_progress(len(self.scraped_scheme_details))

    def save_progress(self, count):
        with open(self.last_scraped_index_file, 'w') as f:
            f.write(str(count))

    def load_progress(self):
        if os.path.exists(self.last_scraped_index_file):
            with open(self.last_scraped_index_file, 'r') as f:
                return int(f.read())
        return 0

    def download(self):
        scheme_links = self.get_scheme_links()
        self.get_scheme_details(scheme_links)
        return self.scraped_scheme_details

    def save_to_json(self, data, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_data.extend(data)  # Append new data
        else:
            existing_data = data

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

    def save_to_csv(self, data, filename):
        file_exists = os.path.exists(filename)
        with open(filename, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            if not file_exists:
                writer.writeheader()  # Write header only if the file is new
            writer.writerows(data)  # Append new rows

    def combine_myscheme_provided_and_scraped_data(self, scraped_scheme_details):
        myscheme_structured_data = json.load(open('myScheme-data.json'))['hits']['hits']
        required_fields_from_structured_data = ['schemeShortTitle', 'schemeCategory', 'schemeSubCategory', 'gender',
                                                'minority', 'beneficiaryState', 'residence', 'caste', 'disability',
                                                'occupation', 'maritalStatus', 'education', 'age', 'isStudent', 'isBpl']

        myscheme_structured_data_dict = {i['_source']['schemeName'].lower().strip(): i['_source'] for i in myscheme_structured_data}
        combined_schemes_data = []

        for scheme in scraped_scheme_details:
            structured_info = myscheme_structured_data_dict.get(scheme['scheme_name'].lower().strip())
            if structured_info is not None:
                structured_info = {k: v for k, v in structured_info.items() if k in required_fields_from_structured_data}
                scheme.update(structured_info)
            combined_schemes_data.append(copy.deepcopy(scheme))

        return combined_schemes_data

if __name__ == '__main__':
    scraper = MySchemeScraper()

    # Set signal handler for graceful exit
    signal.signal(signal.SIGINT, scraper.signal_handler)

    # Load progress to continue from where it left off
    last_index = scraper.load_progress()

    scraped_scheme_details = scraper.download()

    # Save the data to JSON and CSV when the download completes
    scraper.save_to_json(scraped_scheme_details, 'myschemes_scraped.json')
    scraper.save_to_csv(scraped_scheme_details, 'myschemes_scraped.csv')

    # Combine with structured data if available
    combined_schemes_data = scraper.combine_myscheme_provided_and_scraped_data(scraped_scheme_details)

    # Save combined data to JSON and CSV
    scraper.save_to_json(combined_schemes_data, 'myschemes_scraped_combined.json')
    scraper.save_to_csv(combined_schemes_data, 'myschemes_scraped_combined.csv')

    # Close the driver after all tasks are complete
    scraper.driver.quit()
