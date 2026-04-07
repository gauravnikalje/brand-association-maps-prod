import pandas as pd

def main():
    file_path = r"C:\Users\Administrator\Desktop\BAM\BAM_output_52a4c94d.xlsx"
    print(f"Reading {file_path} using pandas...")
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        print("Successfully read the Excel file.")
        print("\nData Overview:")
        print(f"Total rows: {len(df)}")
        print(f"Columns: {', '.join(df.columns.tolist())}")
        
        print("\nFirst 5 rows:")
        print(df.head())
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")

if __name__ == "__main__":
    main()
