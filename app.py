from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# --- ROUTE 1: THE INTAKE ---
@app.route("/")
def home():
    return render_template("index.html")

# --- ROUTE 2: THE INTERCEPTION ---
@app.route("/calculate", methods=["POST"])
def calculate():
    # 1. EXTRACT: Use request.files instead of request.form
    ledger_file = request.files["internal_ledger"]
    bank_file = request.files["bank_statement"]

    # 2. EXECUTE: Read the raw files directly into Pandas DataFrames.
    df_ledger = pd.read_csv(ledger_file)
    df_bank = pd.read_csv(bank_file)

    # --- RECONCILIATION LOGIC ---

    # Transactions missing from Bank Statement
    missing_from_bank_df = df_ledger[~df_ledger["TransactionID"].isin(df_bank["TransactionID"])]

    # Transactions in Bank Statement not found in Internal Ledger
    missing_from_internal_df = df_bank[~df_bank["TransactionID"].isin(df_ledger["TransactionID"])]

    # Transactions with mismatched amounts (present in both but different amount)
    merged_df = pd.merge(df_ledger, df_bank, on="TransactionID", suffixes=("_ledger", "_bank"))
    mismatched_amounts_df = merged_df[merged_df["Amount_ledger"] != merged_df["Amount_bank"]]

    # Duplicate transactions in Bank Statement
    duplicates_in_bank_df = df_bank[df_bank.duplicated(subset=["TransactionID"], keep=False)]

    # 3. RESPOND: Pass all reconciliation data to the results page.
    return render_template("result.html",
                           ledger_count=len(df_ledger),
                           bank_count=len(df_bank),
                           missing_from_bank=len(missing_from_bank_df),
                           missing_from_internal=len(missing_from_internal_df),
                           mismatched_amounts=len(mismatched_amounts_df),
                           duplicates_in_bank=int(len(duplicates_in_bank_df) / 2))

if __name__ == "__main__":
    app.run(debug=True)