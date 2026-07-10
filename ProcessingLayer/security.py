import os
import pandas as pd
from cryptography.fernet import Fernet

# =========================
# KEY MANAGEMENT
# =========================
KEY_PATH = "StorageLayer/Keys/encryption_key.txt"


def generate_key():
    key = Fernet.generate_key().decode()
    os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)
    with open(KEY_PATH, "w") as f:
        f.write(key)
    print("Key saved successfully ✓")


def load_key():
    with open(KEY_PATH, "r") as f:
        key = f.read().strip()
    return Fernet(key.encode())


# =========================
# CONFIG
# =========================
security_config = {
    "first_name":       "mask",
    "last_name":        "mask",
    "phone":            "mask",
    "street":           "mask",
    "city":             "mask",
    "state":            "mask",
    "postal_code":      "mask",
    "national_id":      "encrypt",
    "insurance_number": "encrypt",
    "salary":           "mask",
    "nurse_first_name": "mask",
    "nurse_last_name":  "mask",
    "diagnosis":        "encrypt",
    "hypertension":     "encrypt",
    "diabetes":         "encrypt",
    "handicap":         "encrypt",
    "dialysis":         "encrypt",
    "notes":            "mask",
    "total_cost":       "mask",
}


# =========================
# PANDAS-BASED OPERATIONS
# (no Spark UDFs — avoids Python worker timeout on Windows)
# =========================

def _mask(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    v = str(v)
    return v[:2] + "****" if len(v) > 2 else "****"


def _encrypt(cipher, v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return cipher.encrypt(str(v).encode()).decode()
    except Exception:
        return None


def _decrypt(cipher, v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return cipher.decrypt(str(v).encode()).decode()
    except Exception:
        return str(v)  # already decrypted or invalid


def apply_security_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """Apply masking and encryption to a pandas DataFrame."""
    cipher = load_key()
    df = df.copy()
    for col, method in security_config.items():
        if col in df.columns:
            if method == "mask":
                df[col] = df[col].apply(_mask)
            elif method == "encrypt":
                df[col] = df[col].apply(lambda v: _encrypt(cipher, v))
    return df


def apply_decryption_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """Decrypt encrypted columns in a pandas DataFrame."""
    cipher = load_key()
    df = df.copy()
    for col, method in security_config.items():
        if col in df.columns and method == "encrypt":
            df[col] = df[col].apply(lambda v: _decrypt(cipher, v))
    return df


# =========================
# LEGACY SPARK WRAPPERS (kept for compatibility, now use pandas internally)
# =========================

def apply_security(df, spark):
    """Spark DataFrame wrapper — converts to pandas, applies security, returns Spark DF."""
    pdf = df.toPandas()
    secured_pdf = apply_security_pandas(pdf)
    return spark.createDataFrame(secured_pdf)


def apply_decryption(df, spark):
    """Spark DataFrame wrapper — converts to pandas, decrypts, returns Spark DF."""
    pdf = df.toPandas()
    decrypted_pdf = apply_decryption_pandas(pdf)
    return spark.createDataFrame(decrypted_pdf)
