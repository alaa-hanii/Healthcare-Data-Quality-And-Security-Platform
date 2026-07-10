import os
import pandas as pd

from ProcessingLayer.security import apply_security_pandas, apply_decryption_pandas, generate_key
from ServicesLayer.audit_service import log_action
from ServicesLayer.auth_service import get_user_role

INPUT_PATH  = "StorageLayer/LoadedData/"
OUTPUT_PATH = "StorageLayer/SecuredData/"
KEY_PATH    = "StorageLayer/Keys/encryption_key.txt"


def run_security():
    """
    Read CSVs from LoadedData, apply masking/encryption with pandas,
    write secured CSVs to SecuredData. No Spark write = no winutils needed.
    """
    try:
        # Generate key if missing
        if not os.path.exists(KEY_PATH):
            generate_key()

        os.makedirs(OUTPUT_PATH, exist_ok=True)

        if not os.path.exists(INPUT_PATH):
            return {"error": f"Input path not found: {INPUT_PATH}"}

        files = [f for f in os.listdir(INPUT_PATH) if f.endswith(".csv")]

        if not files:
            return {"error": "No CSV files found in LoadedData"}

        processed = []
        for file in files:
            path = os.path.join(INPUT_PATH, file)
            try:
                df = pd.read_csv(path)
                secured_df = apply_security_pandas(df)

                # Save directly as CSV — no Spark, no winutils
                out_path = os.path.join(OUTPUT_PATH, file)
                secured_df.to_csv(out_path, index=False)
                processed.append({"file": file, "rows": len(df), "cols": len(df.columns)})
                print(f"✓ Secured: {file}")
            except Exception as fe:
                print(f"⚠ Error processing {file}: {fe}")
                processed.append({"file": file, "error": str(fe)})

        log_action("system", "run_security")

        return {
            "status": "Security Applied",
            "files_processed": len(processed),
            "details": processed
        }

    except Exception as e:
        return {"error": str(e)}


def decrypt_data(username: str):
    role = get_user_role(username)
    if role != "doctor":
        return {"error": "Access Denied"}

    try:
        results = []
        for file in os.listdir(OUTPUT_PATH):
            if not file.endswith(".csv"):
                continue
            path = os.path.join(OUTPUT_PATH, file)
            try:
                df = pd.read_csv(path)
                df_dec = apply_decryption_pandas(df)
                results.append({
                    "file": file,
                    "data": df_dec.head(10).to_dict(orient="records")
                })
            except Exception as fe:
                results.append({"file": file, "error": str(fe)})

        log_action(username, "decrypt_data")
        return results

    except Exception as e:
        return {"error": str(e)}
