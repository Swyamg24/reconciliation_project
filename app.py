from flask import Flask, render_template, request, send_file, abort
import pandas as pd
import io

app = Flask(__name__)

# -------------------------------
# In-memory storage (temporary)
# -------------------------------
class DataStore:
    results = None


# -------------------------------
# Utility Functions
# -------------------------------
def load_data(ledger_file, bank_file):
    """Load CSV files into pandas DataFrames."""
    try:
        df_ledger = pd.read_csv(ledger_file)
        df_bank = pd.read_csv(bank_file)
        return df_ledger, df_bank
    except Exception as e:
        raise ValueError(f"Error reading CSV files: {str(e)}")


def reconcile_data(df_ledger, df_bank):
    """Perform reconciliation logic and return results."""

    missing_from_bank = df_ledger[
        ~df_ledger["TransactionID"].isin(df_bank["TransactionID"])
    ]

    missing_from_ledger = df_bank[
        ~df_bank["TransactionID"].isin(df_ledger["TransactionID"])
    ]

    merged = pd.merge(
        df_ledger,
        df_bank,
        on="TransactionID",
        suffixes=("_ledger", "_bank")
    )

    mismatched_amounts = merged[
        merged["Amount_ledger"] != merged["Amount_bank"]
    ]

    duplicates_in_bank = df_bank[
        df_bank.duplicated(subset=["TransactionID"], keep=False)
    ]

    return {
        "missing_from_bank": missing_from_bank,
        "missing_from_ledger": missing_from_ledger,
        "mismatched_amounts": mismatched_amounts,
        "duplicates_in_bank": duplicates_in_bank
    }


def generate_excel(results):
    """Generate Excel file in memory."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        results["missing_from_bank"].to_excel(
            writer, sheet_name="Missing from Bank", index=False
        )
        results["missing_from_ledger"].to_excel(
            writer, sheet_name="Missing from Ledger", index=False
        )
        results["mismatched_amounts"].to_excel(
            writer, sheet_name="Mismatched Amounts", index=False
        )
        results["duplicates_in_bank"].to_excel(
            writer, sheet_name="Duplicates in Bank", index=False
        )

    output.seek(0)
    return output


# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    # Validate file inputs
    if "internal_ledger" not in request.files or "bank_statement" not in request.files:
        return abort(400, "Both files are required")

    ledger_file = request.files["internal_ledger"]
    bank_file = request.files["bank_statement"]

    if ledger_file.filename == "" or bank_file.filename == "":
        return abort(400, "No file selected")

    try:
        # Load data
        df_ledger, df_bank = load_data(ledger_file, bank_file)

        # Reconcile
        results = reconcile_data(df_ledger, df_bank)

        # Store results
        DataStore.results = results

        # Prepare summary
        summary = {
            "ledger_count": len(df_ledger),
            "bank_count": len(df_bank),
            "missing_from_bank": len(results["missing_from_bank"]),
            "missing_from_internal": len(results["missing_from_ledger"]),
            "mismatched_amounts": len(results["mismatched_amounts"]),
            "duplicates_in_bank": results["duplicates_in_bank"]["TransactionID"].nunique()
        }

        return render_template("result.html", **summary)

    except Exception as e:
        return abort(500, f"Processing error: {str(e)}")


@app.route("/download")
def download():
    if DataStore.results is None:
        return abort(400, "No data available. Please run analysis first.")

    try:
        output = generate_excel(DataStore.results)

        return send_file(
            output,
            download_name="Reconciliation_Report.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return abort(500, f"Download error: {str(e)}")


# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)