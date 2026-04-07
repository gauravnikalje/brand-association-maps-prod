import pandas as pd

def main():
    file_my_output = r"C:\Users\Administrator\Desktop\BAM\BAM_output_52a4c94d.xlsx"
    file_actual = r"C:\Users\Administrator\Desktop\BAM\output\JLR_BAM_output_2026_04_05.xlsx"
    
    df_my = pd.read_excel(file_my_output).sort_values(['word1', 'word2']).reset_index(drop=True)
    df_actual = pd.read_excel(file_actual).sort_values(['word1', 'word2']).reset_index(drop=True)
    
    # Merge using outer join to see what's missing
    merged = pd.merge(df_my, df_actual, on=['word1', 'word2'], how='outer', indicator=True)
    missing = merged[merged['_merge'] == 'right_only']
    
    print(f"Missing rows: {len(missing)}")
    if len(missing) > 0:
        print(missing[['word1', 'word2', 'n_actual']].head(15))

if __name__ == "__main__":
    main()
