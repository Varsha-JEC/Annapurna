import streamlit as st
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from firebase_config import db
from firebase_admin import firestore
from pathlib import Path
import hashlib
import secrets

# ----------------------------
# Streamlit Page Config (MUST be first Streamlit call)
# ----------------------------
st.set_page_config(page_title="NGO Portal", page_icon="🤝", layout="wide")

# ----------------------------
# Load environment variables
# ----------------------------
env_path = Path(__file__).parent.parent / '.env'
print(f"🔍 Looking for .env file at: {env_path}")

load_dotenv(env_path, override=True)

print("📋 Environment variables:")
for var in ["FIREBASE_CREDENTIALS_JSON_PATH", "FIREBASE_DATABASE_URL"]:
    print(f"   {var}: {'✅ Set' if os.getenv(var) else '❌ Not set'}")

if not os.getenv("FIREBASE_CREDENTIALS_JSON_PATH"):
    print("❌ FIREBASE_CREDENTIALS_JSON_PATH is not set in .env file")
if not os.getenv("FIREBASE_DATABASE_URL"):
    print("❌ FIREBASE_DATABASE_URL is not set in .env file")

creds_path = os.getenv('FIREBASE_CREDENTIALS_JSON_PATH', '')
print(f"📂 Raw path from env: {creds_path}")
print(f"📂 Absolute path: {os.path.abspath(creds_path) if creds_path else 'N/A'}")
print(f"📂 File exists: {os.path.exists(creds_path) if creds_path else 'N/A'}")

# ----------------------------
# Password Hashing Functions (Same as Donor Portal)
# ----------------------------
def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a random salt.
    Returns salted hash in format: 'salt$hash'
    """
    if not password or not password.strip():
        raise ValueError("Password cannot be empty")
    
    salt = secrets.token_hex(32)
    salted_password = salt + password
    password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.
    """
    if not plain_password or not stored_hash:
        return False
    
    try:
        if '$' not in stored_hash:
            return False
        
        salt, original_hash = stored_hash.split('$', 1)
        salted_password = salt + plain_password
        password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
        return secrets.compare_digest(password_hash, original_hash)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

# ----------------------------
# NGO Authentication Functions
# ----------------------------
def create_ngo(org_name: str, email: str, password: str, address: str, contact_person: str, phone: str):
    """Create a new NGO account."""
    if not db:
        return False, "Database not initialized."
    try:
        if not org_name or not org_name.strip():
            return False, "Organization name cannot be empty"
        if not email or not email.strip():
            return False, "Email cannot be empty"
        if not password or not password.strip():
            return False, "Password cannot be empty"
        if not contact_person or not contact_person.strip():
            return False, "Contact person cannot be empty"
        if not phone or not phone.strip():
            return False, "Phone number cannot be empty"
        
        ngo_ref = db.collection("ngos").document(email.strip().lower())
        if ngo_ref.get().exists:
            return False, "NGO with this email already exists"
        
        hashed_password = hash_password(password)
        ngo_data = {
            "org_name": org_name.strip(),
            "email": email.strip().lower(),
            "hashed_password": hashed_password,
            "address": address.strip() if address else "",
            "contact_person": contact_person.strip(),
            "phone": phone.strip(),
            "created_at": firestore.SERVER_TIMESTAMP,
            "auth_method": "email"
        }
        ngo_ref.set(ngo_data)
        return True, "NGO registered successfully."
    except ValueError as ve:
        return False, str(ve)
    except Exception as e:
        return False, f"Error creating NGO: {str(e)}"


def verify_ngo_login(email: str, password: str):
    """Verify NGO login credentials."""
    if not db:
        return False, None
    try:
        if not email or not password:
            return False, None
        
        ngo_ref = db.collection("ngos").document(email.strip().lower())
        ngo_doc = ngo_ref.get()
        
        if not ngo_doc.exists:
            return False, None
        
        ngo_data = ngo_doc.to_dict()
        hashed_password = ngo_data.get("hashed_password")
        
        if not hashed_password:
            return False, None
        
        if verify_password(password, hashed_password):
            return True, ngo_data
        
        return False, None
    except Exception as e:
        st.error(f"Error logging in: {e}")
        return False, None


def update_ngo_password(email: str, new_password: str):
    """Update existing NGO's password."""
    if not db:
        return False, "Database not initialized."
    try:
        if not email or not email.strip():
            return False, "Email cannot be empty"
        if not new_password or not new_password.strip():
            return False, "Password cannot be empty"
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters long"

        ngo_ref = db.collection("ngos").document(email.strip().lower())
        ngo_doc = ngo_ref.get()
        if not ngo_doc.exists:
            return False, "No NGO found with this email"

        hashed_password = hash_password(new_password)
        ngo_ref.update({
            "hashed_password": hashed_password,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        return True, "Password updated successfully. Please login with your new password."
    except Exception as e:
        return False, f"Error updating password: {str(e)}"

# ----------------------------
# Session State Initialization
# ----------------------------
for key, default in {
    "ngo_logged_in": False,
    "ngo_data": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def save_ngo_data(ngo_info: dict):
    """Save NGO data to session state."""
    st.session_state.ngo_data = {
        "org_name": ngo_info.get("org_name", "NGO User"),
        "email": ngo_info.get("email"),
        "address": ngo_info.get("address", ""),
        "contact_person": ngo_info.get("contact_person", ""),
        "phone": ngo_info.get("phone", ""),
        "auth_method": ngo_info.get("auth_method", "email")
    }
    st.session_state.ngo_logged_in = True


def get_available_donations():
    """Fetch all available donations from Cloud Firestore."""
    if not db:
        st.error("Database connection not available.")
        return []
    try:
        donations_ref = db.collection('donations').where('status', '==', 'Pending').stream()
        
        donation_list = []
        for doc in donations_ref:
            donation_data = doc.to_dict()
            donation_data['id'] = doc.id
            donation_list.append(donation_data)
            
        return donation_list
    except Exception as e:
        st.error(f"Error fetching donations: {e}")
        return []


def accept_donation(donation_id: str, ngo_data: dict):
    """Update donation status to Accepted in Firestore."""
    if not db:
        return False
    try:
        doc_ref = db.collection('donations').document(donation_id)
        doc_ref.update({
            'status': 'Accepted',
            'accepted_by_ngo': ngo_data.get('org_name', 'Unknown NGO'),
            'accepted_by_email': ngo_data.get('email'),
            'accepted_at': firestore.SERVER_TIMESTAMP,
        })
        return True
    except Exception as e:
        st.error(f"Error accepting donation: {e}")
        return False

# ----------------------------
# Styling
# ----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
}

.main-header {
    text-align: center;
    padding: 3rem 2rem;
    background: linear-gradient(135deg, #1e293b 0%, #3b82f6 50%, #8b5cf6 100%);
    color: white;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 
        0 20px 25px -5px rgba(59, 130, 246, 0.2),
        0 10px 10px -5px rgba(59, 130, 246, 0.1);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%, rgba(255, 255, 255, 0.1) 100%);
    pointer-events: none;
}

.main-header h1 {
    font-size: 3rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    color: white !important;
}

.main-header p {
    font-size: 1.3rem !important;
    font-weight: 800 !important;
    opacity: 0.9;
    margin: 0 !important;
    color: white !important;
}

.section-heading {
    color: #1e293b !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
    margin-top: 2rem;
    margin-bottom: 1.5rem;
    letter-spacing: -0.025em;
}

div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255, 255, 255, 0.5);
    padding: 8px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    background: transparent;
    border-radius: 8px;
    color: #000000;
    font-weight: 1000;
    padding: 0 24px;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
}

.stApp .stButton button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2) !important;
}

.stApp .stButton button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3) !important;
}

.stApp .stButton button p {
    color: white !important;
}

.stApp [data-testid="stSidebar"] .stButton button {
    color: white !important;
}

.stApp [data-testid="stSidebar"] .stButton button p {
    color: white !important;
}

.donation-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(59, 130, 246, 0.15);
    border-left: 4px solid #3b82f6;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.donation-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 20px -3px rgba(59, 130, 246, 0.2);
    border-left-color: #2563eb;
}

.stTextInput input, .stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    transition: all 0.2s ease !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #7dd3fc !important; 
    box-shadow: 0 0 0 3px rgba(125, 211, 252, 0.25) !important; 
}

.stApp [data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
    backdrop-filter: blur(10px);
}

.stSuccess {
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    border-radius: 12px !important;
    color: #065f46 !important;
}

.stInfo {
    background: rgba(59, 130, 246, 0.1) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 12px !important;
    color: #1e40af !important;
}

.stError {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    border-radius: 12px !important;
    color: #991b1b !important;
}

.stApp p, .stApp li {
    color: #4b5563;
    line-height: 1.7;
}

stApp h1, .stApp h2, .stApp h3 {
    color: #1e293b;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
}

[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid #e0e6f1 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    margin-bottom: 1rem !important;
}

hr {
    border-color: rgba(59, 130, 246, 0.2) !important;
    margin: 2rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# LOGIN / REGISTER
# ----------------------------
if not st.session_state.ngo_logged_in:
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white !important;">🤲 NGO Portal 🤲</h1>
        <p style="color: white !important;">Empowering Organizations to Fight Hunger Together</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    # --- Login Tab ---
    with tab1:
        st.subheader("Login to Your Account")
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔒 Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True):
            if not db:
                st.error("❌ Database connection failed.")
            else:
                success, ngo_data = verify_ngo_login(email, password)
                if success:
                    save_ngo_data(ngo_data)
                    st.success("✅ Login successful! Welcome to the NGO Portal.")
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")

        # 👉 Forgot Password section
        st.markdown("---")
        st.markdown("##### 🔑 Forgot your password?")
        
        # Optional: custom CSS for expander width
        st.markdown("""
        <style>
            div[data-testid='stExpander'] {
                width: fit-content !important;
                min-width: 200px !important;
                max-width: 300px !important;
            }
            div[data-testid='stExpander'] > div:first-child {
                width: 100% !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        with st.expander("Click here to reset your password"):
            reset_email = st.text_input("📧 Registered Email", key="reset_email")
            new_pass = st.text_input("🆕 New Password", type="password", key="reset_new_pass")
            confirm_new_pass = st.text_input("🆕 Confirm New Password", type="password", key="reset_confirm_new_pass")

            if st.button("Reset Password", use_container_width=True, key="reset_password_btn"):
                if not reset_email or not new_pass or not confirm_new_pass:
                    st.error("❌ All fields are required.")
                elif new_pass != confirm_new_pass:
                    st.error("❌ New password and confirmation do not match.")
                elif len(new_pass) < 6:
                    st.error("❌ Password must be at least 6 characters long.")
                else:
                    success, msg = update_ngo_password(reset_email, new_pass)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

    # --- Register Tab ---
    with tab2:
        st.subheader("Register Your NGO")
        with st.form("register_form"):
            org_name = st.text_input("🏢 Organization Name")
            email = st.text_input("📧 Email")
            password = st.text_input("🔒 Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            address = st.text_area("📍 Address")
            contact_person = st.text_input("👤 Contact Person")
            phone = st.text_input("📞 Contact Number")

            submitted = st.form_submit_button("Register")
            if submitted:
                if not org_name or not email or not password or not contact_person or not phone:
                    st.error("❌ All fields except address are required!")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match!")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters long!")
                else:
                    if not db:
                        st.error("❌ Database connection failed.")
                    else:
                        success, msg = create_ngo(org_name, email, password, address, contact_person, phone)
                        if success:
                            st.success("✅ NGO registered successfully! Please log in.")
                        else:
                            st.error(f"❌ {msg}")

# ----------------------------
# DASHBOARD – After Login
# ----------------------------
else:
    with st.sidebar:
        st.success(f"✅ Logged in as: {st.session_state.ngo_data['org_name']}")

        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        
        if st.button("🔄 Refresh Donations"):
            st.rerun()

    st.markdown("""
    <div class="main-header">
        <h1 style="color: white !important;">📦 Available Donations</h1>
        <p style="color: white !important;">Connect with donors and make a difference in your community</p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Loading available donations..."):
        available_donations = get_available_donations()

    st.info(f"📊 **{len(available_donations)}** pending donations are available for pickup.")

    if not available_donations:
        st.warning("ℹ️ No active donations available right now. Check back later!")
    else:
        available_donations.sort(
            key=lambda d: d.get('created_at', datetime.min),
            reverse=True
        )

        for donation in available_donations:
            with st.container():
                st.markdown(f"""
                <div class="donation-card">
                    <h3 style="color: #1e2d3b; margin-bottom: 1rem;">🍲 {donation.get('food_name', 'Food Item')}</h3>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(
                        donation.get('image_url', "https://via.placeholder.com/300x200?text=No+Image"),
                        use_container_width=True,
                        caption=f"Serves: {donation.get('quantity', 'N/A')}",
                    )

                with col2:
                    st.write(f"**👤 Donor:** {donation.get('donor_name', 'Anonymous')}")
                    st.write(f"**📞 Contact:** {donation.get('contact_number', 'Not provided')}")
                    st.write(f"**📍 Address:** {donation.get('address', 'N/A')}")
                    st.write(f"**📅 Expires:** {donation.get('expiry_date', 'N/A')}")
                    st.write(f"**🥗 Type:** {donation.get('food_type', 'N/A')}")
                    st.write(f"**📝 Notes:** {donation.get('description', 'None')}")

                    if st.button("✅ Accept this Donation", key=f"accept_{donation.get('id')}", use_container_width=True):
                        if accept_donation(donation.get('id'), st.session_state.ngo_data):
                            st.success(f"🎉 Donation from {donation.get('donor_name', 'donor')} accepted!")
                            st.info("The donor will be notified. Please arrange for pickup.")
                            st.rerun()
