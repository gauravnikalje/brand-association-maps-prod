import json
import logging

REQUIRED_KEYS = [
    "client",
    "brand",
    "input_files",
    "message_filters",
    "bigram_filters",
    "custom_stopwords",
    "bigram_normalizations",
    "min_word_length"
]

def load_config(config_path: str) -> dict:
    """
    Load and validate client configuration.
    
    Args:
        config_path: Path to the JSON configuration file.
        
    Returns:
        dict: Parsed configuration dictionary.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {config_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON in {config_path}: {e}")
        raise

    missing_keys = [key for key in REQUIRED_KEYS if key not in config]
    if missing_keys:
        error_msg = f"Missing required configuration keys: {', '.join(missing_keys)}"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    logging.info(f"Loaded configuration for client: {config['client']} / {config['brand']}")
    return config
