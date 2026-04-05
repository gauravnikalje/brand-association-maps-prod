import os
import pandas as pd
from dotenv import load_dotenv
from src.ai_taxonomy import generate_taxonomy_suggestions

def test():
    load_dotenv()
    print("Testing NVIDIA API Key...")
    
    # Mock untagged data with just 2 bigrams
    df = pd.DataFrame([
        {"word1": "battery", "word2": "drain"},
        {"word1": "leather", "word2": "seat"}
    ])
    
    # Mock taxonomy
    existing_tax = pd.DataFrame({
        "Attribute - T1": ["Performance", "Comfort"],
        "Attribute - T2": ["Range Issues", "Interior Design"],
        "Attribute - T3": ["Battery", "Materials"],
        "Attribute - T4": ["Battery Life", "Upholstery"]
    })
    
    result = generate_taxonomy_suggestions(df, existing_tax, "TestClient", "Electric Vehicles", "output")
    print(result.to_json(orient='records', indent=2))

if __name__ == "__main__":
    test()
