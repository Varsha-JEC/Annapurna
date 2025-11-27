# firebase_config.py
import os
import firebase_admin
from firebase_admin import credentials, firestore

try:
    import streamlit as st
except ImportError:
    st = None

db = None  # global

def initialize_firebase():
    global db
    try:
        if not firebase_admin._apps:

            # 1️⃣ Render secret file fixed path
            possible_paths = ["/etc/secrets/firebase_credentials.json"]

            # 2️⃣ Env variable path (local / For render dono )
            env_path = os.getenv("FIREBASE_CREDENTIALS_JSON_PATH")
            if env_path:
                possible_paths.append(env_path)

            # 3️⃣ Local development fallback
            possible_paths.append("firebase_credentials.json")
            possible_paths.append("serviceAccount.json")

            cred_path = None
            print("🔍 Looking for Firebase credentials in:")
            for p in possible_paths:
                print("   -", p)
                if p and os.path.exists(p):
                    cred_path = p
                    print(f"✅ Using Firebase credentials at: {p}")
                    break

            if not cred_path:
                msg = (
                    "Firebase credentials file not found.\n"
                    "Tried:\n" + "\n".join(f"- {p}" for p in possible_paths)
                )
                print("❌ " + msg)
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
        print(f"❌ Firebase initialization error: {e}")
        if st:
            st.error(f"⚠️ Firebase initialization error: {e}")
        db = None
        return db

# app load initialize
if db is None:
    db = initialize_firebase()
