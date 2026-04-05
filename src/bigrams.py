import pandas as pd
import re
import logging
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Try to ensure nltk required packages are loaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Hardcoded country/city lists from generic logic
CITIES = ["london", "new york", "paris", "dubai", "shanghai", "beijing", "tokyo", "berlin", 
          "rome", "sydney", "mumbai", "delhi", "moscow", "toronto", "singapore", "hong kong",
          "los angeles", "chicago", "boston", "seattle", "san francisco", "madrid", "barcelona"]

def generate_bigrams(messages: pd.Series, config: dict) -> pd.DataFrame:
    """
    Generate, filter, normalize, and count bigrams from textual messages.
    
    Args:
        messages: Series of lemmatized text
        config: Client configuration dict
        
    Returns:
        DataFrame with [word1, word2, n] representing bigram frequencies
    """
    logging.info("Generating and filtering bigrams...")
    
    # Pre-compute filter sets
    nltk_stops = set(stopwords.words('english'))
    custom_stops = set(config.get("custom_stopwords", []))
    all_stops = nltk_stops.union(custom_stops)
    
    cities_set = set(CITIES)
    car_brands = set(config.get("car_brands_to_remove", []))
    bigram_filters = config.get("bigram_filters", [])
    
    # Pre-compile regex filters and normalizations
    compiled_filters = [re.compile(f) for f in bigram_filters]
    
    norms = config.get("bigram_normalizations", {})
    compiled_norms = [(re.compile(k), v) for k, v in norms.items()]
    
    min_len = config.get("min_word_length", 2)
    
    bigram_counts = {}
    
    for msg in messages.dropna():
        # Tokenize (simple splitting by space works best for already cleaned text, or word_tokenize)
        tokens = str(msg).split()
        if len(tokens) < 2:
            continue
            
        # Sliding window
        for i in range(len(tokens) - 1):
            w1 = tokens[i]
            w2 = tokens[i+1]
            
            # Apply individual word checks (stopwords, length, numeric, country/city, brand)
            if (len(w1) <= min_len) or (len(w2) <= min_len): continue
            if w1 in all_stops or w2 in all_stops: continue
            if w1.isnumeric() or w2.isnumeric(): continue
            if w1 in cities_set or w2 in cities_set: continue
            if w1 in car_brands or w2 in car_brands: continue
            
            # Apply Regex filters (if ANY word matches, discard bigram)
            discard = False
            for pat in compiled_filters:
                if pat.match(w1) or pat.match(w2):
                    discard = True
                    break
            if discard:
                continue
                
            # Apply normalizations
            for pat, repl in compiled_norms:
                if pat.match(w1): w1 = repl
                if pat.match(w2): w2 = repl
                
            # Alphabetical sort and word equality check
            bw1, bw2 = sorted([w1, w2])
            if bw1 == bw2:
                continue
                
            # Count
            key = (bw1, bw2)
            bigram_counts[key] = bigram_counts.get(key, 0) + 1
            
    # Convert to DataFrame
    rows = [{"word1": k[0], "word2": k[1], "n": v} for k, v in bigram_counts.items()]
    df_bigrams = pd.DataFrame(rows)
    
    if not df_bigrams.empty:
        df_bigrams = df_bigrams.sort_values(by="n", ascending=False).reset_index(drop=True)
    else:
        df_bigrams = pd.DataFrame(columns=["word1", "word2", "n"])
        
    logging.info(f"Generated {len(df_bigrams)} unique bigrams.")
    return df_bigrams
