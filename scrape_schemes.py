import requests
from bs4 import BeautifulSoup
import csv
import certifi

def scrape_scheme_details(url):
    """Scrapes scheme details from a given URL."""
    try:
        # This is where the SSL verification happens, using certifi
        response = requests.get(url, verify=certifi.where())
        response.raise_for_status()  # Raise an error for bad HTTP responses

        soup = BeautifulSoup(response.content, 'html.parser')

        fieldset = soup.find('fieldset', class_='panel-default')
        if not fieldset:
            print("Fieldset not found on the page. Check HTML structure.")
            return None

        scheme_data = {}
        data_rows = fieldset.find_all('div', class_=['node_viewlist_even', 'node_viewlist_odd'])

        for row in data_rows:
            key_span = row.find('span', class_='left_column')
            if key_span:
                key = key_span.text.strip().replace("\xa0", " ")
                value_span = key_span.find_next_sibling('span', class_='right_column')
                value = value_span.text.strip() if value_span else ''

                if key in ["Scheme Details", "Eligibility criteria", "Validity of the Scheme"]:
                    next_row = row.find_next_sibling('div', class_=['node_viewlist_even', 'node_viewlist_odd'])
                    sub_key_span = next_row.find('span', class_='left_column')
                    sub_key = sub_key_span.text.strip().replace("\xa0", " ") if sub_key_span else ''
                    sub_value_span = sub_key_span.find_next_sibling('span', class_='right_column') if sub_key_span else None
                    sub_value = sub_value_span.text.strip() if sub_value_span else ''
                    scheme_data[sub_key] = sub_value
                else:
                    scheme_data[key] = value

        return scheme_data

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def save_to_csv(scheme_data, filename="schemes.csv"):
    """Saves scheme data to a CSV file."""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(scheme_data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for scheme in scheme_data:
                writer.writerow(scheme)

        print(f"Data saved to {filename}")

    except Exception as e:
        print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    all_scheme_data = []

    scheme_urls = [
        "https://www.tn.gov.in/scheme/department_wise/view/2/391",
        "https://www.tn.gov.in/scheme/department_wise/view/2/390",
        # ... add more URLs ...
    ]

    for url in scheme_urls:
        scraped_data = scrape_scheme_details(url)
        if scraped_data:
            all_scheme_data.append(scraped_data)

    if all_scheme_data:
        save_to_csv(all_scheme_data)