import pandas as pd
import json
import argparse
import os

def excel_to_json(excel_file, json_file):
    """
    Convert Excel file to JSON format.
    Column A will be used as 'intput' and Column B as 'output' values.
    """
    # Check if the Excel file exists
    if not os.path.exists(excel_file):
        print(f"Error: The file {excel_file} does not exist.")
        return
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Check if the dataframe has at least 2 columns
        if df.shape[1] < 2:
            print("Error: The Excel file should have at least 2 columns.")
            return
        
        # Convert to list of dictionaries
        data = []
        for _, row in df.iterrows():
            input_val = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            output_val = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            
            data.append({
                "input": input_val,  # Using "intput" as specified in the example
                "output": output_val
            })
        
        # Write to JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully converted {excel_file} to {json_file}")
        print(f"Processed {len(data)} records.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert Excel to JSON')
    parser.add_argument('excel_file', help='Path to the Excel file')
    parser.add_argument('json_file', help='Path to save the JSON file')
    
    args = parser.parse_args()
    excel_to_json(args.excel_file, args.json_file)
