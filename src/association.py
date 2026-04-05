import pandas as pd
import numpy as np
import logging

def get_association_matrix(mentions_assoc: str, sentiment_assoc: str) -> str:
    """4x4 mapping logic for Final Association."""
    if mentions_assoc == "Strong":
        if sentiment_assoc == "Strong": return "Strong"
        if sentiment_assoc == "Moderate": return "Moderate"
        if sentiment_assoc == "Weak": return "Weak"
        return "Weak"
    elif mentions_assoc == "Moderate":
        if sentiment_assoc == "Strong": return "Strong"
        if sentiment_assoc == "Moderate": return "Moderate"
        if sentiment_assoc == "Weak": return "Weak"
        return "Weak"
    elif mentions_assoc == "Weak":
        if sentiment_assoc in ["Strong", "Moderate"]: return "Moderate"
        if sentiment_assoc == "Weak": return "Weak"
        return "Negligible"
    else: # Negligible
        if sentiment_assoc == "Strong": return "Moderate"
        if sentiment_assoc in ["Moderate", "Weak"]: return "Weak"
        return "Negligible"

def compute_association(df: pd.DataFrame, mention_col: str = "Total") -> pd.DataFrame:
    """
    Compute association scoring (Mentions, Sentiment, Overall) using IQR.
    """
    if df.empty:
        return df
        
    df = df.copy()
    
    # Calculate Mentions bounds based on quantiles strictly
    q1 = df[mention_col].quantile(0.25)
    q2 = df[mention_col].quantile(0.50)
    q3 = df[mention_col].quantile(0.75)
    
    def grade_mentions(val):
        if val >= q3: return "Strong"
        if val > q2 and val < q3: return "Moderate"
        if val > q1 and val <= q2: return "Weak"
        return "Negligible"
        
    def grade_sentiment(val):
        if val >= 80: return "Strong"
        if val >= 50 and val < 80: return "Moderate"
        if val >= 20 and val < 50: return "Weak"
        return "Negligible"
        
    df["Mentions_association"] = df[mention_col].apply(grade_mentions)
    df["Sentiment_association"] = df["Positive_perc"].apply(grade_sentiment)
    
    df["Association"] = df.apply(lambda r: get_association_matrix(r["Mentions_association"], r["Sentiment_association"]), axis=1)
    
    return df

def aggregate_and_score(tagged_df: pd.DataFrame, levels: list[str]) -> pd.DataFrame:
    """
    Groups bigrams at specified level (like T2, T3) and applies association scoring globally AND per-T1.
    """
    if tagged_df.empty:
        return pd.DataFrame()
        
    logging.info(f"Aggregating and scoring for levels: {levels}")
    
    agg = tagged_df.groupby(levels).agg(
        Total=("Total", "sum"),
        Positive_perc=("Positive_perc", "mean"),
        Positive=("Positive", "sum"),
        Negative=("Negative", "sum")
    ).reset_index()
    
    # Recompute perc over the sum
    agg["Positive_perc"] = (agg["Positive"] / agg["Total"] * 100).fillna(0).round(2)
    agg["Negative_perc"] = (agg["Negative"] / agg["Total"] * 100).fillna(0).round(2)
    
    # Global Scoring
    agg = compute_association(agg, mention_col="Total")
    
    # Per-T1 Scoring
    # If "Attribute - T1" is in the grouping, apply the same computing locally
    if "Attribute - T1" in agg.columns:
        def score_group(group):
            return compute_association(group, mention_col="Total")[["Mentions_association", "Sentiment_association", "Association"]]
            
        t1_scored = agg.groupby("Attribute - T1", group_keys=False).apply(score_group)
        agg["Mentions_association1"] = t1_scored["Mentions_association"]
        agg["Sentiment_association1"] = t1_scored["Sentiment_association"]
        agg["Association1"] = t1_scored["Association"]
        
    return agg
