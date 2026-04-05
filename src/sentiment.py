import pandas as pd
import re
import logging

def map_sentiment(source_df: pd.DataFrame, tagged_bigrams: pd.DataFrame) -> pd.DataFrame:
    """
    Map sentiment from source messages back to tagged bigrams.
    
    Args:
        source_df: Initial source datatrame with `Message` and `Sentiment`.
        tagged_bigrams: DataFrame of bigrams mapped to taxonomy.
        
    Returns:
        DataFrame grouping by word1, word2, calculating Pos/Neg counts and %.
    """
    logging.info("Mapping sentiment...")
    
    if tagged_bigrams.empty or source_df.empty:
        return pd.DataFrame()
        
    # Clean source_df messages for pure word matching (basic clean to remove punctuation)
    # The initial cleaner removed punctuation, we just need to ensure whitespace is normalized
    temp_df = source_df.copy()
    temp_df["Message_clean"] = temp_df["Message"].astype(str).str.lower()
    temp_df["Message_clean"] = temp_df["Message_clean"].apply(lambda x: re.sub(r'[^\w\s]', ' ', x))
    temp_df["Message_clean"] = temp_df["Message_clean"].apply(lambda x: " " + re.sub(r'\s+', ' ', x).strip() + " ")
    
    # We will search the messages for strings like " word1 word2 " or " word2 word1 "
    # This might be slow for massive datasets, but matches the R behavior.
    
    # Create matching dictionary
    # Instead of iterating over all messages and searching all bigrams, which is O(N*M),
    # A faster approach is to tokenize all messages, create actual bigrams, and exact match.
    # However, to perfectly mirror R which checks if both words appear adjacently 
    # (word1_word2 or word2_word1), we can build bigram tokens per message.
    
    records = []
    
    # Make a set of valid keys for O(1) lookup
    valid_keys = set(tagged_bigrams["Key"].tolist())
    
    for idx, row in temp_df.iterrows():
        sentiment = str(row.get("Sentiment", "")).upper()
        if sentiment not in ["POSITIVE", "NEGATIVE"]:
            # If neutral or other, skip or treat as you wish (R code generally isolates Pos/Neg)
            continue
            
        msg = row["Message_clean"]
        words = msg.split()
        
        found_keys = set()
        for i in range(len(words) - 1):
            w1 = words[i]
            w2 = words[i+1]
            # Must sort to match Key
            bw1, bw2 = sorted([w1, w2])
            k = f"{bw1}_{bw2}"
            if k in valid_keys:
                found_keys.add(k)
                
        for key in found_keys:
            v_w1, v_w2 = key.split("_", 1)
            records.append({
                "word1": v_w1,
                "word2": v_w2,
                "Sentiment": sentiment
            })
            
    sentiment_df = pd.DataFrame(records)
    if sentiment_df.empty:
        return pd.DataFrame()
        
    # Group by
    grouped = sentiment_df.groupby(["word1", "word2", "Sentiment"]).size().unstack(fill_value=0).reset_index()
    
    # Ensure Positive, Negative exist
    if "POSITIVE" not in grouped.columns: grouped["POSITIVE"] = 0
    if "NEGATIVE" not in grouped.columns: grouped["NEGATIVE"] = 0
    
    grouped = grouped.rename(columns={"POSITIVE": "Positive", "NEGATIVE": "Negative"})
    
    grouped["Total"] = grouped["Positive"] + grouped["Negative"]
    grouped["Positive_perc"] = (grouped["Positive"] / grouped["Total"]) * 100
    grouped["Negative_perc"] = (grouped["Negative"] / grouped["Total"]) * 100
    
    grouped["Positive_perc"] = grouped["Positive_perc"].fillna(0).round(2)
    grouped["Negative_perc"] = grouped["Negative_perc"].fillna(0).round(2)
    
    logging.info(f"Mapped sentiment for {len(grouped)} unique bigrams.")
    
    # Merge with tagged taxonomy
    merged_df = tagged_bigrams.merge(grouped, on=["word1", "word2"], how="inner")
    
    return merged_df
