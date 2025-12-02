# firebase_config.py  (FINAL – local + Render, env folder support)
import os
import firebase_admin
from firebase_admin import credentials, firestore

try:
    import streamlit as st
except Exception:
    st = None

db = None


def _clean(path):
    """Remove extra quotes etc. from env path."""
    if not path:
        return None
    return path.strip().strip('"').strip("'")


def initialize_firebase():
    global db
    try:
        if not firebase_admin._apps:
            # 1) Env variable se path (Render + local dono)
            env_path = _clean(os.getenv("FIREBASE_CREDENTIALS_JSON_PATH"))

            # 2) Possible paths list (no hard-coded D: now)
            possible_paths = [
                "/etc/secrets/firebase_credentials.json",      # Render secret file
                env_path,                                      # .env / Render env
                os.path.join("env", "firebase_credentials.json"),  # local env/ folder
                "firebase_credentials.json",                   # project root fallback
                "serviceAccount.json",
            ]

            cred_path = None
            print("🔍 Looking for Firebase credentials in:")
            for p in possible_paths:
                if not p:
                    continue
                print("   -", p)
                if os.path.isfile(p):
                    cred_path = p
                    print(f"✅ Using Firebase credentials at: {p}")
                    break

            if not cred_path:
                msg = (
                    "Firebase credentials file not found. Tried:\n"
                    + "\n".join(p for p in possible_paths if p)
                )
                print("❌", msg)
                if st:
                    st.error(msg)
                db = None
                return db

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin initialized")

        db = firestore.client()
        print("✅ Firestore DB initialized")
        return db

    except Exception as e:
        print("❌ Firebase init error:", e)
        if st:
            st.error(f"⚠️ Firebase init error: {e}")
        db = None
        return db


if db is None:
    db = initialize_firebase()
