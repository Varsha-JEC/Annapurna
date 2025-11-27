import sys
import os
import json
from pathlib import Path
from datetime import datetime
import uuid
import hashlib
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
import streamlit as st
from googleapiclient.discovery import build
from firebase_config import db
from chatbot_utils import AnniChatbot
import google.generativeai as genai

# Assuming utils/styles.py contains these functions
from utils.styles import load_css, set_page_config, apply_custom_styles

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.append(project_root)

# --- PAGE CONFIGURATION (MUST BE FIRST) ---
set_page_config()

# ----------------------------------------------------------------
# FIREBASE INITIALIZATION
# ----------------------------------------------------------------
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ----------------------------------------------------------------
# GOOGLE OAUTH CONFIGURATION
# ----------------------------------------------------------------
try:
    redirect_uris = json.loads(
        os.getenv("GOOGLE_OAUTH_REDIRECT_URIS", '["http://localhost:8501"]')
    )
except json.JSONDecodeError:
    st.error("Error decoding GOOGLE_OAUTH_REDIRECT_URIS from environment.")
    redirect_uris = ["http://localhost:8501"]

GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": redirect_uris,
    }
}
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# --- AUTHENTICATION FUNCTIONS ---
def get_google_auth_url():
    """Generate Google OAuth authorization URL"""
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=GOOGLE_CLIENT_CONFIG["web"]["redirect_uris"][0],
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return auth_url

def get_google_user_info(code: str):
    """Exchange code for tokens and fetch user info"""
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=GOOGLE_CLIENT_CONFIG["web"]["redirect_uris"][0],
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    service = build("oauth2", "v2", credentials=credentials)
    return service.userinfo().get().execute()

def check_user_in_firebase(email: str):
    """Check if user exists in Firebase (in users or ngos collection)"""
    if not db:
        return None, None
    
    email = email.strip().lower()
    
    # Check in users collection (Donor)
    user_ref = db.collection("users").document(email)
    user_doc = user_ref.get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        return "Donor", user_data
    
    # Check in ngos collection
    ngo_ref = db.collection("ngos").document(email)
    ngo_doc = ngo_ref.get()
    if ngo_doc.exists:
        ngo_data = ngo_doc.to_dict()
        return "NGO", ngo_data
    
    return None, None

# --- HELPER FUNCTION FOR DIRECT FORM NAVIGATION ---
def navigate_to_form(role):
    """Navigate directly to the donation/acceptance form based on role"""
    if role == "Donor":
        # Navigate to Donor page which has the donation form
        st.switch_page("pages/2_💖_Donor.py")
    else:  # NGO
        # Navigate to NGO page which has the acceptance form
        st.switch_page("pages/3_🏘️_NGO.py")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'google_picture' not in st.session_state:
    st.session_state.google_picture = None
if 'google_email' not in st.session_state:
    st.session_state.google_email = None
if 'google_name' not in st.session_state:
    st.session_state.google_name = None
if 'is_new_user' not in st.session_state:
    st.session_state.is_new_user = False
if 'show_welcome_message' not in st.session_state:
    st.session_state.show_welcome_message = False
if 'redirect_to_form' not in st.session_state:
    st.session_state.redirect_to_form = False

if 'chatbot' not in st.session_state:
    if GEMINI_API_KEY:
        st.session_state.chatbot = AnniChatbot(GEMINI_API_KEY)
    else:
        st.session_state.chatbot = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'show_chatbot' not in st.session_state:
    st.session_state.show_chatbot = False

# ----------------------------------------------------------------
# GOOGLE OAUTH CALLBACK HANDLER
# ----------------------------------------------------------------
if "code" in st.query_params and not st.session_state.logged_in:
    code = st.query_params["code"]
    if isinstance(code, list):
        code = code[0]
        
    try:
        # Get user info from Google
        user_info = get_google_user_info(code)
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        # Clear query params immediately
        st.query_params.clear()
        
        # Check if user exists in Firebase
        existing_role, existing_data = check_user_in_firebase(email)
        
        if existing_role:
            # ✅ EXISTING USER - Auto redirect to their respective FORM
            st.session_state.logged_in = True
            st.session_state.role = existing_role
            st.session_state.google_email = email
            st.session_state.google_name = existing_data.get('name') or existing_data.get('org_name') or name
            st.session_state.google_picture = existing_data.get('google_picture') or picture
            st.session_state.username = email
            st.session_state.is_new_user = False
            st.session_state.show_welcome_message = False
            st.session_state.redirect_to_form = True
            
            # Success message with role-specific text
            if existing_role == "Donor":
                st.success(f"✅ Welcome back, {st.session_state.google_name}! Redirecting to donation form...")
            else:
                st.success(f"✅ Welcome back, {st.session_state.google_name}! Redirecting to acceptance form...")
            
            st.balloons()
            
            # Small delay for UX
            import time
            time.sleep(0.5)
            
            # Auto redirect to form page (not portal)
            navigate_to_form(existing_role)
                
        else:
            # ❌ NEW USER - Show welcome message and ask to register
            st.session_state.google_email = email
            st.session_state.google_name = name
            st.session_state.google_picture = picture
            st.session_state.is_new_user = True
            st.session_state.show_welcome_message = True
            st.session_state.logged_in = False
            st.rerun()
        
    except Exception as e:
        st.error(f"⚠️ Google login failed. Please try again. Error: {str(e)}")
        st.query_params.clear()
        import time
        time.sleep(2)
        st.rerun()

# --- FULL WIDTH LAYOUT ---
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], .stApp {
    margin: 0 !important;
    padding: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    overflow-x: hidden !important;
}

.main .block-container {
    max-width: 100% !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    margin: 0 !important;
    width: 100% !important;
}

section.main > div {
    padding-top: 0rem !important;
}

[data-testid="stSidebar"] {
    height: 100vh !important;
    min-height: 100vh !important;
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    width: 100% !important;
}

.stImage img {
    width: 100% !important;
    height: auto !important;
    object-fit: cover !important;
}

[data-testid="stMarkdownContainer"] {
    width: 100% !important;
}

@media (min-width: 1600px) {
    .main .block-container {
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Replace the add_footer() function in your annapurna.py with this updated version
def add_footer():
    """Modern, responsive footer with three columns for better organization"""
    # Start footer container
    st.markdown('<div class="footer-container">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <h3 class="footer-title">About Annapurna</h3>
        <p class="footer-text">
            Annapurna is a platform that connects donors with NGOs to reduce food waste and help those in need efficiently. 💚
        </p>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <h3 class="footer-title">Quick Links</h3>
        <ul class="footer-links">
            <li><a href="/" class="footer-link" target="_self">🏠 Home</a></li>
            <li><a href="/About" class="footer-link" target="_self">ℹ️ About</a></li>
            <li><a href="/NGO" class="footer-link" target="_self">🏢 NGO</a></li>
            <li><a href="/Donor" class="footer-link" target="_self">💖 Donor</a></li>
            <li><a href="/Volunteer" class="footer-link" target="_self">🤝 Volunteer</a></li>
            <li><a href="/Feedback" class="footer-link" target="_self">📝 Feedback</a></li>
        </ul>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <h3 class="footer-title">Connect With Us</h3>
        <p class="footer-text" style="margin-bottom: 0.5rem;">
            📧 <a href="mailto:AnnapurnaFoodbridge@gmail.com" class="footer-email">AnnapurnaFoodbridge@gmail.com</a>
        </p>
        <p class="footer-text" style="margin-bottom: 1rem;">
            📞 <a href="tel:+919630995163" class="footer-phone">+91 9630995163</a><br>
            📞 <a href="tel:+917049302011" class="footer-phone">+91 70493 02011</a>
        </p>
        <div class="social-icons">
            <a href="https://facebook.com" target="_blank" class="social-icon" title="Facebook">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v3.385z"/>
                </svg>
            </a>
            <a href="https://twitter.com" target="_blank" class="social-icon" title="Twitter">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                </svg>
            </a>
            <a href="https://instagram.com" target="_blank" class="social-icon" title="Instagram">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
            </a>
            <a href="https://linkedin.com" target="_blank" class="social-icon" title="LinkedIn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M4.98 3.5c0 1.381-1.11 2.5-2.48 2.5s-2.48-1.119-2.48-2.5c0-1.38 1.11-2.5 2.48-2.5s2.48 1.12 2.48 2.5zm.02 4.5h-5v16h5v-16zm7.982 0h-4.968v16h4.969v-8.399c0-4.67 6.029-5.052 6.029 0v8.399h4.988v-10.131c0-7.88-8.922-7.593-11.018-3.714v-2.155z"/>
                </svg>
            </a>
        </div>
        """, unsafe_allow_html=True)

    # Footer bottom section
    st.markdown("""
    <div class="footer-bottom">
        <p style="text-align: center;">© 2025 Annapurna. All rights reserved. Made with ❤️ for a hunger-free world.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Close footer container
    st.markdown('</div>', unsafe_allow_html=True)
    
# Load CSS
load_css("assets/css/style.css")
apply_custom_styles()

# --- SIDEBAR ---
with st.sidebar:
    st.image("assets/Annapurna logo.png", width=1000)
    st.markdown("---")

    if st.session_state.logged_in:
        st.success(f"Logged in as: **{st.session_state.google_name}** ({st.session_state.role})")
        
        if st.session_state.google_picture:
            st.markdown(f'<div style="text-align: center;"><img src="{st.session_state.google_picture}" style="width: 50px; height: 50px; border-radius: 50%;"></div>', unsafe_allow_html=True)
        
        # Navigation buttons based on role - Go to FORM directly
        if st.session_state.role == "Donor":
            if st.button("🍽️ Donate Food Now", use_container_width=True, type="primary"):
                navigate_to_form("Donor")
        elif st.session_state.role == "NGO":
            if st.button("✅ Accept this Donation", use_container_width=True, type="primary"):
                navigate_to_form("NGO")
            
        if st.button("🚪 Logout", key="sidebar_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.google_picture = None
            st.session_state.google_email = None
            st.session_state.google_name = None
            st.session_state.is_new_user = False
            st.session_state.show_welcome_message = False
            st.session_state.redirect_to_form = False
            st.query_params.clear()
            st.rerun()    
# --- MAIN CONTENT
# Replace the NEW USER WELCOME MESSAGE section in your annapurna.py (around line 295) with this:

if st.session_state.show_welcome_message and st.session_state.is_new_user:
    # Styles
    st.markdown("""
<style>
/* Main welcome container */
.new-user-welcome {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 24px;
    padding: 32px 18px;
    margin: 1.5rem auto;
    max-width: 1000px;
    box-shadow: 0 16px 48px rgba(0,0,0,0.25);
    position: relative;
    overflow: hidden;
}

.new-user-welcome::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1px);
    background-size: 18px 18px;
    opacity: 0.5;
}

/* Welcome header */
.welcome-header {
    text-align: center;
    margin-bottom: 28px;
    position: relative;
    z-index: 2;
}

.namaste-emoji {
    font-size: 3rem;
    display: inline-block;
    animation: float 3s ease-in-out infinite;
    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-14px); }
}

.welcome-title {
    color: white !important;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 12px 0 8px 0;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    letter-spacing: -0.5px;
}

.welcome-subtitle {
    color: white !important;
    font-size: 1.1rem;
    font-weight: 400;
    margin: 0 0 4px 0;
}

.welcome-email {
    color: white !important;
    font-size: 0.98rem;
    font-style: italic;
    margin: 0;
}

/* Cards container */
.role-cards-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 18px;
    padding: 10px;
    position: relative;
    z-index: 2;
}

/* Individual role card */
.role-card {
    background: white;
    border-radius: 18px;
    padding: 10px 10px;
    text-align: center;
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    cursor: pointer;
    position: relative;
    overflow: hidden;
    border: 2px solid transparent;
    max-width: 320px;
    margin: 0 auto;
}

.role-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(79,70,229,0.08) 0%, rgba(147,51,234,0.08) 100%);
    opacity: 0;
    transition: opacity 0.35s ease;
}

.role-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 14px 30px rgba(0,0,0,0.22);
    border-color: #4f46e5;
}

.role-card:hover::before {
    opacity: 1;
}

.role-card.donor:hover {
    border-color: #4f46e5;
}

.role-card.ngo:hover {
    border-color: #16a34a;
}

.role-card.volunteer:hover {
    border-color: #ea580c;
}

/* Card icon */
.card-icon {
    font-size: 3rem;
    margin-bottom: 12px;
    display: inline-block;
    transition: transform 0.35s ease;
    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}

.role-card:hover .card-icon {
    transform: scale(1.15) rotate(4deg);
}

/* Card title */
.card-title {
    color: #0f172a;
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0 0 8px 0;
    transition: color 0.3s ease;
}

.role-card:hover .card-title {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Card description */
.card-description {
    color: #475569;
    font-size: 0.92rem;
    line-height: 1.5;
    margin: 0 0 12px 0;
    min-height: 60px;
}

/* Card features */
.card-features {
    text-align: left;
    margin: 10px 0 14px 0;
    padding: 0 4px;
}

.feature-item {
    color: #64748b;
    font-size: 0.82rem;
    margin: 6px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}

.feature-item::before {
    content: '✓';
    color: #16a34a;
    font-weight: 700;
    font-size: 1rem;
}

/* Card button */
.card-button {
    display: inline-block;
    padding: 10px 22px;
    border-radius: 10px;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.92rem;
    color: white;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
    border: none;
    position: relative;
    overflow: hidden;
}

.card-button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    transform: translate(-50%, -50%);
    transition: width 0.55s ease, height 0.55s ease;
}

.card-button:hover::before {
    width: 220px;
    height: 220px;
}

.card-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(102, 126, 234, 0.5);
}

.role-card.donor .card-button {
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.role-card.ngo .card-button {
    background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.4);
}

.role-card.volunteer .card-button {
    background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.45);
}

/* Responsive design */
@media (max-width: 768px) {
    .welcome-title {
        font-size: 1.7rem;
    }
    
    .welcome-subtitle {
        font-size: 1rem;
    }
    
    .role-cards-container {
        grid-template-columns: 1fr;
        padding: 4px;
    }
    
    .card-description {
        min-height: auto;
    }
}

/* Animation entrance */
@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(24px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.role-card {
    animation: slideInUp 0.55s ease forwards;
}

.role-card:nth-child(1) {
    animation-delay: 0.05s;
}

.role-card:nth-child(2) {
    animation-delay: 0.15s;
}

.role-card:nth-child(3) {
    animation-delay: 0.25s;
}
</style>
""", unsafe_allow_html=True)

    # HTML (NO leading spaces so Streamlit doesn't treat lines as code)
    st.markdown(
        f"""
<div class="new-user-welcome">
<div class="welcome-header">
  <div class="namaste-emoji">🙏</div>
  <h1 class="welcome-title" style="color: white !important;">Namaste! Welcome to Annapurna</h1>
  <p class="welcome-subtitle" style="color: white !important;">We're delighted to have you join our mission to end hunger!</p>
  <p class="welcome-email" style="color: white !important;">Signed in as: <strong>{st.session_state.google_email}</strong></p>
</div>

<div class="role-cards-container">

  <!-- Donor Card -->
  <div class="role-card donor">
    <div class="card-icon">💖</div>
    <h2 class="card-title">Become a Donor</h2>
    <p class="card-description">
      Transform surplus food into hope. Your generous donations help feed those in need and reduce food waste in our community.
    </p>
    <div class="card-features">
      <div class="feature-item">Quick & easy donation process</div>
      <div class="feature-item">Real-time tracking of your impact</div>
      <div class="feature-item">Connect with verified NGOs</div>
      <div class="feature-item">Make a difference today</div>
    </div>
    <a href="/Donor" class="card-button" target="_self">
      <span style="position: relative; z-index: 1;">Start Donating →</span>
    </a>
  </div>

  <!-- NGO Card -->
  <div class="role-card ngo">
    <div class="card-icon">🏘️</div>
    <h2 class="card-title">Register as NGO</h2>
    <p class="card-description">
      Join our network of changemakers. Access quality food donations to serve communities and amplify your social impact.
    </p>
    <div class="card-features">
      <div class="feature-item">Access verified food donations</div>
      <div class="feature-item">Efficient distribution network</div>
      <div class="feature-item">Community impact tracking</div>
      <div class="feature-item">Partner with generous donors</div>
    </div>
    <a href="/NGO" class="card-button" target="_self">
      <span style="position: relative; z-index: 1;">Register NGO →</span>
    </a>
  </div>

  <!-- Volunteer Card -->
  <div class="role-card volunteer">
    <div class="card-icon">🤝</div>
    <h2 class="card-title" style="font-size: 2rem;">Join as Volunteer</h2>
    <p class="card-description">
      Be the bridge between surplus and scarcity. Your time and energy help deliver food and smiles to those who need it most.
    </p>
    <div class="card-features">
      <div class="feature-item">Flexible volunteering schedule</div>
      <div class="feature-item">Direct community impact</div>
      <div class="feature-item">Meet like-minded people</div>
      <div class="feature-item">Build a better tomorrow</div>
    </div>
    <a href="/Volunteer" class="card-button" target="_self">
      <span style="position: relative; z-index: 1;">Volunteer Now →</span>
    </a>
  </div>

</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.stop()


    
# --- REGULAR HOMEPAGE CONTENT (Only shown if not a new user) ---
st.markdown("""
<style>
.welcome-header-container {
    background: linear-gradient(135deg, #a8c0ff 0%, #3f2b96 100%);
    border-radius: 15px;
    padding: 50px 20px;
    margin-bottom: 30px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.welcome-header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.2) 1px, transparent 1px);
    background-size: 15px 15px;
    opacity: 0.7;
    z-index: 1;
}

.welcome-header-container h1 {
    font-size: 3.5em !important;
    font-weight: 700 !important;
    margin-bottom: 10px !important;
    position: relative;
    z-index: 2;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3) !important;
    color: white !important;
}

.welcome-header-container p {
    font-size: 1.2em !important;
    opacity: 0.95 !important;
    position: relative;
    z-index: 2;
    color: white !important;
    margin: 0 !important;
}
</style>

<div class="welcome-header-container">
    <div style="position: relative; z-index: 2;">
        <div style="color: white !important; margin: 0; font-size: 3.5em; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); line-height: 1.2;">🌾Welcome to Annapurna🌾</div>
        <div style="color: white !important; margin-top: 10px; font-size: 1.2em; opacity: 0.95;">💖 Building bridges between surplus food and hungry hearts 💖</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.community-header-container {
    background: linear-gradient(135deg, #b8a8d8 0%, #8b7ba8 100%);
    border-radius: 15px;
    padding: 30px 20px;
    margin-bottom: 30px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.community-header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.2) 1px, transparent 1px);
    background-size: 15px 15px;
    opacity: 0.7;
    z-index: 1;
}

.stImage img {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stImage img:hover {
    transform: scale(1.05);
    box-shadow: 0 12px 20px rgba(0,0,0,0.2);
}
</style>

<div class="community-header-container">
    <div style="position: relative; z-index: 2;">
        <div style="color: white !important; margin: 0; font-size: 2.2em; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); line-height: 1.2;">✨ Our Community ✨</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('''
<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin-bottom: 1.5rem;">
    <h2 class="community-subtitle" style="margin: 0;">🙏Our Generous Donors🙏</h2>
</div>
''', unsafe_allow_html=True)

col_d1, col_d2 = st.columns(2, gap="medium")
with col_d1:
    st.image("assets/donor-1.jpg", use_container_width=True)
with col_d2:
    st.image("assets/donor-2.jpg", use_container_width=True)

col_d3, col_d4 = st.columns(2, gap="medium")
with col_d3:
    st.image("assets/donor-3.jpg", use_container_width=True)
with col_d4:
    st.image("assets/donor-4.jpg", use_container_width=True)

st.markdown('''
<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin: 2.5rem 0 1.5rem;">
    <h2 class="community-subtitle" style="margin: 0;">🤝Our Valued NGO Partners🤝</h2>
</div>
''', unsafe_allow_html=True)

col_n1, col_n2 = st.columns(2, gap="medium")
with col_n1:
    st.image("assets/ngo-1.jpg", use_container_width=True)
with col_n2:
    st.image("assets/ngo-2.jpg", use_container_width=True)

col_n3, col_n4 = st.columns(2, gap="medium")
with col_n3:
    st.image("assets/ngo-3.jpg", use_container_width=True)
with col_n4:
    st.image("assets/ngo-4.jpg", use_container_width=True)

st.markdown("""
<div style="text-align: center; margin: 3rem 0 2rem;">
    <p style="font-size: 1.1rem; color: #0a0a0a;">
       🤝 Become a part of the Annapurna family and help us combat food waste and hunger. Whether you are a donor, an NGO, or a volunteer, your contribution makes a difference.🤝
    </p>
</div>
""", unsafe_allow_html=True)

# --- LOGIN SECTION (Only shown if not logged in and not a new user) ---
if not st.session_state.logged_in:
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h2 style="color: #1e293b;">Join Annapurna Today!</h2>
        <p style="color: #4b5563;">Sign in with Google to quickly donate or accept food</p>
    </div>
    """, unsafe_allow_html=True)
    
    if (GOOGLE_CLIENT_CONFIG["web"]["client_id"] and 
        GOOGLE_CLIENT_CONFIG["web"]["client_secret"]):
        
        google_auth_url = get_google_auth_url()
        
        col_pre, col_btn, col_post = st.columns([1, 2, 1])
        
        with col_btn:
            st.markdown(
                f'''
                <a href="{google_auth_url}" target="_self" style="
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 12px 24px;
                    background: linear-gradient(180deg, #4285F4 0%, #357AE8 100%);
                    color: white;
                    font-weight: 600;
                    font-size: 16px;
                    font-family: 'Segoe UI', Roboto, Arial, sans-serif;
                    text-decoration: none;
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.4);
                    transition: all 0.2s ease-in-out;
                    width: 100%;
                " onmouseover="this.style.backgroundColor='#357AE8'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.2)'; this.style.transform='translateY(1px)'" onmouseout="this.style.backgroundColor='#4285F4'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.4)'; this.style.transform='translateY(0)'">
                    <img src="https://www.google.com/favicon.ico" 
                        style="width:22px; height:22px; margin-right:12px; background:white; border-radius:50%; padding:3px;">
                    Continue with Google
                </a>
                ''',
                unsafe_allow_html=True
            )
    else:
        st.warning("⚠️ Google OAuth is not configured. Please use the specific Donor/NGO pages for login.")
# --- CHATBOT UI ---
if st.session_state.chatbot:
    # CSS for floating button AND new chat window
    st.markdown('''
    <style>
       /* --- 2. CHAT WINDOW --- */
    /* This targets the main chat window container */
    div[data-testid="stVerticalBlock"]:has(> div.chat-window-marker) {
        position: fixed !important;
        bottom: 100px !important;
        right: 30px !important;
        width: 400px !important;
        max-width: 90vw !important;
        height: 600px !important;
        max-height: 80vh !important;
        background: white !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3) !important;
        z-index: 999998 !important;
        animation: slideUp 0.3s ease !important;
        overflow: hidden !important;
        /* We use flex to layout the header, messages, and input */
        display: flex !important;
        flex-direction: column !important;
    }}

    @keyframes slideUp {{
        from {{ transform: translateY(20px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}

    /* This targets the header container */
    div[data-testid="stVerticalBlock"]:has(> div.chat-header-marker) {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 10px 15px 25px; /* Adjusted padding */
        border-bottom: 2px solid #e5e7eb;
        flex-shrink: 0; /* Header should not shrink */
    }}
    
    /* Make the close button blend in */
    div[data-testid="stVerticalBlock"]:has(> div.chat-header-marker) button {{
        background: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 1.2rem;
        padding: 0 !important;
        margin-top: -5px; /* Align icon */
    }}
    
    div[data-testid="stVerticalBlock"]:has(> div.chat-header-marker) button:hover {{
        background: rgba(255,255,255,0.2) !important;
    }}

    /* This targets the scrollable message area */
    div[data-testid="stScrollableContainer"]:has(div.chat-messages-marker) {{
        flex-grow: 1; /* Message area should fill available space */
        background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
        padding: 20px;
    }}

    div[data-testid="stScrollableContainer"]:has(div.chat-messages-marker) > div[data-testid="stVerticalBlock"] {{
        gap: 0.5rem !important; /* Spacing between messages */
    }}

    /* This targets the input form container */
    div[data-testid="stVerticalBlock"]:has(div.chat-input-marker) {{
        padding: 15px;
        background: white;
        border-top: 2px solid #e5e7eb;
        flex-shrink: 0; /* Input area should not shrink */
    }}

    /* --- 3. CHAT MESSAGE STYLES (These are mostly unchanged) --- */
    .message {{
        margin-bottom: 15px;
        display: flex;
        gap: 10px;
        animation: fadeIn 0.3s ease;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .message.user {{ flex-direction: row-reverse; }}

    .message-content {{
        max-width: 80%; /* Slightly wider */
        padding: 12px 16px;
        border-radius: 15px;
        line-height: 1.5;
        font-size: 0.95rem;
        word-wrap: break-word;
    }}

    .message.user .message-content {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px 15px 0 15px;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }}

    .message.bot .message-content {{
        background: white;
        color: #1f2937;
        border: 2px solid #e5e7eb;
        border-radius: 15px 15px 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .message-avatar {{
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}

    .message.user .message-avatar {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }}

    .message.bot .message-avatar {{
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    }}

    /* --- 4. FORM BUTTON STYLES --- */
    /* Style form buttons inside the chat */
    div[data-testid="stVerticalBlock"]:has(div.chat-input-marker) button[kind="primary"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(div.chat-input-marker) button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        transform: scale(1.02) !important;
    }}
    </style>
    ''', unsafe_allow_html=True)
    
   # Floating button
    with st.container():
        # Yeh marker div CSS ko batayega ki floating button is container mein hai
        st.markdown('<div class="floating-button-container"></div>', unsafe_allow_html=True)
        
        if st.button("🤖 Ask Anni", key="floating_chat_toggle", help="Chat with Anni", type="primary"):
            st.session_state.show_chatbot = not st.session_state.show_chatbot
            st.rerun()

    # Chat window - Built with native Streamlit containers
    if st.session_state.show_chatbot:
        
        # This is the main window container
        with st.container(border=False):
            # Marker div for CSS to target this container
            st.markdown('<div class="chat-window-marker"></div>', unsafe_allow_html=True) 
            
            # --- Header ---
            with st.container(border=False):
                # Marker div for CSS to target header
                st.markdown('<div class="chat-header-marker"></div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns([5, 1], gap="small")
                with col1:
                    st.markdown('<h3 style="color: white; margin: 0; line-height: 40px;">🤖 Chat with Anni</h3>', unsafe_allow_html=True)
                with col2:
                    if st.button("❌", key="close_chat", help="Close chat"):
                        st.session_state.show_chatbot = False
                        st.rerun()

            # --- Messages ---
            # Use st.container(height=...) to create the scrollable message area
            with st.container(height=400):
                # Marker div for CSS to target message area
                st.markdown('<div class="chat-messages-marker"></div>', unsafe_allow_html=True)
                
                if not st.session_state.chat_history:
                    st.markdown('''
                    <div class="message bot">
                        <div class="message-avatar">🤖</div>
                        <div class="message-content">
                            Hi! I'm Anni, your Annapurna assistant! 🌾<br><br>
                            I'm here to help you with:<br>
                            • How to donate food 🍽️<br>
                            • How NGOs can accept donations 🤝<br>
                            • Information about our platform 💖<br><br>
                            What would you like to know?
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                for msg in st.session_state.chat_history:
                    role_class = "user" if msg['role'] == 'user' else "bot"
                    avatar = "👤" if msg['role'] == 'user' else "🤖"
                    st.markdown(f'''
                    <div class="message {role_class}">
                        <div class="message-avatar">{avatar}</div>
                        <div class="message-content">{msg['content']}</div>
                    </div>
                    ''', unsafe_allow_html=True)
            
            # --- Input Area ---
            with st.container(border=False):
                # Marker div for CSS to target input area
                st.markdown('<div class="chat-input-marker"></div>', unsafe_allow_html=True)
                
                with st.form(key="chat_form", clear_on_submit=True):
                    user_input = st.text_input("Message", key="user_input", label_visibility="collapsed", placeholder="Type your message...")
                    col1, col2, col3 = st.columns([4, 1, 1], gap="small")
                    
                    with col2:
                        send = st.form_submit_button("Send", use_container_width=True, type="primary")
                    with col3:
                        clear = st.form_submit_button("Clear", use_container_width=True)
                    
                    if send and user_input:
                        st.session_state.chat_history.append({
                            'role': 'user',
                            'content': user_input,
                            'timestamp': datetime.now()
                        })
                        
                        with st.spinner("Anni is thinking..."):
                            response = st.session_state.chatbot.get_response(user_input)
                        
                        st.session_state.chat_history.append({
                            'role': 'bot',
                            'content': response,
                            'timestamp': datetime.now()
                        })
                        st.rerun()
                    
                    if clear:
                        st.session_state.chat_history = []
                        st.session_state.chatbot.reset_chat()
                        st.rerun()

else:
    st.markdown('''
    <div style="position: fixed; bottom: 30px; right: 30px; z-index: 999999; background: #ccc; color: white; padding: 15px; border-radius: 50px; font-size: 1.2rem;">
        🤖 Unavailable
    </div>
    ''', unsafe_allow_html=True)

# Add the footer
add_footer()