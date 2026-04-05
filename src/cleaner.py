import pandas as pd
import re
import logging
import spacy

def clean_messages(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Clean messages dataframe (lowercase, regex filtering, punctuation removal).
    
    Args:
        df: DataFrame with at least `SocialNetwork`, `Message`, `Sentiment` columns.
        config: Client configuration dict.
        
    Returns:
        Cleaned DataFrame.
    """
    # Ensure working on a copy to avoid SettingWithCopyWarning
    df = df.copy()
    
    if "Message" not in df.columns:
        raise ValueError("DataFrame missing 'Message' column.")
        
    logging.info(f"Starting message cleaning on {len(df)} rows.")

    # Lowercase messages
    df["Message"] = df["Message"].astype(str).str.lower()
    
    # Message filters
    msg_filters = config.get("message_filters", [])
    for mf in msg_filters:
        # Check if matched and replace entire message with empty string if matched
        df.loc[df["Message"].str.contains(mf, regex=True, na=False), "Message"] = ""
        
    # Strip punctuation
    df["Message"] = df["Message"].apply(lambda x: re.sub(r'[^\w\s]', ' ', x))
    
    # Strip non-alphabetic characters
    df["Message"] = df["Message"].apply(lambda x: re.sub(r'[^a-zA-Z\s]', ' ', x))
    
    # Collapse repeated chars (3+)
    df["Message"] = df["Message"].apply(lambda x: re.sub(r'([a-zA-Z])\1{2,}', r'\1', x))
    
    # Clean whitespace
    df["Message"] = df["Message"].apply(lambda x: re.sub(r'\s+', ' ', x).strip())
    
    # Drop rows where Message is empty string
    initial_len = len(df)
    df = df[df["Message"] != ""]
    df = df.dropna(subset=["Message"])
    
    logging.info(f"Dropped {initial_len - len(df)} rows due to empty messages/filters.")

    # Normalize Sentiment to uppercase if present
    if "Sentiment" in df.columns:
        df["Sentiment"] = df["Sentiment"].astype(str).str.upper()
        
    return df

def lemmatize_messages(messages: pd.Series) -> pd.Series:
    """
    Lemmatize text using spaCy.
    
    Args:
        messages: Series containing text.
        
    Returns:
        Series with lemmatized text.
    """
    try:
        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        logging.info("spaCy 'en_core_web_sm' loaded successfully.")
    except Exception as e:
        logging.warning(f"spaCy 'en_core_web_sm' failing to load: {e}. Returning original messages.")
        return messages
        
    def _lemmatize_text(text: str) -> str:
        # Use spaCy to lemmatize
        doc = nlp(text)
        return " ".join([token.lemma_ for token in doc if not token.is_space])
        
    logging.info("Lemmatizing messages...")
    return messages.apply(_lemmatize_text)
