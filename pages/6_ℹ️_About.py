import streamlit as st
import base64

# Page configuration
st.set_page_config(
    page_title="About Annapurna",
    page_icon="✨",
    layout="wide"
)

# Custom CSS with modern blue theme
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
}

.main-header p {
   font-size: 1.3rem !important;
   font-weight: 700 !important;
   opacity: 0.9;
   margin: 0 !important;
   color: white !important; 
}

/* Mission card - modern blue theme */
.mission-card {
    background: rgba(59, 130, 246, 0.05);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 15px;
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-left: 4px solid #3b82f6;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1);
}

.mission-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.2);
    border-left-color: #2563eb;
}

.mission-card h3 {
    color: #1e293b !important;
    font-weight: 700 !important;
    margin-bottom: 1rem !important;
}

.mission-card p {
    color: #4b5563 !important;
    line-height: 1.7;
}

/* Vision card - modern teal theme */
.vision-card {
    background: rgba(16, 185, 129, 0.05);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 15px;
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-left: 4px solid #10b981;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.1);
}

.vision-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.2);
    border-left-color: #059669;
}

.vision-card h3 {
    color: #1e293b !important;
    font-weight: 700 !important;
    margin-bottom: 1rem !important;
}

.vision-card p {
    color: #4b5563 !important;
    line-height: 1.7;
}

/* Purpose card - modern purple theme */
.purpose-card {
    background: rgba(139, 92, 246, 0.05);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 15px;
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-left: 4px solid #8b5cf6;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px -1px rgba(139, 92, 246, 0.1);
}

.purpose-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(139, 92, 246, 0.2);
    border-left-color: #7c3aed;
}

.purpose-card h3 {
    color: #1e293b !important;
    font-weight: 700 !important;
    margin-bottom: 1rem !important;
}

.purpose-card p {
    color: #4b5563 !important;
    line-height: 1.7;
}

/* Stats container with glassmorphism */
.stats-container {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(15px);
    padding: 3rem 2rem;
    border-radius: 20px;
    margin: 2rem 0;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 
        0 10px 15px -3px rgba(0, 0, 0, 0.1),
        0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.stats-container h3 {
    background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700 !important;
}

.impact-number {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Enhanced button styling */
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

/* Process steps styling */
.stApp h4 {
    color: #1e293b !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}

/* Metric container styling */
.stApp [data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.stApp [data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    border-color: rgba(59, 130, 246, 0.2);
}

/* Section headings */
.stApp h2, .stApp h3 {
    color: #1e293b !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
}

/* Body text */
.stApp p, .stApp li {
    color: #4b5563;
    line-height: 1.7;
}

/* Core values section styling */
.stApp strong {
    color: #1e293b !important;
    font-weight: 700 !important;
}

/* Video and image info styling */
.stApp .stInfo {
    background: rgba(59, 130, 246, 0.05) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 12px !important;
    color: #1e293b !important;
}
</style>
""", unsafe_allow_html=True)

def get_image_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Main header
st.markdown("""
<div class="main-header">
    <h1>🌸About Annapurna🌸</h1>
    <p>Connecting Hearts, Sharing Meals, Building Communities</p>
</div>
""", unsafe_allow_html=True)

# Introduction section
st.markdown("""
### Welcome to Annapurna🌸

In a world where approximately **828 million people** go to bed hungry while **1.3 billion tons** of food is wasted annually, 
Annapurna stands as a beacon of hope. We are more than just a platform – we are a movement dedicated to creating a 
sustainable food ecosystem where surplus becomes sustenance.
""")

st.markdown("---")

# Mission, Vision, Purpose section with enhanced styling
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="mission-card">
        <h3>🎯 Our Mission</h3>
        <p>To bridge the gap between food surplus and food scarcity by creating a seamless, technology-driven platform 
        that connects donors with NGOs and volunteers. We transform food waste into food security through innovation 
        and community collaboration.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="vision-card">
        <h3>👁️ Our Vision</h3>
        <p>A world without hunger, where no edible food goes to waste. We envision a community where everyone has 
        access to nutritious meals, regardless of their economic status, and where environmental sustainability 
        goes hand in hand with social responsibility.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="purpose-card">
        <h3>💡 Our Purpose</h3>
        <p>To empower communities to fight food insecurity locally. We provide the tools for individuals and 
        organizations to make a tangible impact, creating a network of compassion that extends from households 
        to enterprises.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# How it works section
st.subheader("🔄 How Annapurna Works")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    #### 1. 📱 Register
    - Donors, NGOs, and volunteers sign up
    - Simple verification process
    - Build your profile
    """)

with col2:
    st.markdown("""
    #### 2. 🤝 Connect
    - Smart matching algorithm
    - Location-based connections
    - Real-time notifications
    """)

with col3:
    st.markdown("""
    #### 3. 🚚 Coordinate
    - Schedule pickups and deliveries
    - Track food distribution
    - Ensure food safety
    """)

with col4:
    st.markdown("""
    #### 4. 📊 Impact
    - Measure results together
    - Share success stories
    - Build community
    """)

st.markdown("---")

# Impact statistics
try:
    # Get banner as base64
    banner_path = "assets/Banner - Annapurna.png"
    banner_b64 = get_image_as_base64(banner_path)
    st.markdown(f"""
    <div style="
        background-image: url('data:image/png;base64,{banner_b64}');
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
        width: 100%;
        height: 60vh;
        min-height: 200px;
        margin: 0.5rem 0 1rem 0;
        border-radius: 5px;
        box-shadow: 0 10px 10px -3px rgba(0, 0, 0, 0.2);
    ">
    </div>
    """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error loading banner: {str(e)}")
    st.markdown("""
    <div class="stats-container">
        <h3 style="text-align: center; margin-bottom: 2rem; color: #1e293b !important;">📈 Our Growing Impact</h3>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🍽️ Meals Distributed",
        value="50,000+",
        delta="↗️ Growing daily"
    )

with col2:
    st.metric(
        label="🏢 Partner Organizations",
        value="150+",
        delta="↗️ 25 this month"
    )

with col3:
    st.metric(
        label="🌱 Food Waste Reduced",
        value="25 tons",
        delta="↗️ 5 tons this week"
    )

with col4:
    st.metric(
        label="🤝 Active Volunteers",
        value="500+",
        delta="↗️ 50 new this month"
    )

st.markdown("---")

# Core values section
st.subheader("💎 Our Core Values")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🌍 Sustainability**  
    Environmental responsibility drives every decision we make.
    
    **🤝 Community**  
    Building stronger, more connected neighborhoods.
    
    **💫 Innovation**  
    Using technology to solve age-old problems.
    """)

with col2:
    st.markdown("""
    **🎯 Transparency**  
    Open, honest communication in all our operations.
    
    **❤️ Compassion**  
    Leading with empathy and understanding.
    
    **⚡ Efficiency**  
    Maximizing impact while minimizing waste.
    """)

st.markdown("---")

# Team section
st.subheader("👥 Meet Our Team")
st.markdown("""
Annapurna is built by a passionate team of developers, social workers, and community organizers who believe 
technology can be a force for good. Our diverse backgrounds unite around a common goal: ensuring no one goes 
hungry while perfectly good food goes to waste.
""")

# Call to action
st.markdown("---")
st.subheader("🚀 Join the Movement")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏢 Become a Donor", use_container_width=True):
        st.success("Ready to start donating? Contact us to get started!")

with col2:
    if st.button("🤝 Volunteer with Us", use_container_width=True):
        st.success("Thank you for your interest in volunteering!")

with col3:
    if st.button("🏛️ Partner NGO", use_container_width=True):
        st.success("Let's work together to fight hunger!")

# Video sections
st.markdown("---")
st.subheader("🎬 Discover Annapurna in Action")

# Introduction video section
st.markdown("### ❤️ Annapurna commencement Video")
st.markdown("Get to know Annapurna and learn how our platform is revolutionizing food distribution:")

try:
    st.video("assets/Introduction.mp4")
except:
    st.info("❤️ Annapurna commencement video will be displayed here: assets/Introduction.mp4")

st.markdown("---")

# Action video section  
st.markdown("### 🎥 See Our Impact in Action")
st.markdown("Watch real stories of how Annapurna is making a difference in communities:")

try:
    st.video("assets/Action.mp4")
except:
    st.info("📹 Action/impact video will be displayed here: assets/Action.mp4")

st.markdown("---")
