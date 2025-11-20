import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
import hashlib
import secrets

# ==============================
# Load environment variables
# ==============================
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

# ==============================
# Firebase Initialization
# ==============================
@st.cache_resource
def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_JSON_PATH")
            if not cred_path or not os.path.exists(cred_path):
                st.error("Firebase credentials file not found. Check FIREBASE_CREDENTIALS_JSON_PATH in your .env file.")
                return None
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully")
        
        return firestore.client()
    except Exception as e:
        st.error(f"⚠️ Firebase initialization error: {e}")
        return None

db = initialize_firebase()

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="FoodBridge Admin Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# ADMIN CONFIGURATION
# ==============================
ADMIN_EMAIL = "ecologicalfibrecomposites@gmail.com"
ADMIN_PASSWORD = "Pvb@123456"

# ==============================
# Password Hashing Functions
# ==============================
def hash_password(password: str) -> str:
    if not password or not password.strip():
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(32)
    salted_password = salt + password
    password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
    return f"{salt}${password_hash}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
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

# ==============================
# Firebase Data Functions
# ==============================
def get_all_users():
    """Fetch all registered users (donors)"""
    if not db:
        return []
    try:
        users_ref = db.collection('users').stream()
        users_list = []
        for doc in users_ref:
            user_data = doc.to_dict()
            user_data['doc_id'] = doc.id  # This is the email
            users_list.append(user_data)
        return users_list
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return []

def get_all_ngos():
    """Fetch all registered NGOs"""
    if not db:
        return []
    try:
        ngos_ref = db.collection('ngos').stream()
        ngos_list = []
        for doc in ngos_ref:
            ngo_data = doc.to_dict()
            ngo_data['doc_id'] = doc.id  # This is the email
            ngos_list.append(ngo_data)
        return ngos_list
    except Exception as e:
        st.error(f"Error fetching NGOs: {e}")
        return []

def get_all_volunteers():
    """Fetch all registered volunteers"""
    if not db:
        return []
    try:
        volunteers_ref = db.collection('volunteers').stream()
        volunteers_list = []
        for doc in volunteers_ref:
            volunteer_data = doc.to_dict()
            volunteer_data['doc_id'] = doc.id  # Auto-generated ID
            volunteers_list.append(volunteer_data)
        return volunteers_list
    except Exception as e:
        st.error(f"Error fetching volunteers: {e}")
        return []

def get_all_donations():
    """Fetch all donations"""
    if not db:
        return []
    try:
        donations_ref = db.collection('donations').stream()
        donations_list = []
        for doc in donations_ref:
            donation_data = doc.to_dict()
            donation_data['id'] = doc.id
            donations_list.append(donation_data)
        donations_list.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
        return donations_list
    except Exception as e:
        st.error(f"Error fetching donations: {e}")
        return []

def get_all_feedbacks():
    """Fetch all feedbacks"""
    if not db:
        return []
    try:
        feedbacks_ref = db.collection('feedbacks').stream()
        feedback_list = []
        for doc in feedbacks_ref:
            feedback_data = doc.to_dict()
            feedback_data['id'] = doc.id
            feedback_list.append(feedback_data)
        feedback_list.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
        return feedback_list
    except Exception as e:
        st.error(f"Error fetching feedbacks: {e}")
        return []

def delete_user(user_email: str):
    """Delete a user"""
    if not db:
        return False, "Database not initialized."
    try:
        # Users are stored with email as document ID
        db.collection("users").document(user_email).delete()
        return True, "User deleted successfully!"
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"

def delete_ngo(ngo_email: str):
    """Delete an NGO"""
    if not db:
        return False, "Database not initialized."
    try:
        # NGOs are stored with email as document ID
        db.collection("ngos").document(ngo_email).delete()
        return True, "NGO deleted successfully!"
    except Exception as e:
        return False, f"Error deleting NGO: {str(e)}"

def delete_volunteer(volunteer_doc_id: str):
    """Delete a volunteer"""
    if not db:
        return False, "Database not initialized."
    try:
        # Volunteers use auto-generated document IDs
        db.collection("volunteers").document(volunteer_doc_id).delete()
        return True, "Volunteer deleted successfully!"
    except Exception as e:
        return False, f"Error deleting volunteer: {str(e)}"

# ==============================
# STYLING
# ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
}

.main-header {
    width: 100%;
    text-align: center;
    padding: 3rem 2rem;
    background: linear-gradient(135deg, #1e293b 0%, #3b82f6 50%, #8b5cf6 100%);
    color: white!important;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 
        0 20px 25px -5px rgba(59, 130, 246, 0.2),
        0 10px 10px -5px rgba(59, 130, 246, 0.1);
}

.main-header h1 {
    font-size: 3rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
    color: white !important;
}

.main-header p {
    font-size: 1.3rem !important;
    font-weight: 800 !important;
    opacity: 0.9;
    color: white !important;
}

.stat-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #3b82f6;
    margin-bottom: 1rem;
}

.stat-number {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1e293b;
}

.stat-label {
    font-size: 1rem;
    color: #64748b;
    font-weight: 500;
}

.user-card {
    background: #f8fafc;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    border: 1px solid #e2e8f0;
    transition: all 0.2s;
}

.user-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.stApp .stButton button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stApp .stButton button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-2px) !important;
}

.delete-btn button {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.875rem !important;
}

.delete-btn button:hover {
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
}

hr {
    border-color: rgba(59, 130, 246, 0.2) !important;
    margin: 2rem 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE
# ==============================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None
if "delete_type" not in st.session_state:
    st.session_state.delete_type = None

# ==============================
# ADMIN LOGIN
# ==============================
if not st.session_state.admin_logged_in:
    st.markdown("""
    <div class="main-header">
        <h1>👨‍💼 Admin Access Control 👨‍💼</h1>
        <p>Connecting Hearts, Sharing Meals, Building Communities</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🔐 Admin Login")
    with st.form("admin_login_form"):
        admin_email = st.text_input("Admin Email")
        admin_pass = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if admin_email == ADMIN_EMAIL and admin_pass == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials.")
    st.stop()

# ==============================
# ADMIN DASHBOARD
# ==============================
st.markdown("""
<div class="main-header">
    <h1>📊 Admin Dashboard 📊</h1>
    <p>Manage Users, Donations, and Feedback</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.success(f"👋 Welcome, Admin!")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.admin_logged_in = False
        st.session_state.confirm_delete = None
        st.session_state.delete_type = None
        st.rerun()
    
    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# Fetch all data
users = get_all_users()
ngos = get_all_ngos()
volunteers = get_all_volunteers()
donations = get_all_donations()
feedbacks = get_all_feedbacks()

# Statistics Overview
st.subheader("📈 Platform Statistics")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(users)}</div>
        <div class="stat-label">👥 Donors</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(ngos)}</div>
        <div class="stat-label">🏠 NGOs</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(volunteers)}</div>
        <div class="stat-label">🤝 Volunteers</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(donations)}</div>
        <div class="stat-label">📦 Donations</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(feedbacks)}</div>
        <div class="stat-label">⭐ Feedbacks</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 Donors", 
    "🏠 NGOs", 
    "🤝 Volunteers", 
    "📦 Donations", 
    "⭐ Feedbacks"
])

# ==============================
# TAB 1: DONORS
# ==============================
with tab1:
    st.subheader(f"👥 Registered Donors ({len(users)})")
    
    if users:
        # Add search functionality
        search_donor = st.text_input("🔍 Search donors by name or email", key="search_donor")
        
        filtered_users = users
        if search_donor:
            filtered_users = [u for u in users if 
                            search_donor.lower() in u.get('name', '').lower() or 
                            search_donor.lower() in u.get('email', '').lower()]
        
        for user in filtered_users:
            # Count donations by this donor
            donor_donations = [d for d in donations if d.get('donor_email') == user.get('email')]
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="user-card">
                        <h4>👤 {user.get('name', 'N/A')}</h4>
                        <p><strong>📧 Email:</strong> {user.get('email', 'N/A')}</p>
                        <p><strong>📅 Registered:</strong> {user.get('created_at', 'N/A')}</p>
                        <p><strong>🎁 Total Donations:</strong> {len(donor_donations)}</p>
                        <p><strong>✅ Accepted:</strong> {len([d for d in donor_donations if d.get('status') == 'Accepted'])}</p>
                        <p><strong>⏳ Pending:</strong> {len([d for d in donor_donations if d.get('status') == 'Pending'])}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                    if st.button("🗑️ Delete", key=f"del_user_{user['doc_id']}"):
                        st.session_state.confirm_delete = user['doc_id']
                        st.session_state.delete_type = 'user'
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.confirm_delete == user['doc_id'] and st.session_state.delete_type == 'user':
                    st.warning(f"⚠️ Confirm deletion of donor **{user.get('name')}**?")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Yes", key=f"confirm_{user['doc_id']}"):
                            success, msg = delete_user(user['doc_id'])
                            if success:
                                st.success(msg)
                                st.session_state.confirm_delete = None
                                st.session_state.delete_type = None
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_b:
                        if st.button("❌ No", key=f"cancel_{user['doc_id']}"):
                            st.session_state.confirm_delete = None
                            st.session_state.delete_type = None
                            st.rerun()
    else:
        st.info("No donors registered yet.")

# ==============================
# TAB 2: NGOs
# ==============================
with tab2:
    st.subheader(f"🏠 Registered NGOs ({len(ngos)})")
    
    if ngos:
        search_ngo = st.text_input("🔍 Search NGOs by name or email", key="search_ngo")
        
        filtered_ngos = ngos
        if search_ngo:
            filtered_ngos = [n for n in ngos if 
                           search_ngo.lower() in n.get('org_name', '').lower() or 
                           search_ngo.lower() in n.get('email', '').lower()]
        
        for ngo in filtered_ngos:
            # Count donations accepted by this NGO
            ngo_donations = [d for d in donations if d.get('accepted_by_email') == ngo.get('email')]
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="user-card">
                        <h4>🏢 {ngo.get('org_name', 'N/A')}</h4>
                        <p><strong>📧 Email:</strong> {ngo.get('email', 'N/A')}</p>
                        <p><strong>👤 Contact Person:</strong> {ngo.get('contact_person', 'N/A')}</p>
                        <p><strong>📞 Phone:</strong> {ngo.get('phone', 'N/A')}</p>
                        <p><strong>📍 Address:</strong> {ngo.get('address', 'N/A')}</p>
                        <p><strong>📅 Registered:</strong> {ngo.get('created_at', 'N/A')}</p>
                        <p><strong>🎁 Donations Accepted:</strong> {len(ngo_donations)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                    if st.button("🗑️ Delete", key=f"del_ngo_{ngo['doc_id']}"):
                        st.session_state.confirm_delete = ngo['doc_id']
                        st.session_state.delete_type = 'ngo'
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.confirm_delete == ngo['doc_id'] and st.session_state.delete_type == 'ngo':
                    st.warning(f"⚠️ Confirm deletion of NGO **{ngo.get('org_name')}**?")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Yes", key=f"confirm_{ngo['doc_id']}"):
                            success, msg = delete_ngo(ngo['doc_id'])
                            if success:
                                st.success(msg)
                                st.session_state.confirm_delete = None
                                st.session_state.delete_type = None
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_b:
                        if st.button("❌ No", key=f"cancel_{ngo['doc_id']}"):
                            st.session_state.confirm_delete = None
                            st.session_state.delete_type = None
                            st.rerun()
    else:
        st.info("No NGOs registered yet.")

# ==============================
# TAB 3: VOLUNTEERS
# ==============================
with tab3:
    st.subheader(f"🤝 Registered Volunteers ({len(volunteers)})")
    
    if volunteers:
        search_vol = st.text_input("🔍 Search volunteers by name or email", key="search_vol")
        
        filtered_volunteers = volunteers
        if search_vol:
            filtered_volunteers = [v for v in volunteers if 
                                 search_vol.lower() in v.get('name', '').lower() or 
                                 search_vol.lower() in v.get('email', '').lower()]
        
        for volunteer in filtered_volunteers:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    interests_str = ", ".join(volunteer.get('interests', []))
                    st.markdown(f"""
                    <div class="user-card">
                        <h4>👤 {volunteer.get('name', 'N/A')}</h4>
                        <p><strong>📧 Email:</strong> {volunteer.get('email', 'N/A')}</p>
                        <p><strong>📞 Phone:</strong> {volunteer.get('phone', 'N/A')}</p>
                        <p><strong>📍 Location:</strong> {volunteer.get('location', 'N/A')}</p>
                        <p><strong>📅 Availability:</strong> {volunteer.get('availability', 'N/A')}</p>
                        <p><strong>🎯 Interests:</strong> {interests_str or 'N/A'}</p>
                        <p><strong>💼 Experience:</strong> {volunteer.get('experience', 'None provided')}</p>
                        <p><strong>📅 Registered:</strong> {volunteer.get('registration_date', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                    if st.button("🗑️ Delete", key=f"del_vol_{volunteer['doc_id']}"):
                        st.session_state.confirm_delete = volunteer['doc_id']
                        st.session_state.delete_type = 'volunteer'
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.confirm_delete == volunteer['doc_id'] and st.session_state.delete_type == 'volunteer':
                    st.warning(f"⚠️ Confirm deletion of volunteer **{volunteer.get('name')}**?")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Yes", key=f"confirm_{volunteer['doc_id']}"):
                            success, msg = delete_volunteer(volunteer['doc_id'])
                            if success:
                                st.success(msg)
                                st.session_state.confirm_delete = None
                                st.session_state.delete_type = None
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_b:
                        if st.button("❌ No", key=f"cancel_{volunteer['doc_id']}"):
                            st.session_state.confirm_delete = None
                            st.session_state.delete_type = None
                            st.rerun()
    else:
        st.info("No volunteers registered yet.")

# ==============================
# TAB 4: DONATIONS
# ==============================
with tab4:
    st.subheader(f"📦 All Donations ({len(donations)})")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Accepted", "Rejected"])
    with col2:
        food_type_filter = st.selectbox("Filter by Food Type", ["All", "Veg", "Non-Veg", "Mixed"])
    with col3:
        search_donation = st.text_input("🔍 Search by donor or food name")
    
    # Apply filters
    filtered_donations = donations
    if status_filter != "All":
        filtered_donations = [d for d in filtered_donations if d.get('status') == status_filter]
    if food_type_filter != "All":
        filtered_donations = [d for d in filtered_donations if d.get('food_type') == food_type_filter]
    if search_donation:
        filtered_donations = [d for d in filtered_donations if 
                            search_donation.lower() in d.get('donor_name', '').lower() or 
                            search_donation.lower() in d.get('food_name', '').lower()]
    
    st.info(f"📊 Showing {len(filtered_donations)} donations")
    
    if filtered_donations:
        for donation in filtered_donations:
            status_color = {
                "Pending": "🟡",
                "Accepted": "🟢",
                "Rejected": "🔴"
            }.get(donation.get('status'), "⚪")
            
            created_at = "N/A"
            if 'created_at' in donation and donation['created_at']:
                ts = donation['created_at']
                if hasattr(ts, "strftime"):
                    created_at = ts.strftime("%Y-%m-%d %I:%M %p")
                elif hasattr(ts, "to_datetime"):
                    created_at = ts.to_datetime().strftime("%Y-%m-%d %I:%M %p")
            
            st.markdown(f"""
            <div class="user-card">
                <h4>{status_color} {donation.get('food_name', 'N/A')}</h4>
                <p><strong>👤 Donor:</strong> {donation.get('donor_name', 'N/A')} ({donation.get('donor_email', 'N/A')})</p>
                <p><strong>📦 Quantity:</strong> {donation.get('quantity', 'N/A')} servings</p>
                <p><strong>🥗 Type:</strong> {donation.get('food_type', 'N/A')}</p>
                <p><strong>📅 Expires:</strong> {donation.get('expiry_date', 'N/A')}</p>
                <p><strong>📍 Address:</strong> {donation.get('address', 'N/A')}</p>
                <p><strong>📞 Contact:</strong> {donation.get('contact_number', 'N/A')}</p>
                <p><strong>📝 Description:</strong> {donation.get('description', 'None')}</p>
                <p><strong>📅 Created:</strong> {created_at}</p>
                <p><strong>🎯 Status:</strong> {donation.get('status', 'N/A')}</p>
                {f"<p><strong>🏢 Accepted By:</strong> {donation.get('accepted_by_ngo', 'N/A')}</p>" if donation.get('status') == 'Accepted' else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No donations found matching the filters.")

# ==============================
# TAB 5: FEEDBACKS
# ==============================
with tab5:
    st.subheader(f"⭐ All Feedbacks ({len(feedbacks)})")
    
    # Filter
    feedback_filter = st.selectbox("Filter by Type", ["All", "Donor", "NGO"])
    
    filtered_feedbacks = feedbacks
    if feedback_filter != "All":
        filtered_feedbacks = [f for f in feedbacks if f.get('type') == feedback_filter]
    
    st.info(f"📊 Showing {len(filtered_feedbacks)} feedbacks")
    
    if filtered_feedbacks:
        for feedback in filtered_feedbacks:
            created_at = "Recently"
            if 'created_at' in feedback and feedback['created_at']:
                ts = feedback['created_at']
                if hasattr(ts, "strftime"):
                    created_at = ts.strftime("%Y-%m-%d %I:%M %p")
                elif hasattr(ts, "to_datetime"):
                    created_at = ts.to_datetime().strftime("%Y-%m-%d %I:%M %p")
            
            st.markdown(f"""
            <div class="user-card">
                <h4>⭐ {"⭐" * feedback.get('rating', 0)} ({feedback.get('rating', 0)}/5)</h4>
                <p><strong>📌 For:</strong> {feedback.get('type', 'N/A')}</p>
                <p><strong>💬 Message:</strong> {feedback.get('message', 'N/A')}</p>
                <p><strong>👤 Author:</strong> {feedback.get('author', 'Anonymous')}</p>
                <p><strong>📅 Submitted:</strong> {created_at}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No feedbacks found matching the filter.")