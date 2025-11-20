# utils/styles.py

import streamlit as st
from pathlib import Path
import os

def set_page_config():
    """Set the page configuration for the Streamlit app."""
    st.set_page_config(
        page_title="Annapurna",
        # Use your logo for the icon
        page_icon="assets/Annapurna logo.png", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

def load_css(css_file):
    """Load and inject CSS file into the Streamlit app.
    
    Args:
        css_file (str): Path to the CSS file relative to the project root.
    """
    try:
        with open(css_file, "r", encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS file {css_file}: {e}")


def apply_custom_styles():
    """Apply custom styles and customizations to the Streamlit app."""
    
    # Hide Streamlit's default menu and footer
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Apply all modern styles needed for Home.py
    modern_styles = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, .stApp {
            font-family: 'Inter', sans-serif;
        }

        /* Modern Color Scheme */
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
            min-height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
            max-width: 100% !important;
            overflow-x: hidden;
        }
        
        .main .block-container {
            max-width: 100% !important;
            /* Add bottom padding for footer */
            padding: 1rem 2rem 12rem !important; 
            margin: 0 !important;
            width: 100% !important;
        }
        
        /* Sidebar Modern Styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
            border-right: 1px solid rgba(30, 41, 59, 0.1) !important;
        }
        
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown p {
            color: #374151 !important;
        }

        [data-testid="stSidebar"] .stImage img {
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        
        /* Main Content Headings */
        .stApp [data-testid="stMarkdownContainer"] h1,
        .stApp [data-testid="stMarkdownContainer"] h2,
        .stApp [data-testid="stMarkdownContainer"] h3 {
            color: #1e293b !important;
            font-weight: 700 !important;
        }
        
        .stApp [data-testid="stMarkdownContainer"] p {
            color: #4b5563 !important;
            line-height: 1.7;
        }

        /* Gallery Image Styling */
        .stImage img {
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .stImage img:hover {
            transform: scale(1.03);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }

        /* Floating Chat Button */
        .chat-button {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
            color: white !important;
            padding: 16px 24px;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
            font-size: 16px;
            font-weight: 600;
            z-index: 1000;
            transition: all 0.3s ease;
            border: none;
        }
        
        .chat-button:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.4);
        }
        
        /* Community/Gallery Titles from Home.py */
        .community-main-title {
            text-align: center;
            font-family: 'Serif', Georgia, serif;
            color: #010203 !important;
            font-weight: 900 !important;
            font-size: 3.5rem !important;
            margin: 2rem 0 !important;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            letter-spacing: -1px;
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            padding: 2.5rem 3rem;
            border-radius: 25px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        }
        .community-subtitle {
            text-align: center;
            font-family: 'Serif', Georgia, serif;
            color: #010203 !important;
            font-weight: 400 !important;
            font-size: 2.2rem !important;
            margin-bottom: 1.5rem !important;
        }
        </style>
    """
    st.markdown(modern_styles, unsafe_allow_html=True)