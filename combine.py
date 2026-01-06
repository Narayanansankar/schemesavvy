import pandas as pd
import re

# Load the CSV file
csv_file_path = 'myschemes_scraped.csv'  # Update with your actual CSV file path
data = pd.read_csv(csv_file_path)


# Function to categorize schemes based on keywords in the name and details
def categorize_scheme(name, details):
    text = (str(name) + " " + str(details)).lower()  # Combine name and details for categorization

    if 'agriculture' in text or 'farmer' in text or 'crop' in text:
        return 'Agriculture'
    elif 'education' in text or 'scholarship' in text or 'student' in text or 'school' in text:
        return 'Education'
    elif 'health' in text or 'medical' in text or 'hospital' in text or 'insurance' in text:
        return 'Healthcare'
    elif 'job' in text or 'employment' in text or 'recruitment' in text or 'placement' in text:
        return 'Jobs'
    elif 'housing' in text or 'home' in text or 'house' in text or 'property' in text:
        return 'Housing'
    elif 'loan' in text or 'credit' in text or 'finance' in text or 'subsidy' in text:
        return 'Financial Services'
    elif 'women' in text or 'child' in text or 'maternity' in text or 'girl' in text:
        return 'Women & Child Development'
    elif 'pension' in text or 'old age' in text or 'social security' in text or 'welfare' in text:
        return 'Social Welfare'
    elif 'youth' in text or 'entrepreneur' in text or 'startup' in text:
        return 'Youth Affairs & Entrepreneurship'
    elif 'environment' in text or 'forest' in text or 'climate' in text:
        return 'Environment'
    else:
        return 'Others'  # Default category if no match is found


# Function to assign a state based on keywords in the scheme name and details
def assign_state(name, details):
    text = (str(name) + " " + str(details)).lower()  # Combine name and details

    if 'tamil nadu' in text:
        return 'Tamil Nadu'
    elif 'maharashtra' in text:
        return 'Maharashtra'
    elif 'kerala' in text:
        return 'Kerala'
    elif 'uttar pradesh' in text:
        return 'Uttar Pradesh'
    elif 'karnataka' in text:
        return 'Karnataka'
    elif 'gujarat' in text:
        return 'Gujarat'
    elif 'rajasthan' in text:
        return 'Rajasthan'
    else:
        return 'National'  # Default if no specific state is found




# Create new 'Category', 'State', and 'Caste Category' columns
data['Category'] = data.apply(lambda row: categorize_scheme(row['scheme_name'], row['details']), axis=1)
data['State'] = data.apply(lambda row: assign_state(row['scheme_name'], row['details']), axis=1)

# Save the updated CSV with the new 'Category', 'State', and 'Caste Category' fields
updated_csv_file_path = 'myschemes_with_category_state_and_caste.csv'
data.to_csv(updated_csv_file_path, index=False)

print(f"Updated CSV saved to: {updated_csv_file_path}")
