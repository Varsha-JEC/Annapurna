import streamlit as st
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

# ----------------------------
# Load environment variables
# ----------------------------
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

# ----------------------------
# Firebase Initialization
# ----------------------------
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

# ----------------------------
# Volunteer Registration Function
# ----------------------------
def save_volunteer_registration(volunteer_data: dict):
    """Save volunteer registration to Firebase"""
    if not db:
        return False, "Database connection not available."
    try:
        # Add to 'volunteers' collection
        db.collection("volunteers").add(volunteer_data)
        return True, "Registration successful!"
    except Exception as e:
        return False, f"Error saving registration: {str(e)}"

# --- Page Configuration ---
st.set_page_config(
    page_title="Join as a Volunteer",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
/* Import modern font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global styling */
.stApp {
    font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
}

/* Main header with modern blue gradient */
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

/* Section headings */
.section-subheading {
    color: #1e293b !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
    margin-top: 2rem;
    margin-bottom: 1.5rem;
}

/* Form styling */
div[data-testid="stForm"] {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 25px;
    margin-top: 20px;
}

div[data-testid="stForm"] button {
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

div[data-testid="stForm"] button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3) !important;
}

div[data-testid="stForm"] button p {
    color: white !important;
}

/* Body text */
.stApp p, .stApp li {
    color: #4b5563;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🤝 Join as a Volunteer 🤝</h1>
    <p>Your time can make a difference in someone's life</p>
</div>
""", unsafe_allow_html=True)

# --- VOLUNTEERS SECTION ---
st.markdown("<h1 class='section-subheading'>👥 Our Amazing Volunteers 🌟</h1>", unsafe_allow_html=True)
volunteer_images = [
    "assets/food donation prepaed by voluteer-1.jpg", 
    "assets/food-donation-box-being-prepared-by-volunteers-2.jpg", 
    "assets/food donation prepaed by voluteer-3.jpg"
]
cols = st.columns(3)
for i, image_path in enumerate(volunteer_images):
    with cols[i]:
        st.image(image_path, caption="🙌 Helping Hand", use_container_width=True)

st.write("---")
st.markdown("<p style='font-weight: bold; color: black; font-size: 1.1em;'>🤝 Let's join hands to make a difference in the lives of those in need. 💚</p>", unsafe_allow_html=True)

# --- VOLUNTEER REGISTRATION FORM ---
with st.form("volunteer_registration"):
    name = st.text_input("👤 Full Name *", placeholder="Enter your name")
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("📧 Email *", placeholder="your@email.com")
    with col2:
        phone = st.text_input("📞 Phone Number *", placeholder="+91 1234567890")
    location = st.text_input("📍 Preferred Location *", placeholder="City or area")
    availability = st.text_input("📅 Availability *", placeholder="e.g., Weekends, Evenings")

    st.write("🎯 Areas of Interest")
    interests = {
        "Food Collection": st.checkbox("Food Collection"),
        "Delivery & Logistics": st.checkbox("Delivery & Logistics"),
        "Event Coordination": st.checkbox("Event Coordination"),
        "Community Outreach": st.checkbox("Community Outreach")
    }
    experience = st.text_area("💼 Skills & Experience (Optional)", placeholder="Tell us about any relevant skills or experience...")

    submitted = st.form_submit_button("Register as Volunteer")

    if submitted:
        selected_interests = [interest for interest, is_selected in interests.items() if is_selected]
        
        # Validate required fields
        if not name or not email or not phone or not location or not availability:
            st.error("❌ Please fill out all required fields (*).")
        elif not selected_interests:
            st.warning("⚠️ Please select at least one area of interest.")
        else:
            # Prepare volunteer data
            volunteer_data = {
                "name": name.strip(),
                "email": email.strip().lower(),
                "phone": phone.strip(),
                "location": location.strip(),
                "availability": availability.strip(),
                "interests": selected_interests,
                "experience": experience.strip() if experience else "",
                "registration_date": firestore.SERVER_TIMESTAMP,
                "status": "Active"  # Can be used to track active volunteers
            }
            
            # Save to Firebase
            if not db:
                st.error("❌ Database connection failed. Please try again later.")
            else:
                success, message = save_volunteer_registration(volunteer_data)
                
                if success:
                    st.success(f"🎉 Thank you, {name}, for registering! We will contact you shortly.")
                    st.balloons()
                    
                    # Display registration summary
                    st.write("### 📋 Registration Summary")
                    st.write(f"**👤 Name:** {name}")
                    st.write(f"**📧 Email:** {email}")
                    st.write(f"**📞 Phone:** {phone}")
                    st.write(f"**📍 Location:** {location}")
                    st.write(f"**📅 Availability:** {availability}")
                    st.write(f"**🎯 Interests:** {', '.join(selected_interests)}")
                    if experience:
                        st.write(f"**💼 Experience:** {experience}")
                else:
                    st.error(f"❌ {message}")