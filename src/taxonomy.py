import pandas as pd
import os
import logging

def load_taxonomies(config: dict, data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load Bigram and Monogram taxonomies from the given directory.
    Cleans strings and formats matching columns.
    
    Args:
        config: Client config dict (contains file names).
        data_dir: Path to directory containing taxonomy files.
        
    Returns:
        tuple containing (bigram_tax_df, mono_tax_df)
    """
    files = config.get("input_files", {})
    bigram_file = os.path.join(data_dir, files.get("bigram_taxonomy", "Bigram tagging_taxonomy.xlsx"))
    mono_file = os.path.join(data_dir, files.get("monogram_taxonomy", "monogram tagging_taxonomy.xlsx"))
    
    logging.info("Loading taxonomy files...")
    
    bigram_tax = pd.read_excel(bigram_file)
    mono_tax = pd.read_excel(mono_file)
    
    # Clean whitespace and case on Attribute columns
    for df in [bigram_tax, mono_tax]:
        for col in df.columns:
            if "Attribute" in str(col) or "word" in str(col).lower():
                df[col] = df[col].astype(str).str.strip()
    
    # For bigram taxonomy: Ensure word1 and word2 are sorted alphabetically just like generation
    if "word1" in bigram_tax.columns and "word2" in bigram_tax.columns:
        # Sort words
        def sort_words(row):
            w1, w2 = str(row["word1"]), str(row["word2"])
            sorted_w = sorted([w1, w2])
            return sorted_w[0], sorted_w[1]
            
        sorted_pairs = bigram_tax.apply(sort_words, axis=1, result_type="expand")
        bigram_tax["word1"] = sorted_pairs[0]
        bigram_tax["word2"] = sorted_pairs[1]
        
        bigram_tax["Key"] = bigram_tax["word1"] + "_" + bigram_tax["word2"]
        
    if "word" in mono_tax.columns:
        mono_tax["word"] = mono_tax["word"].astype(str).str.lower()
        
    logging.info(f"Loaded Bigram Taxonomy: {len(bigram_tax)} rows. Monogram Taxonomy: {len(mono_tax)} rows.")
    return bigram_tax, mono_tax

def map_taxonomy(bigram_counts: pd.DataFrame, bigram_tax: pd.DataFrame, mono_tax: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform 3-pass mapping of bigrams to the taxonomy.
    
    Args:
        bigram_counts: DataFrame from generate_bigrams
        bigram_tax: Bigram taxonomy DataFrame
        mono_tax: Monogram taxonomy DataFrame
        
    Returns:
        tuple(tagged_df, untagged_df)
    """
    logging.info("Mapping taxonomies (3-pass algorithm)...")
    
    if bigram_counts.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    # Prepare key
    bigram_counts["Key"] = bigram_counts["word1"] + "_" + bigram_counts["word2"]
    
    # Filter tax df columns to only keep what's needed to avoid duplicates
    bi_cols = [c for c in bigram_tax.columns if "Attribute" in str(c)] + ["Key"]
    bigram_tax_subset = bigram_tax[bi_cols].drop_duplicates(subset=["Key"], keep="first")
    
    mo_cols = [c for c in mono_tax.columns if "Attribute" in str(c)] + ["word"]
    mono_tax_subset = mono_tax[mo_cols].drop_duplicates(subset=["word"], keep="first")
    
    # PASS 1: Bigram Match
    df_p1 = bigram_counts.merge(bigram_tax_subset, on="Key", how="left")
    
    # Rows successfully tagged in Pass 1
    tagged_p1 = df_p1.dropna(subset=[c for c in df_p1.columns if "Attribute - T1" in str(c)]).copy()
    untagged_p1 = df_p1[df_p1[[c for c in df_p1.columns if "Attribute - T1" in str(c)]].isna().all(axis=1)].copy()
    
    # Drop attribute columns from untagged for next pass
    att_cols = [c for c in df_p1.columns if "Attribute" in str(c)]
    untagged_p1 = untagged_p1.drop(columns=att_cols)
    
    # PASS 2: Monogram Match on word1
    df_p2 = untagged_p1.merge(mono_tax_subset, left_on="word1", right_on="word", how="left").drop(columns=["word"])
    tagged_p2 = df_p2.dropna(subset=[c for c in df_p2.columns if "Attribute - T1" in str(c)]).copy()
    untagged_p2 = df_p2[df_p2[[c for c in df_p2.columns if "Attribute - T1" in str(c)]].isna().all(axis=1)].copy()
    untagged_p2 = untagged_p2.drop(columns=att_cols)
    
    # PASS 3: Monogram Match on word2
    df_p3 = untagged_p2.merge(mono_tax_subset, left_on="word2", right_on="word", how="left").drop(columns=["word"])
    tagged_p3 = df_p3.dropna(subset=[c for c in df_p3.columns if "Attribute - T1" in str(c)]).copy()
    untagged_final = df_p3[df_p3[[c for c in df_p3.columns if "Attribute - T1" in str(c)]].isna().all(axis=1)].copy()
    untagged_final = untagged_final.drop(columns=att_cols)
    
    # Combine tagged DataFrames
    tagged_df = pd.concat([tagged_p1, tagged_p2, tagged_p3], ignore_index=True)
    
    logging.info(f"Tagged {len(tagged_df)} bigrams. Untagged: {len(untagged_final)}")
    
    return tagged_df, untagged_final
