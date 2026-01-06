import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Ensure required NLTK data is downloaded
try:
    nltk.data.find('corpora/stopwords')
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/wordnet') 
except LookupError:
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('punkt_tab') # Required for newer NLTK versions

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def preprocess_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    words = nltk.word_tokenize(text)
    words = [lemmatizer.lemmatize(word) for word in words if word.isalnum() and word not in stop_words]
    return " ".join(words)

def extract_entities(query: str) -> tuple[str | None, str | None]:
    query = query.lower()
    
    # Map common aliases/variations to Canonical State Names
    state_aliases = {
        "andhra pradesh": "Andhra Pradesh", "andhra": "Andhra Pradesh", "ap": "Andhra Pradesh",
        "arunachal pradesh": "Arunachal Pradesh", "arunachal": "Arunachal Pradesh",
        "assam": "Assam",
        "bihar": "Bihar",
        "chhattisgarh": "Chhattisgarh", "cg": "Chhattisgarh",
        "goa": "Goa",
        "gujarat": "Gujarat",
        "haryana": "Haryana",
        "himachal pradesh": "Himachal Pradesh", "himachal": "Himachal Pradesh", "hp": "Himachal Pradesh",
        "jharkhand": "Jharkhand",
        "karnataka": "Karnataka",
        "kerala": "Kerala",
        "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
        "maharashtra": "Maharashtra", "mh": "Maharashtra",
        "manipur": "Manipur",
        "meghalaya": "Meghalaya",
        "mizoram": "Mizoram",
        "nagaland": "Nagaland",
        "odisha": "Odisha", "orissa": "Odisha",
        "punjab": "Punjab", "pb": "Punjab",
        "rajasthan": "Rajasthan", "raj": "Rajasthan",
        "sikkim": "Sikkim",
        "tamil nadu": "Tamil Nadu", "tamilnadu": "Tamil Nadu", "tn": "Tamil Nadu", "tamil": "Tamil Nadu",
        "telangana": "Telangana", "ts": "Telangana",
        "tripura": "Tripura",
        "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh", "uttar": "Uttar Pradesh",
        "uttarakhand": "Uttarakhand", "uk": "Uttarakhand", "ut": "Uttarakhand",
        "west bengal": "West Bengal", "wb": "West Bengal", "bengal": "West Bengal",
        "delhi": "Delhi", "new delhi": "Delhi",
        "jammu and kashmir": "Jammu and Kashmir", "j&k": "Jammu and Kashmir",
        "puducherry": "Puducherry", "pondicherry": "Puducherry",
        "united states": None, "usa": None, "us": None, # Exclude country confusion
        "all india": "All India", "central": "All India", "national": "All India", "pan india": "All India", "india": "All India"
    }

    found_state = None
    # Check for state matches (longest match first determines precedence, e.g. "West Bengal" over "Bengal")
    # We sort aliases by length descending so "Tamil Nadu" is checked before "Tamil"
    sorted_aliases = sorted(state_aliases.keys(), key=len, reverse=True)
    
    for alias in sorted_aliases:
        # Check for whole word match to avoid partials like 'up' in 'support'
        # Simple approach: check if alias is in query. 
        # For short 2-letter codes, we strictly enforce word boundaries.
        if len(alias) <= 2:
            if f" {alias} " in f" {query} ":
                 found_state = state_aliases[alias]
                 break
        elif alias in query:
             found_state = state_aliases[alias]
             break

    categories = {
        "education": ["education", "scholarship", "study", "student", "college", "school", "university"],
        "healthcare": ["health", "hospital", "medical", "insurance", "treatment", "medicine"],
        "women": ["women", "girl", "female", "mother", "widow", "lady", "ladies"],
        "disability": ["handicap", "disability", "disabled", "divyang", "blind", "differently abled"],
        "agriculture": ["agriculture", "farmer", "crop", "farming", "kisan", "irrigation"],
        "employment": ["employment", "job", "work", "training", "skill", "business", "entrepreneur", "loan", "startup"],
        "housing": ["house", "housing", "home", "shelter", "awaas", "accommodation"],
        "pension": ["pension", "retirement", "old age", "senior citizen"],
    }

    found_category = next((cat for cat, kw in categories.items() if any(k in query for k in kw)), None)
    return found_state, found_category