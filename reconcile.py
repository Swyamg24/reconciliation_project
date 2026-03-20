import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime
import os
def generate_sample_ledgers():
    print("Generating sample ledger data...")
    fake = Faker()
    if not os.path.exists('data'):
        os.makedirs('data')

    num_base_transactions = 100
    data = []
    for i in range(num_base_transactions):
        data.append({
            'TransactionID':f'TXN{1000+i}',
            'Date':fake.date_between(start_date='-30d',end_date='today'),
            'Description':fake.catch_phrase(),
            'Amount':round(random.uniform(10.50,500.99),2)
        })
    base_df = pd.DataFrame(data)
    internal_ledger = base_df.iloc[:105].copy()
    bank_statement = base_df.iloc[:100].copy()
    bank_statement = pd.concat([bank_statement, base_df.iloc[105:]], ignore_index=True)
    mismatch_indices = random.sample(range(100), 3)
    for idx in mismatch_indices:
        bank_statement.loc[idx, 'Amount'] += round(random.uniform(0.01, 1.50), 2)

    duplicate_indices = random.sample(range(100), 2)
    duplicates = bank_statement.iloc[duplicate_indices]
    bank_statement = pd.concat([bank_statement, duplicates], ignore_index=True)

    bank_statement = bank_statement.sample(frac=1).reset_index(drop=True)

    internal_ledger.to_csv('data/internal_ledger.csv', index=False)
    bank_statement.to_csv('data/bank_statement.csv', index=False)

    print("Sample ledgers 'internal_ledger.csv' and 'bank_statement.csv' created in 'data/' folder.\n")

def reconcile():
    print("Loading and pre-processing data...")
    try:
        internal_df = pd.read_csv('data/internal_ledger.csv')
        bank_df = pd.read_csv('data/bank_statement.csv')
    except FileNotFoundError:
        print("Error: CSV files not found. Please run generate_sample_ledgers() first.")
        return
    
    internal_df['Date'] = pd.to_datetime(internal_df['Date'])
    bank_df['Date'] = pd.to_datetime(bank_df['Date'])
    
    internal_df['Amount'] = pd.to_numeric(internal_df['Amount'])
    bank_df['Amount'] = pd.to_numeric(bank_df['Amount'])

    internal_df.dropna(how='all', inplace=True)
    bank_df.dropna(how='all', inplace=True)
    
    print("Data loaded successfully.")

    print("Performing reconciliation...")

    internal_ids = set(internal_df['TransactionID'])
    bank_ids = set(bank_df['TransactionID'])

    missing_from_bank_ids = internal_ids - bank_ids
    missing_from_bank_df = internal_df[internal_df['TransactionID'].isin(missing_from_bank_ids)]

    missing_from_internal_ids = bank_ids - internal_ids
    missing_from_internal_df = bank_df[bank_df['TransactionID'].isin(missing_from_internal_ids)]

    merged_df = pd.merge(internal_df, bank_df, on='TransactionID', how='inner', suffixes=('_internal', '_bank'))

    mismatched_amounts_df = merged_df[~np.isclose(merged_df['Amount_internal'], merged_df['Amount_bank'])]

    duplicates_in_bank_df = bank_df[bank_df.duplicated(subset=['TransactionID'], keep=False)].sort_values('TransactionID')

    print("Reconciliation complete.\n")

    print("Reconciliation Report")
    print("=====================")
    print(f"Total Transactions in Internal Ledger: {len(internal_df)}")
    print(f"Total Transactions in Bank Statement: {len(bank_df)}")
    print("\nDiscrepancies Found:")
    print("--------------------")
    print(f"- {len(missing_from_bank_df)} transactions missing from Bank Statement.")
    print(f"- {len(missing_from_internal_df)} transactions in Bank Statement not found in Internal Ledger.")
    print(f"- {len(mismatched_amounts_df)} transactions with mismatched amounts.")
    print(f"- {int(len(duplicates_in_bank_df)/2)} duplicate transactions found in Bank Statement.") 

    report_filename = 'reconciliation_report.xlsx'
    print(f"\nGenerating Excel report: {report_filename}...")
    with pd.ExcelWriter(report_filename, engine='openpyxl') as writer:
        missing_from_bank_df.to_excel(writer, sheet_name='Missing_from_Bank', index=False)
        missing_from_internal_df.to_excel(writer, sheet_name='Missing_from_Internal', index=False)
        mismatched_amounts_df.to_excel(writer, sheet_name='Mismatched_Amounts', index=False)
        duplicates_in_bank_df.to_excel(writer, sheet_name='Duplicates_in_Bank', index=False)

        print("Report generated successfully.")

if __name__ == "__main__":
    generate_sample_ledgers()
    reconcile()
