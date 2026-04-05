import pandas as pd
import os
import logging
from datetime import datetime

def write_output(results: dict, output_dir: str, client_name: str):
    """
    Write BAM results to an Excel file with multiple sheets.
    
    Args:
        results: dict containing {"word_level": df, "t4": df, "t3": df, "t2": df, "untagged": df}
        output_dir: Output directory path.
        client_name: Project client/brand name.
    """
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y_%m_%d")
    
    main_output = os.path.join(output_dir, f"{client_name}_BAM_output_{date_str}.xlsx")
    untagged_output = os.path.join(output_dir, f"{client_name}_untagged_bigrams_{date_str}.xlsx")
    
    logging.info(f"Writing main output to {main_output}")
    
    try:
        with pd.ExcelWriter(main_output, engine="openpyxl") as writer:
            for sheet_name, df in results.items():
                if sheet_name == "untagged" or df is None or df.empty:
                    continue
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Setup autofit and format headers if possible
                worksheet = writer.sheets[sheet_name]
                for col in worksheet.columns:
                    max_length = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[col_letter].width = adjusted_width
                # Freeze top row
                worksheet.freeze_panes = "A2"
                
    except Exception as e:
        logging.error(f"Failed to write main output: {e}")
        
    untagged_df = results.get("untagged")
    if untagged_df is not None and not untagged_df.empty:
        logging.info(f"Writing untagged bigrams to {untagged_output}")
        try:
            untagged_df.to_excel(untagged_output, index=False)
        except Exception as e:
            logging.error(f"Failed to write untagged output: {e}")
            
    logging.info("Excel write completed.")
