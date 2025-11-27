import streamlit as st
import json
import os
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from dotenv import load_dotenv
from firebase_config import db
import hashlib
import secrets
import time
import googlemaps

# Apply custom styles (keeping your original styles)
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

.ngo-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-left: 4px solid #10b981;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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

[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid #e0e6f1 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    margin-bottom: 1rem !important;
}

.status-tag {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 16px;
    font-weight: 600;
    font-size: 0.9rem;
}

.status-pending {
    background-color: #fffbeb; 
    color: #b45309;
}

.status-accepted {
    background-color: #f0fdf4;
    color: #15803d;
}
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Initialize Google Maps client
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = None
if GOOGLE_MAPS_API_KEY:
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        print("✅ Google Maps API initialized successfully")
    except Exception as e:
        print(f"⚠️ Google Maps API initialization failed: {e}")
        gmaps = None
else:
    print("⚠️ GOOGLE_MAPS_API_KEY not found in environment variables")

# --- Password Hashing ---
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

# --- USER AUTH ---
def create_user(name: str, email: str, password: str):
    if not db:
        return False, "Database not initialized."
    try:
        if not name or not name.strip():
            return False, "Name cannot be empty"
        if not email or not email.strip():
            return False, "Email cannot be empty"
        if not password or not password.strip():
            return False, "Password cannot be empty"
        user_ref = db.collection("users").document(email.strip().lower())
        if user_ref.get().exists:
            return False, "User with this email already exists"
        hashed_password = hash_password(password)
        user_data = {
            "name": name.strip(),
            "email": email.strip().lower(),
            "hashed_password": hashed_password,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        user_ref.set(user_data)
        return True, "User created successfully."
    except ValueError as ve:
        return False, str(ve)
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

def verify_login(email: str, password: str):
    if not db:
        return False, None
    try:
        if not email or not password:
            return False, None
        user_ref = db.collection("users").document(email.strip().lower())
        user_doc = user_ref.get()
        if not user_doc.exists:
            return False, None
        user_data = user_doc.to_dict()
        hashed_password = user_data.get("hashed_password")
        if not hashed_password:
            return False, None
        if verify_password(password, hashed_password):
            return True, user_data
        return False, None
    except Exception as e:
        st.error(f"Error logging in: {e}")
        return False, None

# --- Session Initialization ---
if "user" not in st.session_state:
    st.session_state.user = None
if "donor_logged_in" not in st.session_state:
    st.session_state.donor_logged_in = False
if "geocode_cache" not in st.session_state:
    st.session_state.geocode_cache = {}

# --- FIREBASE DONATION FUNCTIONS ---
def save_donation_to_firebase(donation_data: dict):
    if not db:
        return False
    try:
        db.collection("donations").add(donation_data)
        return True
    except Exception as e:
        print(f"Error saving donation: {str(e)}")
        return False

def get_donations_by_email(email: str):
    if not db:
        return []
    try:
        query = db.collection("donations").where("donor_email", "==", email)
        donations = [doc.to_dict() for doc in query.stream()]
        donations.sort(key=lambda x: x.get('created_at') or datetime.min, reverse=True)
        return donations
    except Exception as e:
        st.error(f"Error fetching donations: {e}")
        return []

# --- IMPROVED NGO LOCATION FUNCTIONS ---
def get_ngos_from_firebase():
    """Fetch all NGOs from Firebase"""
    if not db:
        st.error("Database not initialized")
        return []
    try:
        ngos = []
        docs = db.collection("ngos").stream()
        for doc in docs:
            ngo_data = doc.to_dict()
            ngo_data['id'] = doc.id
            ngos.append(ngo_data)
        print(f"✅ Fetched {len(ngos)} NGOs from Firebase")
        for ngo in ngos:
            print(f"  - {ngo.get('org_name', 'Unknown')}: {ngo.get('address', 'No address')}")
        return ngos
    except Exception as e:
        st.error(f"Error fetching NGOs: {e}")
        return []

def geocode_address_with_retry(address: str, max_retries=3):
    """
    Geocode address using Google Maps API (primary) or fallback
    Optimized for Indian addresses
    """
    # Check cache first
    if address in st.session_state.geocode_cache:
        print(f"🔍 Using cached coordinates for: {address}")
        return st.session_state.geocode_cache[address]
    
    # Clean address
    clean_address = address.strip()
    
    # Try Google Maps API first (if available)
    if gmaps:
        print(f"🔍 Geocoding with Google Maps API: {clean_address}")
        try:
            result = gmaps.geocode(clean_address, region='in')
            
            if result and len(result) > 0:
                location = result[0]['geometry']['location']
                coords = (location['lat'], location['lng'])
                print(f"✅ Google Maps found coordinates: {coords}")
                
                # Cache the result
                st.session_state.geocode_cache[address] = coords
                return coords
            else:
                print(f"⚠️ Google Maps: No results for {clean_address}")
        except Exception as e:
            print(f"❌ Google Maps API error: {e}")
    
    # Fallback: Try adding India if not present
    if not any(term in clean_address.lower() for term in ['india', 'bharat']):
        clean_address_with_country = f"{clean_address}, India"
        if gmaps:
            try:
                result = gmaps.geocode(clean_address_with_country, region='in')
                if result and len(result) > 0:
                    location = result[0]['geometry']['location']
                    coords = (location['lat'], location['lng'])
                    print(f"✅ Google Maps found (with India): {coords}")
                    st.session_state.geocode_cache[address] = coords
                    return coords
            except Exception as e:
                print(f"❌ Google Maps API error (retry): {e}")
    
    print(f"❌ Failed to geocode: {address}")
    return None

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates in kilometers"""
    try:
        distance = round(geodesic(coord1, coord2).kilometers, 2)
        return distance
    except Exception as e:
        print(f"Error calculating distance: {e}")
        return None

def find_nearby_ngos(donor_address: str, max_distance: float = 10.0):
    """
    Find NGOs near the donor's address with improved error handling
    """
    print(f"\n🔎 Searching for NGOs near: {donor_address}")
    print(f"📏 Maximum distance: {max_distance} km")
    
    # Get donor coordinates
    donor_coords = geocode_address_with_retry(donor_address)
    if not donor_coords:
        print("❌ Could not geocode donor address")
        return None, []
    
    print(f"✅ Donor location: {donor_coords}")
    
    # Get all NGOs
    ngos = get_ngos_from_firebase()
    if not ngos:
        print("⚠️ No NGOs found in database")
        return donor_coords, []
    
    nearby_ngos = []
    
    # Process each NGO
    for ngo in ngos:
        ngo_address = ngo.get('address', '').strip()
        if not ngo_address:
            print(f"⚠️ NGO {ngo.get('org_name', 'Unknown')} has no address")
            continue
        
        print(f"\n📍 Processing NGO: {ngo.get('org_name', 'Unknown')}")
        print(f"   Address: {ngo_address}")
        
        # Geocode NGO address
        ngo_coords = geocode_address_with_retry(ngo_address)
        if not ngo_coords:
            print(f"   ❌ Could not geocode NGO address")
            continue
        
        print(f"   ✅ NGO coordinates: {ngo_coords}")
        
        # Calculate distance
        distance = calculate_distance(donor_coords, ngo_coords)
        if distance is None:
            print(f"   ❌ Could not calculate distance")
            continue
        
        print(f"   📏 Distance: {distance} km")
        
        if distance <= max_distance:
            ngo['distance'] = distance
            ngo['coordinates'] = ngo_coords
            nearby_ngos.append(ngo)
            print(f"   ✅ Added to nearby list")
        else:
            print(f"   ⚠️ Too far ({distance} km > {max_distance} km)")
    
    # Sort by distance
    nearby_ngos.sort(key=lambda x: x.get('distance', float('inf')))
    
    print(f"\n📊 Final results: {len(nearby_ngos)} NGOs within {max_distance} km")
    for ngo in nearby_ngos:
        print(f"  - {ngo.get('org_name')}: {ngo.get('distance')} km")
    
    return donor_coords, nearby_ngos

def create_ngo_map(donor_coords, nearby_ngos):
    """Create a folium map showing donor location and nearby NGOs"""
    m = folium.Map(location=donor_coords, zoom_start=12)
    
    # Add donor marker
    folium.Marker(
        donor_coords,
        popup="<b>Your Location</b>",
        tooltip="Your Location",
        icon=folium.Icon(color='red', icon='home', prefix='fa')
    ).add_to(m)
    
    # Add NGO markers
    for ngo in nearby_ngos:
        if 'coordinates' in ngo:
            popup_html = f"""
            <div style="width: 250px; font-family: Arial;">
                <h4 style="margin: 0 0 10px 0; color: #1e293b;">{ngo.get('org_name', 'NGO')}</h4>
                <p style="margin: 5px 0;"><b>Distance:</b> {ngo.get('distance', 'N/A')} km</p>
                <p style="margin: 5px 0;"><b>Contact:</b> {ngo.get('contact_person', 'N/A')}</p>
                <p style="margin: 5px 0;"><b>Phone:</b> {ngo.get('phone', 'N/A')}</p>
                <p style="margin: 5px 0;"><b>Email:</b> {ngo.get('email', 'N/A')}</p>
                <p style="margin: 5px 0;"><b>Address:</b> {ngo.get('address', 'N/A')}</p>
            </div>
            """
            folium.Marker(
                ngo['coordinates'],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{ngo.get('org_name', 'NGO')} - {ngo.get('distance', 'N/A')} km",
                icon=folium.Icon(color='green', icon='heart', prefix='fa')
            ).add_to(m)
    
    return m

# --- STREAMLIT PAGE SETUP ---
st.set_page_config(page_title="Donor Portal", page_icon="🍓", layout="wide")

# --- LOGIN / SIGNUP ---
if not st.session_state.donor_logged_in:
    st.markdown("""
    <div class="main-header">
        <h1>🍓 Food Donor Portal 🍓</h1>
        <p style="font-size: 1.5rem; font-weight: 500; margin: 0.5rem 0 0 0;">Share Your Surplus, Feed Someone in Need</p>
    </div>
    """, unsafe_allow_html=True)

    login_tab, signup_tab = st.tabs(["🔐 Login", "📝 Sign Up"])

    with login_tab:
        st.subheader("Login to Your Account")
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔒 Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            if not db:
                st.error("❌ Database connection failed.")
            else:
                success, user_data = verify_login(email, password)
                if success:
                    st.session_state.donor_logged_in = True
                    st.session_state.user = user_data
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")

    with signup_tab:
        st.subheader("Create a New Account")
        with st.form("signup_form"):
            name = st.text_input("👤 Full Name")
            email = st.text_input("📧 Email")
            password = st.text_input("🔒 Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                if not name or not email or not password:
                    st.error("❌ All fields are required!")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match!")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters long!")
                else:
                    if not db:
                        st.error("❌ Database connection failed.")
                    else:
                        success, msg = create_user(name, email, password)
                        if success:
                            st.success("✅ Account created successfully! Please log in.")
                        else:
                            st.error(f"❌ {msg}")

# --- DASHBOARD AFTER LOGIN ---
if st.session_state.get("donor_logged_in"):
    with st.sidebar:
        st.success(f"Welcome, {st.session_state.user.get('name', 'User')}!")
        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown("""
    <div class="main-header">
        <h1>🍲 Donate Food</h1>
        <p>Make a difference today - Share your surplus food</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["💖 Donate Food", "🗺️ Find Nearby NGOs", "📜 My Donations"])

    # --- TAB 1: DONATION FORM ---
    with tab1:
        st.subheader("💖 Donation Form")
        with st.form("donation_form"):
            food_name = st.text_input("🍽️ Food Name*")
            quantity = st.number_input("📦 Quantity (servings)*", min_value=1)
            food_type = st.selectbox("🥗 Food Type*", ["Veg", "Non-Veg", "Mixed"])
            expiry_date = st.date_input("📅 Expiry Date*", min_value=datetime.now().date())
            contact_number = st.text_input("📞 Contact Number*")
            address = st.text_input("📍 Address*")
            description = st.text_area("📝 Description (optional)")
            donate = st.form_submit_button("💝 Donate Food")

            if donate:
                if not all([food_name, contact_number, address]):
                    st.error("❌ Please fill in all required fields!")
                else:
                    donation_data = {
                        "donor_name": st.session_state.user.get("name"),
                        "donor_email": st.session_state.user.get("email"),
                        "food_name": food_name,
                        "quantity": quantity,
                        "food_type": food_type,
                        "expiry_date": expiry_date.isoformat(),
                        "contact_number": contact_number,
                        "address": address,
                        "description": description,
                        "status": "Pending",
                        "created_at": firestore.SERVER_TIMESTAMP,
                    }
                    if save_donation_to_firebase(donation_data):
                        st.success("✅ Thank you for your generous donation!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to save donation.")

    # --- TAB 2: FIND NEARBY NGOs ---
    with tab2:
        st.subheader("🗺️ Find Nearby NGOs")
        st.write("Enter your address to find NGOs near you that can collect your food donation.")
        
        st.info("💡 **Tip:** Include city name for better results (e.g., 'Adhartal, Jabalpur' or 'Ranjhi, Jabalpur')")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search_address = st.text_input(
                "📍 Enter Your Address", 
                key="search_address",
                placeholder="e.g., Adhartal, Jabalpur"
            )
        with col2:
            max_dist = st.number_input("Max Distance (km)", min_value=1, max_value=50, value=15)
        
        if st.button("🔍 Search Nearby NGOs", use_container_width=True):
            if search_address:
                with st.spinner("Finding nearby NGOs... This may take a moment."):
                    donor_coords, nearby_ngos = find_nearby_ngos(search_address, max_dist)
                    
                    if donor_coords is None:
                        st.error("❌ Could not find your address. Please try:")
                        st.write("- Adding city name (e.g., 'Adhartal, Jabalpur')")
                        st.write("- Using a more specific address")
                        st.write("- Checking spelling")
                    elif len(nearby_ngos) == 0:
                        st.warning(f"⚠️ No NGOs found within {max_dist} km of your location.")
                        st.info("💡 Try increasing the maximum distance or check if NGOs have registered with complete addresses.")
                    else:
                        st.success(f"✅ Found {len(nearby_ngos)} NGO(s) near you!")
                        
                        st.subheader("📍 NGO Locations Map")
                        ngo_map = create_ngo_map(donor_coords, nearby_ngos)
                        st_folium(ngo_map, width=1000, height=500, returned_objects=[])
                        
                        st.subheader("📋 Nearby NGOs List")
                        for i, ngo in enumerate(nearby_ngos, 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="ngo-card">
                                    <h3>🏢 {i}. {ngo.get('org_name', 'NGO')}</h3>
                                    <p><strong>📍 Distance:</strong> {ngo.get('distance', 'N/A')} km away</p>
                                    <p><strong>👤 Contact Person:</strong> {ngo.get('contact_person', 'N/A')}</p>
                                    <p><strong>📞 Phone:</strong> {ngo.get('phone', 'N/A')}</p>
                                    <p><strong>📧 Email:</strong> {ngo.get('email', 'N/A')}</p>
                                    <p><strong>📫 Address:</strong> {ngo.get('address', 'N/A')}</p>
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.info("👆 Please enter your address to search for nearby NGOs.")

    # --- TAB 3: DONATION HISTORY ---
    with tab3:
        st.subheader("📜 My Donation History")

        user_email = st.session_state.user.get("email")
        if user_email:
            donations = get_donations_by_email(user_email)

            if not donations:
                st.info("You haven't made any donations yet.")
            else:
                for donation in donations:
                    created_at = "Pending"
                    if 'created_at' in donation and donation['created_at']:
                        ts = donation['created_at']
                        if hasattr(ts, "strftime"):
                            created_at = ts.strftime("%Y-%m-%d %I:%M %p")
                        elif hasattr(ts, "to_datetime"):
                            created_at = ts.to_datetime().strftime("%Y-%m-%d %I:%M %p")
                            
                    status = donation.get("status", "Pending")
                    icon = {"Pending": "⏳", "Accepted": "✅", "Rejected": "❌"}.get(status, "📋")
                    
                    if status == "Pending":
                        status_class = "status-pending"
                    elif status == "Accepted":
                        status_class = "status-accepted"
                    else:
                        status_class = "status-clipboard"

                    with st.expander(f"**{donation['food_name']}** ({created_at})"):
                        st.markdown(f"**Status:** <span class='status-tag {status_class}'>{status} {icon}</span>", unsafe_allow_html=True)
                        
                        st.write(f"**Quantity:** {donation['quantity']} servings")
                        st.write(f"**Type:** {donation['food_type']}")
                        st.write(f"**Expires:** {donation['expiry_date']}")
                        st.write(f"**Address:** {donation['address']}")
                        if donation.get("description"):
                            st.write(f"**Notes:** {donation['description']}")
        else:
            st.error("Could not find user email to load donations.")