import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from firebase_config import db

# ----------------------------
# Load environment variables
# ----------------------------
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)
# ----------------------------
# Firebase Feedback Functions
# ----------------------------
def save_feedback_to_firebase(feedback_data: dict):
    """Save feedback to Firebase"""
    if not db:
        return False, "Database not initialized."
    try:
        db.collection("feedbacks").add(feedback_data)
        return True, "Feedback submitted successfully!"
    except Exception as e:
        return False, f"Error saving feedback: {str(e)}"

def get_all_feedbacks():
    """Fetch all feedbacks from Firebase"""
    if not db:
        return []
    try:
        feedbacks_ref = db.collection('feedbacks').stream()
        feedback_list = []
        for doc in feedbacks_ref:
            feedback_data = doc.to_dict()
            feedback_data['id'] = doc.id  # Store document ID for editing/deleting
            feedback_list.append(feedback_data)
        
        # Sort by created_at timestamp, newest first
        feedback_list.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
        return feedback_list
    except Exception as e:
        st.error(f"Error fetching feedbacks: {e}")
        return []

def delete_feedback_from_firebase(feedback_id: str):
    """Delete feedback from Firebase"""
    if not db:
        return False, "Database not initialized."
    try:
        db.collection("feedbacks").document(feedback_id).delete()
        return True, "Feedback deleted successfully!"
    except Exception as e:
        return False, f"Error deleting feedback: {str(e)}"


# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Feedback & Reviews", layout="wide", initial_sidebar_state="collapsed")

# ---------- STYLING ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
}

.feedback-card {
    transition: transform 0.2s, box-shadow 0.2s;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.feedback-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.stButton>button {
    min-width: 40px !important;
    height: 40px !important;
    padding: 0.25rem 0.5rem !important;
    margin: 0.25rem 0 !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}

.stButton>button:hover {
    transform: scale(1.1);
}

.star {
    color: #fbbf24;
    font-size: 1.1rem;
    letter-spacing: 2px;
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
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.1) 100%);
    pointer-events: none;
}

.main-header h1 {
    font-size: 3rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    color: white !important;
}

.main-header p {
    font-size: 1.3rem !important;
    font-weight: 800 !important;
    opacity: 0.9;
    color: white !important;
}

div[data-testid="stForm"] {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 12px;
    padding: 2.5rem;
    max-width: 900px;
    margin: auto;
    box-shadow: 0 8px 20px rgba(59,130,246,0.08);
}

[data-baseweb="select"] {
    width: 100% !important;
}

[data-baseweb="select"] > div {
    min-height: 48px !important;
    white-space: nowrap !important;
    overflow: visible !important;
    font-size: 1rem !important;
}

div[data-testid="stForm"] button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stForm"] button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(59,130,246,0.3);
}

.feedback-card {
    max-width: 900px;
    margin: 0 auto 1.25rem auto !important;
    background: #f8fafc !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important;
    border: 1px solid #e2e8f0 !important;
}

.feedback-content strong { color: #1e40af; font-size: 1.1em; }
.feedback-content p { color: #334155; line-height: 1.6; }
.feedback-content small { color: #64748b; }
.star { color: #f59e0b; font-size: 1.2em; }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = None

# ---------- HEADER ----------
st.markdown("""
<div class="main-header">
    <h1>🌟 Feedback & Reviews 🌟</h1>
    <p>Your voice helps us grow and serve better</p>
</div>
""", unsafe_allow_html=True)

# Create tabs for different sections
tab1, tab2 = st.tabs(["📝 Submit Feedback", "📜 All Feedback"])

# ---------- TAB 1: FEEDBACK FORM ----------
with tab1:
    st.markdown("### 📝 Share Your Thoughts")
    
    with st.form("feedback_form"):
        feedback_type = st.selectbox("👥 Feedback For", ["Donor", "NGO"])
        rating = st.slider("⭐ Rating (1-5)", 1, 5, 5)
        message = st.text_area("💬 Your Message", placeholder="Share your experience...")
        author = st.text_input("👤 Your Name (optional)", placeholder="Anonymous")
        
        submitted = st.form_submit_button("📤 Submit Feedback")

        if submitted:
            if not message.strip():
                st.error("❌ Please write a message before submitting.")
            else:
                feedback_entry = {
                    "type": feedback_type,
                    "rating": rating,
                    "message": message.strip(),
                    "author": author.strip() if author.strip() else "Anonymous",
                }
                
                feedback_entry["created_at"] = firestore.SERVER_TIMESTAMP
                success, msg = save_feedback_to_firebase(feedback_entry)
                if success:
                    st.success("📤 Feedback submitted successfully! Thank you!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

# ---------- TAB 2: DISPLAY FEEDBACK ----------
with tab2:
    st.markdown("### 📜 Recent Reviews")
    
    if st.button("🔄 Refresh Feedbacks"):
        st.rerun()
    
    filter_type = st.selectbox("Show Feedback For:", ["All", "Donor", "NGO"])
    
    feedbacks = get_all_feedbacks()
    filtered_feedbacks = feedbacks if filter_type == "All" else [f for f in feedbacks if f["type"] == filter_type]

    if filtered_feedbacks:
        for feedback in filtered_feedbacks:
            # Format timestamp
            created_at = "Recently"
            if 'created_at' in feedback and feedback['created_at']:
                ts = feedback['created_at']
                if hasattr(ts, "strftime"):
                    created_at = ts.strftime("%Y-%m-%d %I:%M %p")
                elif hasattr(ts, "to_datetime"):
                    created_at = ts.to_datetime().strftime("%Y-%m-%d %I:%M %p")
            
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"""
                <div class="feedback-card">
                    <div class="feedback-content">
                        <strong>📌 For {feedback['type']}</strong> | 
                        <span class="star">{"⭐" * feedback['rating']}</span><br>
                        <p>💬 {feedback['message']}</p>
                        <small>👤 {feedback['author']} | 📅 {created_at}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Delete button with confirmation
                if st.button("🗑️", key=f"delete_{feedback['id']}"):
                    if st.session_state.get('confirm_delete') == feedback['id']:
                        success, msg = delete_feedback_from_firebase(feedback['id'])
                        if success:
                            st.success("🗑️ Feedback deleted!")
                            st.session_state.confirm_delete = None
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.session_state.confirm_delete = feedback['id']
                        st.rerun()
                
                # Show confirmation message
                if st.session_state.get('confirm_delete') == feedback['id']:
                    st.warning("⚠️ Delete this?")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Yes", key=f"confirm_del_{feedback['id']}"):
                            success, msg = delete_feedback_from_firebase(feedback['id'])
                            if success:
                                st.success("🗑️ Deleted!")
                                st.session_state.confirm_delete = None
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    with col_b:
                        if st.button("❌ No", key=f"cancel_del_{feedback['id']}"):
                            st.session_state.confirm_delete = None
                            st.rerun()
    else:
        st.info("🌟 Be the first to share your feedback! 🌟")