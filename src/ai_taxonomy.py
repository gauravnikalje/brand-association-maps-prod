import pandas as pd
import json
import logging
import os
from openai import OpenAI

def generate_taxonomy_suggestions(untagged_df: pd.DataFrame, existing_taxonomy: pd.DataFrame, client_name: str, brand_context: str, output_dir: str) -> pd.DataFrame:
    """
    Use NVIDIA NIM reasoning model to generate taxonomy suggestions for unmapped bigrams.
    """
    logging.info("Generating AI taxonomy suggestions for untagged bigrams...")
    if untagged_df.empty:
        logging.info("No untagged bigrams. Skipping AI inference.")
        return pd.DataFrame()
        
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        logging.error("NVIDIA_API_KEY not found in environment variables.")
        raise ValueError("NVIDIA_API_KEY not found.")
        
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    
    # Extract unique values from existing taxonomy for reference
    t1_list = []
    t2_list = []
    t3_list = []
    t4_list = []
    
    if not existing_taxonomy.empty:
        if "Attribute - T1" in existing_taxonomy.columns: t1_list = existing_taxonomy["Attribute - T1"].dropna().unique().tolist()
        if "Attribute - T2" in existing_taxonomy.columns: t2_list = existing_taxonomy["Attribute - T2"].dropna().unique().tolist()
        if "Attribute - T3" in existing_taxonomy.columns: t3_list = existing_taxonomy["Attribute - T3"].dropna().unique().tolist()
        if "Attribute - T4" in existing_taxonomy.columns: t4_list = existing_taxonomy["Attribute - T4"].dropna().unique().tolist()
        
    system_prompt = f"""You are an expert brand analyst performing Brand Association Mapping.
Your task is to classify bigrams (word pairs) extracted from social media conversations about {brand_context} into a 4-level taxonomy.

REASONING MODE: ON — Think step by step before classifying each bigram. 
Consider what the word pair means in the context of brand perception.

EXISTING TAXONOMY REFERENCE (use these categories when applicable):
T1 (Pillars): {t1_list}
T2 (Themes): {t2_list}  
T3 (Attributes): {t3_list}
T4 (Details): {t4_list}

RULES:
- Reuse existing categories whenever the bigram fits
- Only create NEW categories if no existing one is appropriate
- New T1 categories should be rare (brands typically have 2-5 pillars)
- T4 should be the most specific — it can be the bigram itself if no better label exists
- If a bigram is genuinely irrelevant noise, classify T1 as "NOISE"

OUTPUT FORMAT: Return ONLY a JSON array, no other text:
[
  {{"word1": "...", "word2": "...", "t1": "...", "t2": "...", "t3": "...", "t4": "..."}}
]"""

    # Batching into groups of 50
    records = []
    batch_size = 50
    input_records = untagged_df[["word1", "word2"]].drop_duplicates().to_dict('records')
    
    logging.info(f"Total unique untagged bigrams for inference: {len(input_records)}")
    
    for i in range(0, len(input_records), batch_size):
        batch = input_records[i:i+batch_size]
        logging.info(f"Processing batch {i//batch_size + 1}/{(len(input_records)+batch_size-1)//batch_size}...")
        
        user_message = json.dumps(batch)
        try:
            response = client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-ultra-253b-v1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=4000
            )
            
            result_str = response.choices[0].message.content
            if result_str is None:
                logging.error(f"Received empty response from API for batch {i}")
                continue
                
            # Cleanup any markdown json fences if model added them
            if "```json" in result_str:
                result_str = result_str.split("```json")[-1]
            if "```" in result_str:
                result_str = result_str.split("```")[0]
                
            try:
                parsed_json = json.loads(result_str.strip())
                records.extend(parsed_json)
            except json.JSONDecodeError as je:
                logging.error(f"Failed to parse JSON for batch starting at index {i}: {je}")
                
        except Exception as e:
            logging.error(f"NVIDIA API request failed for batch {i}: {e}", exc_info=True)
            
    df_results = pd.DataFrame(records)
    if not df_results.empty:
        os.makedirs(output_dir, exist_ok=True)
        out_file = os.path.join(output_dir, f"{client_name}_ai_suggested_taxonomy.xlsx")
        df_results.to_excel(out_file, index=False)
        logging.info(f"AI taxonomy suggestions saved to {out_file}")
        
    return df_results

def apply_approved_taxonomy(suggestions_path: str, existing_taxonomy_path: str) -> str:
    """MVP functionality to append reviewed suggestions to existing taxonomy."""
    # To be implemented when UI allows saving
    pass
