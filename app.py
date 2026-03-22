from flask import Flask, render_template, request, send_file
import pandas as pd
import io # New import for memory buffering

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate():
    # 1. EXTRACT
    ledger_file = request.files["internal_ledger"]
    bank_file = request.files["bank_statement"]

    # 2. EXECUTE: Load data
    df_ledger = pd.read_csv(ledger_file)
    df_bank = pd.read_csv(bank_file)

    # --- RECONCILIATION LOGIC ---
    missing_from_bank_df = df_ledger[~df_ledger["TransactionID"].isin(df_bank["TransactionID"])]
    missing_from_internal_df = df_bank[~df_bank["TransactionID"].isin(df_ledger["TransactionID"])]
    
    merged_df = pd.merge(df_ledger, df_bank, on="TransactionID", suffixes=("_ledger", "_bank"))
    mismatched_amounts_df = merged_df[merged_df["Amount_ledger"] != merged_df["Amount_bank"]]
    
    duplicates_in_bank_df = df_bank[df_bank.duplicated(subset=["TransactionID"], keep=False)]

    # --- NEW FEATURE: EXCEL GENERATION ---
    # We check if the user clicked a "Download" button or just "View Results"
    if "download" in request.form:
        # Create an in-memory output file for the library to write to
        output = io.BytesIO()
        
        # Initialize the writer with the memory buffer
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            missing_from_bank_df.to_excel(writer, sheet_name="Missing from Bank", index=False)
            missing_from_internal_df.to_excel(writer, sheet_name="Missing from Ledger", index=False)
            mismatched_amounts_df.to_excel(writer, sheet_name="Mismatched Amounts", index=False)
            duplicates_in_bank_df.to_excel(writer, sheet_name="Duplicates in Bank", index=False)
        
        # Seek to the beginning of the file so Flask reads it from the start
        output.seek(0)
        
        return send_file(
            output,
            download_name="Reconciliation_Report.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 3. RESPOND: Standard HTML view
    return render_template("result.html",
                           ledger_count=len(df_ledger),
                           bank_count=len(df_bank),
                           missing_from_bank=len(missing_from_bank_df),
                           missing_from_internal=len(missing_from_internal_df),
                           mismatched_amounts=len(mismatched_amounts_df),
                           duplicates_in_bank=int(len(duplicates_in_bank_df) / 2))

if __name__ == "__main__":
    app.run(debug=True)