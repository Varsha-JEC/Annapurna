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
            import json
            
            # Try JSON from environment variable first (Render)
            firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
            
            if firebase_creds_json:
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
                print("✅ Using Firebase credentials from env variable")
            else:
                # Fallback to file (local dev)
                possible_paths = [
                    os.path.join("env", "firebase_credentials.json"),
                    "firebase_credentials.json",
                    "serviceAccount.json",
                ]
                
                cred_path = None
                for p in possible_paths:
                    if p and os.path.isfile(p):
                        cred_path = p
                        break
                
                if not cred_path:
                    raise RuntimeError("Firebase credentials not found")
                
                cred = credentials.Certificate(cred_path)
                print(f"✅ Using Firebase credentials from: {cred_path}")

            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin initialized")

        db = firestore.client()
        return db

    except Exception as e:
        print("❌ Firebase init error:", e)
        if st:
            st.error(f"⚠️ Firebase init error: {e}")
        return None


if db is None:
    db = initialize_firebase()
