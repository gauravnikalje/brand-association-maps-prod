# AntiGravity BAM AI Pipeline — Unified Build Plan (MVP 1 + MVP 2)

## Goal

Build a single Python CLI pipeline that:  
1. **Replicates the existing R-based BAM workflow** (text cleaning → bigram extraction → taxonomy mapping → sentiment scoring → association output)  
2. **Adds AI-powered taxonomy generation** for new brands using NVIDIA NIM reasoning models  
3. Is **config-driven** so switching from Jaguar to Nike is just a JSON file change  

---

## NVIDIA NIM Model Selection

> [!IMPORTANT]
> The taxonomy generation task requires **precise hierarchical reasoning** — given a raw bigram like "battery life", the model must correctly place it into T1 (Performance & Capability) → T2 (Technology & Innovation) → T3 (Battery Performance) → T4 (Battery Life). This requires o3-class reasoning ability.

### Primary Model: `nvidia/llama-3.1-nemotron-ultra-253b-v1`

| Attribute | Detail |
|---|---|
| **Model ID** | `nvidia/llama-3.1-nemotron-ultra-253b-v1` |
| **API Base** | `https://integrate.api.nvidia.com/v1` |
| **Protocol** | OpenAI-compatible Chat Completions API |
| **Free tier** | Yes — for prototyping/dev (rate limit ~40 req/min) |
| **Reasoning mode** | Toggleable via system prompt ("detailed thinking on") |
| **Why this model** | 253B dense, NAS-optimized. Excels at GPQA and instruction following. Best for structured classification tasks where you need consistent JSON output |

### Fallback Model: `deepseek-ai/deepseek-r1`

| Attribute | Detail |
|---|---|
| **Model ID** | `deepseek-ai/deepseek-r1` |
| **Why fallback** | 671B MoE, strongest pure reasoning (AIME25, MATH500), but slower and more verbose chain-of-thought. Use if Nemotron fails on complex edge cases |

### API Access Setup
1. Sign up at `build.nvidia.com`
2. Generate API key (format: `nvapi-...`)
3. Store in `.env` file as `NVIDIA_API_KEY=nvapi-xxxx`
4. Use `openai` Python SDK with `base_url="https://integrate.api.nvidia.com/v1"`

---

## Project Folder Structure

```
C:\Users\Administrator\Desktop\BAM\
├── Brand Association Maps/          # Original data files (read-only)
│   ├── Input_Data_1.xlsx
│   ├── Input_Data_2.xlsx
│   ├── Rawdata_ref.xlsx
│   ├── Bigram tagging_taxonomy.xlsx
│   ├── monogram tagging_taxonomy.xlsx
│   └── R_Code Block (for reference).R
├── src/                             # [NEW] Pipeline source code
│   ├── __init__.py
│   ├── config_loader.py             # Load and validate client JSON config
│   ├── cleaner.py                   # Text cleaning and lemmatisation
│   ├── bigrams.py                   # Bigram generation and filtering
│   ├── taxonomy.py                  # 3-pass taxonomy mapper
│   ├── sentiment.py                 # Sentiment mapping and aggregation
│   ├── association.py               # Association scoring (IQR + matrix)
│   ├── output_writer.py             # Multi-sheet Excel output with formatting
│   └── ai_taxonomy.py              # [MVP2] AI taxonomy generator via NVIDIA NIM
├── config/                          # [NEW] Client configurations
│   └── jlr.json                     # JLR/Jaguar reference config
├── tests/                           # [NEW] Test scripts
│   └── test_pipeline.py             # End-to-end validation against R output
├── output/                          # [NEW] Generated output files
├── .env                             # [NEW] API keys (NVIDIA_API_KEY)
├── requirements.txt                 # [NEW] Python dependencies
├── bam.py                           # [NEW] Main CLI entry point
└── BAM_context.md                   # Context file (already created)
```

---

## Module-by-Module Build Specification

### Module 1: `requirements.txt`

```
pandas>=2.0
openpyxl>=3.1
spacy>=3.8
nltk>=3.9
numpy>=1.24
scipy>=1.10
python-dotenv>=1.0
openai>=1.0
```

After creating, run: `pip install -r requirements.txt`  
Also ensure: `python -m spacy download en_core_web_sm`  
Also ensure NLTK data: `nltk.download('stopwords')`, `nltk.download('punkt')`, `nltk.download('punkt_tab')`

---

### Module 2: `config/jlr.json`

This is the client-specific configuration. All hardcoded R regex rules become entries here.

```json
{
  "client": "JLR",
  "brand": "Jaguar",
  "input_files": {
    "data": ["Input_Data_1.xlsx", "Input_Data_2.xlsx"],
    "bigram_taxonomy": "Bigram tagging_taxonomy.xlsx",
    "monogram_taxonomy": "monogram tagging_taxonomy.xlsx"
  },
  "message_filters": [
    ".*west bank.*", ".*follow autoeuroland.*", ".*kfc / reliance digital.*",
    ".*harga paket khusus kredit.*", ".*credit broker.*", ".*otr kredit.*",
    ".*menlo park.*", ".*tag friend.*", ".*dar es salaam.*", ".*senate inquiry.*",
    ".*email address.*", ".*view attachment.*", ".*meet goals.*",
    ".*call.*", ".*email.*", ".*wechat.*", ".*whatsapp.*", ".*we chat.*"
  ],
  "bigram_filters": [
    ".*landrover.*", ".*insta.*", ".*thank.*", ".*car.*", ".*vehicle.*",
    ".*life.*", ".*photo.*", ".*youtube.*", ".*hyundai.*", ".*defender.*",
    ".*xx.*", ".*rover.*", ".*reel.*", ".*twitter.*", ".*pic.*",
    ".*mahindra.*", ".*tarmac.*", ".*america.*", ".*microsoft.*",
    ".*lego.*", ".*image.*", ".*quote.*", ".*biggboss.*", ".*ever.*",
    ".*put.*", ".*click.*", ".*seem.*", ".*comment.*", ".*thing.*",
    ".*scale.*", ".*craw.*", ".*rolls.*", ".*gts.*", ".*viper.*", ".*gclass.*"
  ],
  "custom_stopwords": [
    "http", "https", "www", "com", "org", "still", "version", "statement",
    "sale", "start", "come", "thanks", "auto", "near", "land", "rover",
    "new", "will", "range", "one", "like", "can", "many", "lti", "suv",
    "good", "just", "series", "now", "road", "day", "tdi", "also", "time",
    "get", "option", "rear", "work", "nan", "use", "take", "great", "video",
    "beautiful", "color", "way", "add", "love", "photos", "game", "see",
    "buy", "first", "reel", "have", "make", "year", "know", "thing", "think",
    "only", "without", "inch", "need", "let", "project", "always", "shop",
    "thar", "area", "include", "pack", "say", "follow", "today", "super",
    "brand", "little", "don", "show", "big", "find", "part", "may", "much",
    "even", "two", "available", "long", "back", "every", "around", "currently",
    "small", "keep", "light", "owner", "another", "bite", "post", "really",
    "old", "want", "last", "full", "landy", "next", "ready", "sell", "edition",
    "end", "mile", "offer", "please", "fit", "week", "body", "lot", "scale",
    "front", "customer", "feel", "give", "happy", "diecast", "mean", "test",
    "list", "viral", "lift", "high", "top", "review", "change", "people",
    "trend", "cool", "runner", "standard", "far", "since", "doesn", "yes",
    "though", "free", "svr", "didn", "actually", "name", "etc", "hello",
    "originally", "ago", "guy", "maybe", "probably"
  ],
  "bigram_normalizations": {
    ".*offroad.*": "offroad",
    ".*overland.*": "overland",
    ".*camp.*": "camp",
    ".*travel.*": "travel",
    ".*adventur.*": "adventure",
    ".*love.*": "love",
    ".*roadtrip.*": "roadtrip",
    ".*seat.*": "seat",
    ".*electric.*": "electric",
    ".*classic.*": "classic",
    ".*noisey.*": "noise",
    ".*explor.*": "explore"
  },
  "car_brands_to_remove": [],
  "min_word_length": 3
}
```

---

### Module 3: `src/config_loader.py`

**Purpose:** Load and validate the client JSON config.

**Specification:**
- Function `load_config(config_path: str) -> dict` — reads JSON, validates required keys exist
- Required keys: `client`, `brand`, `input_files`, `message_filters`, `bigram_filters`, `custom_stopwords`, `bigram_normalizations`, `min_word_length`
- Raise `ValueError` with clear message if any key is missing
- Return the parsed dict

---

### Module 4: `src/cleaner.py`

**Purpose:** Text cleaning and lemmatisation. Mirrors R code lines 21–67.

**Specification:**

**Function `clean_messages(df: DataFrame, config: dict) -> DataFrame`:**
1. Input: DataFrame with columns `[SocialNetwork, Message, Sentiment]`
2. Lowercase all `Message` text
3. Apply each regex in `config["message_filters"]` — if message matches, replace entire message with empty string
4. Strip punctuation: `re.sub(r'[^\w\s]', ' ', text)`
5. Strip non-alphabetic: `re.sub(r'[^a-zA-Z\s]', ' ', text)`
6. Collapse repeated chars (3+): `re.sub(r'([a-zA-Z])\1{2,}', r'\1', text)`
7. Drop rows where Message is NaN or empty string after cleaning
8. Normalise Sentiment to uppercase (`POSITIVE` / `NEGATIVE`)
9. Return cleaned DataFrame

**Function `lemmatize_messages(messages: Series) -> Series`:**
1. Load spaCy `en_core_web_sm`
2. Process each message through spaCy pipeline
3. Return series of lemmatised strings (join token lemmas with space)
4. Fallback: if spaCy fails to load, return messages as-is with a warning

---

### Module 5: `src/bigrams.py`

**Purpose:** Generate, filter, sort, and count bigrams. Mirrors R code lines 72–275.

**Specification:**

**Function `generate_bigrams(messages: Series, config: dict) -> DataFrame`:**
1. Tokenise each message into bigrams using sliding window (word[i], word[i+1])
2. Apply bigram-level filters from `config["bigram_filters"]` — remove any bigram where either word matches a filter regex
3. Remove NLTK English stopwords + `config["custom_stopwords"]`
4. Remove bigrams where either word is numeric-only (`str.isnumeric()`)
5. Remove bigrams where either word has length <= `config["min_word_length"]` (default 2, keep >2)
6. Remove country names (use a hardcoded list or `pycountry` if available)
7. Remove city names (hardcoded list from R code — ~80 cities)
8. Remove car brands from `config["car_brands_to_remove"]`
9. Apply normalizations from `config["bigram_normalizations"]` — for each regex→replacement pair, apply to both word1 and word2
10. **Sort each bigram pair alphabetically** (`word1, word2 = sorted([w1, w2])`)
11. Count frequency of each unique (word1, word2) pair
12. Remove pairs where word1 == word2
13. Return DataFrame with columns: `[word1, word2, n]` sorted by `n` descending

---

### Module 6: `src/taxonomy.py`

**Purpose:** 3-pass taxonomy mapping. Mirrors R code lines 283–329.

**Specification:**

**Function `load_taxonomies(config: dict, data_dir: str) -> tuple[DataFrame, DataFrame]`:**
1. Load bigram taxonomy Excel: columns `[Attribute - T1, Attribute - T2, Attribute - T3, Attribute - T4, word1, word2]`
2. Load monogram taxonomy Excel: columns `[Attribute - T1, Attribute - T2, Attribute - T3, Attribute - T4, word]`
3. **Normalise taxonomy data:** `.str.strip()` on all Attribute columns, fix casing (`Brand love` → `Brand Love`)
4. Sort bigram taxonomy words alphabetically per row (same as bigram generation)
5. Create a `Key` column: `word1 + "_" + word2`
6. Return both DataFrames

**Function `map_taxonomy(bigram_counts: DataFrame, bigram_tax: DataFrame, mono_tax: DataFrame) -> tuple[DataFrame, DataFrame]`:**
1. Create `Key` on bigram_counts: `word1 + "_" + word2`
2. **Pass 1:** Left-merge bigram_counts with bigram_tax on `Key`. Rows that get T1 values are "tagged"
3. **Pass 2:** Take untagged rows (T1 is NaN). Merge on `word1` against monogram taxonomy's `word` column
4. **Pass 3:** Still-untagged rows. Merge on `word2` against monogram taxonomy's `word` column
5. Combine all tagged rows from passes 1, 2, 3 into `tagged_df`
6. Remaining untagged rows become `untagged_df`
7. Return `(tagged_df, untagged_df)` — tagged_df has columns: `[Attribute - T1, T2, T3, T4, word1, word2, n]`

---

### Module 7: `src/sentiment.py`

**Purpose:** Map bigrams back to source messages to capture sentiment per bigram. Mirrors R code lines 356–609.

**Specification:**

**Function `map_sentiment(source_df: DataFrame, bigram_counts: DataFrame) -> DataFrame`:**
1. Clean source_df messages (lowercase, strip punctuation, strip non-alpha, trim whitespace)
2. Create bigram dictionary from bigram_counts with both word orders for matching:
   - Forward: `word1_word2`
   - Reverse: `word2_word1`
3. For each source message, extract bigrams and check membership against dictionary
4. Tag each message with list of matching bigram keys
5. Explode: one row per (message_id, bigram_key, sentiment)
6. Split bigram_key back into word1, word2. Sort alphabetically.
7. Group by (word1, word2, Sentiment) → count
8. Pivot to get columns: `[word1, word2, Positive, Negative, Total, Positive_perc, Negative_perc]`
9. Handle NaN in percentages → fill with 0
10. Return sentiment DataFrame

---

### Module 8: `src/association.py`

**Purpose:** Compute association scoring at all hierarchy levels. Mirrors R code lines 616–1025.

**Specification:**

**Function `compute_association(df: DataFrame, mention_col: str = "Total") -> DataFrame`:**
1. Compute IQR quartiles on `mention_col`: Q1 (25th), Q2 (50th), Q3 (75th)
2. **Mentions_association:**
   - `>= Q3` → "Strong"
   - `> Q2 and <= Q3` → "Moderate"
   - `> Q1 and <= Q2` → "Weak"
   - `<= Q1` → "Negligible"
3. **Sentiment_association** (from `Positive_perc`):
   - `>= 80` → "Strong"
   - `>= 50 and < 80` → "Moderate"
   - `>= 20 and < 50` → "Weak"
   - `< 20` → "Negligible"
4. **Overall Association** — 4×4 matrix:

| Mentions ↓ / Sentiment → | Strong | Moderate | Weak | Negligible |
|---|---|---|---|---|
| **Strong** | Strong | Moderate | Weak | Weak |
| **Moderate** | Strong | Moderate | Weak | Weak |
| **Weak** | Moderate | Moderate | Weak | Negligible |
| **Negligible** | Moderate | Weak | Weak | Negligible |

5. Add columns: `Mentions_association`, `Sentiment_association`, `Association`
6. Return enriched DataFrame

**Function `aggregate_and_score(tagged_df: DataFrame, levels: list[str]) -> DataFrame`:**
1. Group by the specified attribute columns (e.g., `["Attribute - T1", "Attribute - T2"]` for T2-level)
2. Sum `Total` (mentions), compute mean `Positive_perc`
3. Call `compute_association()` on the aggregated data — **GLOBAL IQR**
4. Also compute **per-T1 IQR** (group by `Attribute - T1`, recalculate quartiles within each T1 group)
5. Add second set of columns: `Mentions_association1`, `Sentiment_association1`, `Association1`
6. Return result

**Output calls (in main pipeline):**
- Word level: `compute_association(merged_df)` → `output_wordlevel.xlsx`
- T4 level: `aggregate_and_score(df, ["Attribute - T1", "Attribute - T2", "Attribute - T3", "Attribute - T4"])`
- T3 level: `aggregate_and_score(df, ["Attribute - T1", "Attribute - T2", "Attribute - T3"])`
- T2 level: `aggregate_and_score(df, ["Attribute - T1", "Attribute - T2"])`

---

### Module 9: `src/output_writer.py`

**Purpose:** Write formatted multi-sheet Excel output.

**Specification:**

**Function `write_output(results: dict, output_dir: str, client_name: str)`:**
1. `results` is a dict: `{"word_level": df, "t4": df, "t3": df, "t2": df, "untagged": df}`
2. Create output filename: `{client_name}_BAM_output_{date}.xlsx`
3. Write each DataFrame as a separate sheet using openpyxl
4. Apply formatting: bold headers, auto-column-width, freeze top row
5. Also write `{client_name}_untagged_bigrams.xlsx` separately for analyst review

---

### Module 10: `src/ai_taxonomy.py` (MVP 2 — AI Taxonomy Generator)

**Purpose:** Given raw bigrams that have NO existing taxonomy, use NVIDIA NIM to generate T1→T4 classifications.

**Specification:**

**Function `generate_taxonomy_suggestions(untagged_df: DataFrame, existing_taxonomy: DataFrame, client_name: str, brand_context: str) -> DataFrame`:**

1. Load API key from `.env` (`NVIDIA_API_KEY`)
2. Initialise OpenAI client:
   ```python
   from openai import OpenAI
   client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)
   ```
3. Extract unique T1, T2, T3, T4 values from `existing_taxonomy` to use as reference anchors
4. Batch untagged bigrams into groups of 50 (to stay within context window)
5. For each batch, send a Chat Completion request:

   **Model:** `nvidia/llama-3.1-nemotron-ultra-253b-v1`  
   **Temperature:** 0.2 (low for consistency)  
   **System prompt:**
   ```
   You are an expert brand analyst performing Brand Association Mapping.
   Your task is to classify bigrams (word pairs) extracted from social media 
   conversations about {brand_context} into a 4-level taxonomy.

   REASONING MODE: ON — Think step by step before classifying each bigram. 
   Consider what the word pair means in the context of brand perception.

   EXISTING TAXONOMY REFERENCE (use these categories when applicable):
   T1 (Pillars): {list of unique T1 values}
   T2 (Themes): {list of unique T2 values}  
   T3 (Attributes): {list of unique T3 values}
   T4 (Details): {list of unique T4 values}

   RULES:
   - Reuse existing categories whenever the bigram fits
   - Only create NEW categories if no existing one is appropriate
   - New T1 categories should be rare (brands typically have 2-5 pillars)
   - T4 should be the most specific — it can be the bigram itself if no better label exists
   - If a bigram is genuinely irrelevant noise, classify T1 as "NOISE"

   OUTPUT FORMAT: Return ONLY a JSON array, no other text:
   [
     {"word1": "...", "word2": "...", "t1": "...", "t2": "...", "t3": "...", "t4": "..."},
     ...
   ]
   ```

   **User prompt:** The batch of bigrams as a JSON list: `[{"word1": "x", "word2": "y"}, ...]`

6. Parse JSON response. If parsing fails, retry with `deepseek-ai/deepseek-r1` as fallback.
7. Combine all batches into a single DataFrame matching the taxonomy schema
8. Save as `{client_name}_ai_suggested_taxonomy.xlsx` for analyst review
9. Return the DataFrame

**Function `apply_approved_taxonomy(suggestions_path: str, existing_taxonomy_path: str) -> str`:**
1. Read analyst-approved suggestions Excel
2. Filter out rows where T1 == "NOISE"
3. Append to existing taxonomy file
4. Save updated taxonomy
5. Return path to updated file

---

### Module 11: `bam.py` (Main CLI Entry Point)

**Purpose:** Orchestrate the full pipeline.

**Specification:**

```
Usage:
  python bam.py --config config/jlr.json --data-dir "Brand Association Maps" --output output/
  python bam.py --config config/jlr.json --data-dir "Brand Association Maps" --output output/ --generate-taxonomy
```

**Flow:**
1. Parse CLI args (argparse): `--config`, `--data-dir`, `--output`, `--generate-taxonomy` (flag)
2. Load config via `config_loader.load_config()`
3. Read input Excel files and concatenate into single DataFrame
4. Run `cleaner.clean_messages()` and `cleaner.lemmatize_messages()`
5. Run `bigrams.generate_bigrams()`
6. Load taxonomies via `taxonomy.load_taxonomies()`
7. Run `taxonomy.map_taxonomy()` → get tagged + untagged DataFrames
8. **If `--generate-taxonomy` flag is set AND untagged bigrams exist:**
   - Run `ai_taxonomy.generate_taxonomy_suggestions()` on untagged bigrams
   - Print: "AI taxonomy suggestions saved to {path}. Review and re-run without --generate-taxonomy."
   - Exit here (human review step)
9. Run `sentiment.map_sentiment()` on source data using tagged bigrams
10. Merge tagged bigrams with sentiment data
11. Run `association.compute_association()` at word level
12. Run `association.aggregate_and_score()` at T4, T3, T2 levels
13. Run `output_writer.write_output()` to generate final Excel
14. Print summary: total bigrams, tagged %, association distribution, output file paths

---

## Test Strategy

### Validation Against R Output
1. Run the R code on Input_Data_1.xlsx and save all intermediate outputs as "golden" reference files
2. Run the Python pipeline on the same input
3. Compare:
   - **Bigram counts:** Total unique bigrams within ±5% of R output
   - **Taxonomy match rate:** ≥95% recall on T1 assignment
   - **Sentiment percentages:** ±2% deviation from R values
   - **Association labels:** Exact match on at least 90% of rows

### Test on Input_Data_2
- Run pipeline on Input_Data_2 (146 rows) to verify it handles small datasets
- This also tests config portability since Input_Data_2 has different sentiment casing (`Positive` vs `POSITIVE`)

### AI Taxonomy Test
- Take 100 random bigrams from the JLR untagged list
- Run through NVIDIA NIM
- Manually verify that ≥80% of suggestions are reasonable classifications

---

## Build Order (for Gemini to execute)

> [!IMPORTANT]
> Build and test each module **in this exact order**. Each module depends on the previous ones.

| Step | Module | Test |
|---|---|---|
| 1 | `requirements.txt` + folder structure | Verify imports work |
| 2 | `config/jlr.json` + `src/config_loader.py` | Load config, print client name |
| 3 | `src/cleaner.py` | Clean Input_Data_1, print row count before/after |
| 4 | `src/bigrams.py` | Generate bigrams, print top 20 by frequency |
| 5 | `src/taxonomy.py` | Map taxonomy, print tagged vs untagged counts |
| 6 | `src/sentiment.py` | Map sentiment, print sample Positive/Negative counts |
| 7 | `src/association.py` | Score associations, print distribution of Strong/Moderate/Weak/Negligible |
| 8 | `src/output_writer.py` | Write Excel, verify file opens correctly |
| 9 | `bam.py` | End-to-end CLI run on Input_Data_1 |
| 10 | `src/ai_taxonomy.py` | Test with 10 sample bigrams against NVIDIA NIM API |
| 11 | Full validation | Compare Python output vs R golden output |

---

## Open Questions for User

1. **NVIDIA API Key:** Do you already have an NVIDIA developer account / API key, or should the plan include a setup step for obtaining one?
2. **R Golden Output:** Do you have the actual R-generated Excel outputs (e.g., `Jag_output_wordlevel_2025.xlsx`) available for comparison testing, or should we generate them first?
3. **AI Taxonomy Scope for MVP:** Should the AI taxonomy generator run automatically on all untagged bigrams during every pipeline run, or should it be a separate manual step (the `--generate-taxonomy` flag approach described above)?
