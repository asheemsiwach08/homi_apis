
import pandas as pd
import numpy as np

def get_data_from_csv(csv_file_path):
    df = pd.read_csv(csv_file_path)
    return df.to_dict(orient="records")


# Fill bankAppId missing values with loanAccountNumber
def fill_bankappid_missing_values(df):
    filterd_df = df[df['bankAppId'].isin(["Not Found", "Not found"])]
    # Replace bankAppId with loanAccountNumber
    df.loc[filterd_df.index, 'bankAppId'] = filterd_df['loanAccountNumber']
    return df

def count_non_empty_values(row):
    """Count non-empty and non-'Not found' values in a row"""
    return sum(1 for value in row if pd.notna(value) and value != 'Not found' and value != '')

def filter_and_deduplicate_csv(df):
    """
    Filter CSV to specified columns and remove duplicates keeping records with maximum data.
    Returns the full rows (with all original columns) after deduplication.
    
    Args:
        df (pandas.DataFrame): Input dataframe to process
        
    Returns:
        pandas.DataFrame: Deduplicated dataframe with all original columns
    """    
    # Define the columns to keep for deduplication logic
    columns_to_keep = ['firstName', 'lastName', 'loanAccountNumber', 'disbursedOn', 
                      'sanctionDate', 'disbursementAmount', 'bankAppId']
    
    # Check which columns exist in the dataframe
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    missing_columns = [col for col in columns_to_keep if col not in df.columns]
    
    if missing_columns:
        print(f"Warning: The following columns are missing from the CSV: {missing_columns}")
    
    # Create a working copy with only the columns needed for deduplication
    df_work = df[existing_columns].copy()
    
    # Remove rows where bankAppId is missing or 'Not found'
    df_work = df_work.dropna(subset=['bankAppId'])
    df_work = df_work[df_work['bankAppId'] != 'Not found']
    
    # Count non-empty values for each row
    df_work['data_completeness'] = df_work.apply(count_non_empty_values, axis=1)
    
    # Find duplicates based on bankAppId
    duplicates = df_work[df_work.duplicated(subset=['bankAppId'], keep=False)]
    
    if not duplicates.empty:
        print(f"Found {len(duplicates)} duplicate records based on bankAppId")
        # For each group of duplicates, keep the one with maximum data completeness
        best_indices = df_work.groupby('bankAppId')['data_completeness'].idxmax()
        df_deduplicated_work = df_work.loc[best_indices]
    else:
        print("No duplicates found")
        df_deduplicated_work = df_work
    
    # Remove the temporary data_completeness column
    df_deduplicated_work = df_deduplicated_work.drop('data_completeness', axis=1)
    
    # Get the corresponding full rows from the original dataframe
    # using the indices from the deduplicated working dataframe
    final_df = df.loc[df_deduplicated_work.index].copy()
    
    print(f"Deduplication complete. Kept {len(final_df)} records out of {len(df)} original records")
    print(f"Final dataframe has {len(final_df.columns)} columns: {list(final_df.columns)}")
    
    # Save the deduplicated data with all original columns
    final_df.to_excel(r"D:\Projects\basicVerify\tests\test_results\analysis_results.xlsx", sheet_name="Sheet2", index=False)
    
    return final_df

