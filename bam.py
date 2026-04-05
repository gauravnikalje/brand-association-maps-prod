import argparse
import logging
import os
import sys
import pandas as pd
from dotenv import load_dotenv

from src.config_loader import load_config
from src.cleaner import clean_messages, lemmatize_messages
from src.bigrams import generate_bigrams
from src.taxonomy import load_taxonomies, map_taxonomy
from src.sentiment import map_sentiment
from src.association import compute_association, aggregate_and_score
from src.output_writer import write_output
from src.ai_taxonomy import generate_taxonomy_suggestions

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    setup_logging()
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="AntiGravity BAM AI Pipeline")
    parser.add_argument("--config", required=True, help="Path to client config JSON file")
    parser.add_argument("--data-dir", required=True, help="Path to input data directory")
    parser.add_argument("--output", default="output", help="Path to output directory")
    parser.add_argument("--generate-taxonomy", action="store_true", help="Run AI taxonomy generation on untagged bigrams")
    
    args = parser.parse_args()
    
    logging.info("Starting BAM Pipeline...")
    
    # 1. Load config
    config = load_config(args.config)
    client_name = config.get("client", "UnknownClient")
    brand_context = config.get("brand", "")
    
    # 2. Read Input Data
    input_files = config.get("input_files", {}).get("data", [])
    df_list = []
    
    for f in input_files:
        path = os.path.join(args.data_dir, f)
        logging.info(f"Loading input file: {path}")
        try:
            xl = pd.ExcelFile(path)
            # If multiple sheets, we concatenate them all or just read the first? 
            # Often R uses the first sheet or specific ones. Let's assume one main sheet or concat all.
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                df_list.append(df)
        except Exception as e:
            logging.error(f"Error reading {path}: {e}")
            sys.exit(1)
            
    if not df_list:
        logging.error("No input data loaded.")
        sys.exit(1)
        
    source_df = pd.concat(df_list, ignore_index=True)
    logging.info(f"Total source rows loaded: {len(source_df)}")
    
    # 3. Clean and Lemmatize
    cleaned_df = clean_messages(source_df, config)
    lemmatized = lemmatize_messages(cleaned_df["Message"])
    
    # 4. Generate Bigrams (returns df grouped by bigram word pair)
    bigram_counts = generate_bigrams(lemmatized, config)
    
    if bigram_counts.empty:
        logging.error("No valid bigrams generated after filtering.")
        sys.exit(1)
        
    # 5. Taxonomy mapping
    bigram_tax, mono_tax = load_taxonomies(config, args.data_dir)
    tagged_df, untagged_df = map_taxonomy(bigram_counts, bigram_tax, mono_tax)
    
    # 6. AI Taxonomy (Optional)
    if args.generate_taxonomy and not untagged_df.empty:
        generate_taxonomy_suggestions(
            untagged_df=untagged_df,
            existing_taxonomy=bigram_tax,
            client_name=client_name,
            brand_context=brand_context,
            output_dir=args.output
        )
        logging.info(f"AI taxonomy suggestions saved to {args.output}. Review and re-run without --generate-taxonomy.")
        sys.exit(0)  # Exit here as per plan for human review step
        
    if tagged_df.empty:
        logging.error("No bigrams matched the taxonomy.")
        sys.exit(1)
        
    # 7. Sentiment Mapping
    sentiment_mapped = map_sentiment(cleaned_df, tagged_df)
    
    # 8. Association Scoring
    logging.info("Computing association logic...")
    word_level = compute_association(sentiment_mapped, mention_col="Total")
    
    t4 = aggregate_and_score(sentiment_mapped, ["Attribute - T1", "Attribute - T2", "Attribute - T3", "Attribute - T4"])
    t3 = aggregate_and_score(sentiment_mapped, ["Attribute - T1", "Attribute - T2", "Attribute - T3"])
    t2 = aggregate_and_score(sentiment_mapped, ["Attribute - T1", "Attribute - T2"])
    
    # 9. Output creation
    results = {
        "word_level": word_level,
        "t4": t4,
        "t3": t3,
        "t2": t2,
        "untagged": untagged_df
    }
    
    write_output(results, args.output, client_name)
    
    # 10. Summary
    logging.info("=== PIPELINE SUMMARY ===")
    logging.info(f"Total bigrams (filtered): {len(bigram_counts)}")
    logging.info(f"Tagged: {len(tagged_df)} ({(len(tagged_df)/len(bigram_counts))*100:.1f}%)")
    logging.info(f"Untagged: {len(untagged_df)}")
    if not word_level.empty:
        dist = word_level["Association"].value_counts().to_dict()
        logging.info(f"Association distribution (Word Level): {dist}")
    logging.info("========================")

if __name__ == "__main__":
    main()
