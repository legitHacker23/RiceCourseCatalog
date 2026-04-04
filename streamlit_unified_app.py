#!/usr/bin/env python3
"""
Rice University Academic Advisor - Unified Streamlit Application
================================================================

This is the main unified Streamlit application that provides a comprehensive
academic advising system for Rice University students. The app combines
multiple intelligence levels (Basic, Enhanced, Expert) to provide personalized
course recommendations and academic planning.

Key Features:
- Hierarchical course selection interface (Department -> Courses)
- Intelligent chat interface with GPT-4 integration
- Balanced schedule generation with prerequisite checking
- Multi-semester academic planning
- Real-time course filtering and search
- Student profile management

Architecture:
- Uses the unified advisor system (app/unified_advisor.py)
- Loads organized course data from data/organized/rice_organized_data.json
- Implements fallback schedule building when main system is unavailable
- Provides multiple intelligence levels for different types of queries

Author: Rice Course Assistant Team
Last Updated: 2024-07-15
"""

import streamlit as st
import pandas as pd
import time
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our unified system components
try:
    from app.unified_advisor import UnifiedAdvisor
    from app.intelligence_router import IntelligenceLevel
    from app.response_formatter import UnifiedResponse
    UNIFIED_SYSTEM_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Unified system not available: {e}")
    UNIFIED_SYSTEM_AVAILABLE = False

# ================================================================
# PAGE CONFIGURATION AND STYLING
# ================================================================

# Set up the main page configuration
st.set_page_config(
    page_title="🦉 Rice Academic Advisor",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful Rice University themed design
# Using official Rice colors: Rice Blue (#002469) and Rice Gray (#5E6062)
st.markdown("""
<style>
    /* Import Rice-inspired fonts */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@300;400;600;700&display=swap');
    
    /* Main app background with Rice theme */
    .main > div {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        min-height: 100vh;
    }
    
    /* Main header styling with Rice blue */
    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        color: #002469;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,36,105,0.1);
        letter-spacing: -1px;
    }
    
    /* Subtitle styling with Rice theme */
    .subtitle {
        font-family: 'Lato', sans-serif;
        font-size: 1.3rem;
        color: #5E6062;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    
    /* Rice owl mascot styling */
    .rice-owl-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem;
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%);
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0,36,105,0.3);
        color: white;
    }
    
    /* Intelligence level indicators with Rice theming */
    .intelligence-indicator {
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,36,105,0.15);
        font-family: 'Lato', sans-serif;
        transition: all 0.3s ease;
    }
    
    .intelligence-indicator:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,36,105,0.25);
    }
    
    /* Rice-themed intelligence levels */
    .basic-level {
        background: linear-gradient(135deg, #e8f4f8 0%, #d1e7dd 100%);
        color: #002469;
        border-left: 5px solid #002469;
    }
    
    .enhanced-level {
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
        color: #5E6062;
        border-left: 5px solid #ffa726;
    }
    
    .expert-level {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        color: #002469;
        border-left: 5px solid #4caf50;
    }
    
    /* Rice-themed quick action buttons */
    .quick-action-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    /* Individual quick action button styling with Rice theme */
    .quick-action-btn {
        padding: 1.5rem;
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%);
        color: white;
        border: none;
        border-radius: 15px;
        cursor: pointer;
        text-align: center;
        font-weight: 600;
        font-family: 'Lato', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(0,36,105,0.25);
    }
    
    .quick-action-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0,36,105,0.4);
        background: linear-gradient(135deg, #1a4b8c 0%, #002469 100%);
    }
    
    /* Statistics and info cards with Rice styling */
    .stats-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        border-left: 6px solid #002469;
        box-shadow: 0 8px 25px rgba(0,36,105,0.15);
        font-family: 'Lato', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stats-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0,36,105,0.25);
    }
    
    /* Feature highlights with Rice theme */
    .feature-highlight {
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #ffa726;
        box-shadow: 0 4px 12px rgba(255,167,38,0.2);
        font-family: 'Lato', sans-serif;
    }

    /* Feature highlights with Blue Rice theme */
    .feature-highlight-blue {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #002469;
        box-shadow: 0 4px 12px rgba(0,36,105,0.2);
        font-family: 'Lato', sans-serif;
    }
    
    /* Chat message styling with Rice theme */
    .chat-message {
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,36,105,0.1);
        font-family: 'Lato', sans-serif;
    }
    
    .user-message {
        background: linear-gradient(135deg, #e8f4f8 0%, #d1e7dd 100%);
        margin-left: 15%;
        border-left: 4px solid #002469;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        margin-right: 15%;
        border-left: 4px solid #5E6062;
    }
    
    /* Performance metrics grid with Rice styling */
    .performance-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    /* Individual metric cards with Rice theme */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,36,105,0.15);
        border-top: 5px solid #002469;
        font-family: 'Lato', sans-serif;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,36,105,0.25);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #002469;
        font-family: 'Playfair Display', serif;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #5E6062;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    /* Rice-specific styling elements */
    .rice-branding {
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,36,105,0.3);
        font-family: 'Lato', sans-serif;
    }
    
    .rice-motto {
        font-size: 1.2rem;
        font-style: italic;
        color: #e8f4f8;
        margin-top: 1rem;
        font-family: 'Playfair Display', serif;
    }
    
    /* Sidebar styling with Rice theme */
    .css-1d391kg {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 3px solid #002469;
    }
    
    /* Course cards with Rice styling */
    .course-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #002469;
        box-shadow: 0 6px 20px rgba(0,36,105,0.15);
        font-family: 'Lato', sans-serif;
        transition: all 0.3s ease;
    }
    
    .course-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,36,105,0.25);
    }
    
    .course-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #002469;
        margin-bottom: 0.5rem;
        font-family: 'Playfair Display', serif;
    }
    
    .course-dept {
        color: #5E6062;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    /* Rice success messages */
    .rice-success {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        color: #2e7d32;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
        font-family: 'Lato', sans-serif;
    }
    
    /* Rice warning messages */
    .rice-warning {
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
        color: #f57c00;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffa726;
        margin: 1rem 0;
        font-family: 'Lato', sans-serif;
    }
    
    /* Rice error messages */
    .rice-error {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        color: #c62828;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
        font-family: 'Lato', sans-serif;
    }
    
    /* Schedule generation styling */
    .schedule-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: 0 8px 25px rgba(0,36,105,0.15);
        border-top: 5px solid #002469;
        font-family: 'Lato', sans-serif;
    }
    
    .schedule-semester {
        font-size: 1.4rem;
        font-weight: 600;
        color: #002469;
        margin-bottom: 1rem;
        font-family: 'Playfair Display', serif;
    }
    
    /* Rice-themed buttons */
    .rice-button {
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%);
        color: white;
        padding: 0.8rem 2rem;
        border: none;
        border-radius: 25px;
        font-weight: 600;
        font-family: 'Lato', sans-serif;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,36,105,0.3);
    }
    
    .rice-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,36,105,0.4);
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%) !important;
        color: white !important;
        border-color: #002469 !important;
    }
    
    /* Rice loading spinner */
    .rice-spinner {
        border: 4px solid #e8f4f8;
        border-top: 4px solid #002469;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 1rem auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Rice owl animation */
    .owl-icon {
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* Style the advisor section container */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) {
        background: white !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        border-radius: 20px !important;
    }
    
    /* Style elements within the advisor container */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stMarkdownContainer"] h3 {
        margin-top: 0 !important;
        margin-bottom: 1rem !important;
        color: #002469 !important;
    }
    
    /* Style the selectbox within the advisor container */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stSelectbox"] {
        margin-bottom: 1rem !important;
        margin-top: -0.25rem !important;
        margin-left: -15px !important;
        padding-left: 0 !important;
    }
    
    /* Target the element container that holds the selectbox */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) div[data-testid="stElementContainer"]:has([data-testid="stSelectbox"]) {
        margin-top: -1rem !important;
        transform: translateY(-15px) !important;
    }
    
    /* Alternative selector for the selectbox container */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) > div[data-testid="stElementContainer"] {
        margin-top: -1rem !important;
        padding-top: 0 !important;
    }
    
    /* Style the selectbox dropdown */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stSelectbox"] > div {
        background: white !important;
    }
    
    /* Style only the selectbox label text to match the heading color */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stSelectbox"] label {
        color: #5E6062 !important;
        font-weight: 600 !important;
    }
    
    /* Style the entire Focus text line to match the heading color */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stMarkdownContainer"] p {
        color: #5E6062 !important;
    }
    
    /* Rice info messages with blue theme */
    .rice-info {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #5E6062;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #002469;
        margin: 1rem 0;
        font-family: 'Lato', sans-serif;
    }
    
    /* Position the Focus content container to move it up */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) div[data-testid="stMarkdownContainer"]:has(.rice-info) {
        margin-top: -1.5rem !important;
        position: relative !important;
        top: -15px !important;
    }
    
    /* Alternative selector for the Focus content */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) > div:nth-child(3) {
        margin-top: -1.5rem !important;
        transform: translateY(-20px) !important;
    }
    
    /* Direct targeting of rice-info elements in sidebar */
    section[data-testid="stSidebar"] .rice-info {
        margin-top: -2.5rem !important;
        margin-bottom: 0.25rem !important;
        width: calc(100% - 2rem) !important;
        box-sizing: border-box !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /** Base style for sidebar buttons to prevent shrinking on hover */
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] .rice-button,
    .stButton > button {
        font-size: 1rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        border-width: 2px !important;
        box-sizing: border-box !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.3s ease !important;
    }
    
    /* Force Streamlit sidebar buttons to use Rice blue on hover, keeping text size consistent */
    section[data-testid="stSidebar"] button:hover,
    section[data-testid="stSidebar"] .rice-button:hover,
    .stButton > button:hover {
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%) !important;
        color: white !important;
        border-color: #002469 !important;
        box-shadow: 0 6px 20px rgba(0,36,105,0.4) !important;
    }
    
    /* Move Quick Switch buttons inside the container visually */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(.stats-card:has(h4:contains("Quick Switch"))) + div {
        margin-top: -1rem !important;
        padding: 0 1rem 1rem 1rem !important;
        background: white !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid #e0e7ef !important;
        border-top: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Style Quick Actions buttons specifically with high specificity */
    div[data-testid="stTabs"] div[data-testid="stTabPanel"] div[data-testid="stColumns"] button[kind="primary"],
    div[data-testid="stTabs"] div[data-testid="stTabPanel"] div[data-testid="stColumns"] button[kind="secondary"],
    div[data-testid="stTabs"] div[data-testid="stTabPanel"] div[data-testid="stColumns"] button {
        font-size: 1rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        border-width: 2px !important;
        box-sizing: border-box !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.3s ease !important;
    }
    
    /* Apply Rice blue hover effect with maximum specificity to override red */
    div[data-testid="stTabs"] div[data-testid="stTabPanel"] div[data-testid="stColumns"] button[kind="primary"]:hover,
    div[data-testid="stTabs"] div[data-testid="stTabPanel"] div[data-testid="stColumns"] button[kind="secondary"]:hover,
    div[data-testid="stTabs"] div[data-testid="stTabPanel"] div[data-testid="stColumns"] button:hover,
    div[data-testid="stTabs"] div[data-testid="stTabPanel"] div[data-testid="stColumns"] div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%) !important;
        background-color: #002469 !important;
        color: white !important;
        border-color: #002469 !important;
        box-shadow: 0 6px 20px rgba(0,36,105,0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Specifically target Quick Actions tab (exclude System Status) */
    div[data-testid="stTabs"] div[data-testid="stTabPanel"]:not(:last-child) button:hover {
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%) !important;
        background-color: #002469 !important;
        color: white !important;
        border-color: #002469 !important;
        box-shadow: 0 6px 20px rgba(0,36,105,0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Target ALL buttons in tabs, then exclude System Status later */
    [data-testid="stTabs"] button:hover {
        background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%) !important;
        background-color: #002469 !important;
        color: white !important;
        border: 2px solid #002469 !important;
        box-shadow: 0 6px 20px rgba(0,36,105,0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Exclude System Status buttons specifically */
    [data-testid="stTabs"] [data-testid="stTabPanel"]:last-child button:hover {
        background: revert !important;
        background-color: revert !important;
        color: revert !important;
        border: revert !important;
        box-shadow: revert !important;
        transform: revert !important;
    }
</style>
""", unsafe_allow_html=True)

# ================================================================
# CORE SYSTEM LOADING AND INITIALIZATION
# ================================================================

@st.cache_resource
def load_unified_advisor():
    """
    Load the unified advisor system with caching for performance.
    
    This function initializes the main UnifiedAdvisor class that handles
    all the intelligence routing, course recommendations, and response
    formatting. It's cached to avoid reloading on every interaction.
    
    Returns:
        UnifiedAdvisor: The initialized advisor system, or None if unavailable
    """
    if not UNIFIED_SYSTEM_AVAILABLE:
        return None
    
    try:
        advisor = UnifiedAdvisor()
        return advisor
    except Exception as e:
        st.error(f"❌ Failed to load unified advisor: {e}")
        return None

# ================================================================
# MAJOR SELECTION INTERFACE
# ================================================================

def setup_major_selection() -> str:
    """
    Create an intuitive major selection interface for students.
    
    This function provides three different ways for students to select
    their major:
    1. Popular majors (most common at Rice)
    2. Browse by school/college
    3. Search through all majors
    
    The interface shows helpful statistics and provides context about
    each major's school affiliation.
    
    Returns:
        str: The selected major name
    """
    
    # Rice University majors organized by school/college
    # This data structure represents the actual academic organization at Rice
    RICE_MAJORS = {
        "🏗️ Engineering": [
            "Bioengineering", "Chemical & Biomolecular Engineering", "Civil & Environmental Engineering",
            "Computational & Applied Mathematics", "Computer Science", "Electrical & Computer Engineering",
            "Materials Science & NanoEngineering", "Mechanical Engineering"
        ],
        "🎭 Humanities": [
            "African & African American Studies", "Art History", "Classical Studies", "English",
            "French Studies", "German Studies", "History", "Jewish Studies", "Linguistics",
            "Music", "Philosophy", "Religion", "Spanish & Portuguese", "Theatre", "Art"
        ],
        "🌍 Social Sciences": [
            "Anthropology", "Economics", "Political Science", "Psychology", "Sociology",
            "Managerial Economics & Organizational Sciences"
        ],
        "🔬 Natural Sciences": [
            "Astronomy", "Biosciences", "Chemistry", "Earth, Environmental & Planetary Sciences",
            "Mathematics", "Physics & Astronomy", "Statistics", "Neuroscience", "Data Science"
        ],
        "🏛️ Architecture": ["Architecture"],
        "🎵 Music": ["Music"],
        "💼 Professional": ["Business", "Accounting"],
        "🌐 Interdisciplinary": [
            "Applied Physics", "Cinema & Media Studies", "Civic Leadership", "Education",
            "Energy & Water Sustainability", "Environmental Studies", "Global Affairs",
            "Liberal Studies", "Medical Humanities", "Social Policy Analysis"
        ]
    }
    
    # Most popular majors at Rice University
    # These are the majors students most commonly select
    POPULAR_MAJORS = [
        "Computer Science", "Economics", "Psychology", "Bioengineering", 
        "Mathematics", "English", "Political Science", "Chemistry"
    ]
    
    st.sidebar.markdown("**📚 Select Your Major**")
    
    # Show helpful statistics about available majors
    total_majors = sum(len(majors) for majors in RICE_MAJORS.values())
    st.sidebar.caption(f"💡 {total_majors} majors available across {len(RICE_MAJORS)} schools")
    
    # Let students choose their selection method
    selection_method = st.sidebar.radio(
        "How would you like to select?",
        ["🔥 Popular Majors", "🏫 Browse by School", "🔍 Search All Majors"],
        help="Choose the easiest way to find your major"
    )
    
    # Method 1: Popular majors (quickest for common majors)
    if selection_method == "🔥 Popular Majors":
        major = st.sidebar.selectbox(
            "Popular Majors",
            POPULAR_MAJORS + ["Other"],
            help="Most common majors at Rice"
        )
        
    # Method 2: Browse by school (organized by academic structure)
    elif selection_method == "🏫 Browse by School":
        # Calculate and show statistics for each school
        school_stats = {school: len(majors) for school, majors in RICE_MAJORS.items()}
        
        # Create school options with major counts for context
        school_options = []
        for school, count in school_stats.items():
            school_options.append(f"{school} ({count} majors)")
        
        # Let student select school first
        school_selection = st.sidebar.selectbox(
            "Select School/College",
            school_options,
            help="Choose your school first (number of majors shown)"
        )
        
        # Extract the actual school name from the formatted option
        school = school_selection.split(" (")[0]
        
        # Show a preview of majors in the selected school
        st.sidebar.markdown(f"**{school} offers {len(RICE_MAJORS[school])} majors:**")
        preview_text = ", ".join(RICE_MAJORS[school][:3])
        if len(RICE_MAJORS[school]) > 3:
            preview_text += f" and {len(RICE_MAJORS[school]) - 3} more..."
        st.sidebar.caption(preview_text)
        
        # Now let student select specific major within the school
        major = st.sidebar.selectbox(
            f"Major in {school}",
            RICE_MAJORS[school] + ["Other"],
            help=f"Select your major from {school}"
        )
        
    # Method 3: Search all majors (for students who know what they want)
    else:  # Search All Majors
        # Create a flat list of all majors across all schools
        all_majors = []
        for school_majors in RICE_MAJORS.values():
            all_majors.extend(school_majors)
        all_majors = sorted(set(all_majors))  # Remove duplicates and sort alphabetically
        
        # Provide search functionality
        search_term = st.sidebar.text_input(
            "🔍 Search for your major",
            placeholder="Type to search...",
            help="Start typing to filter majors"
        )
        
        # Filter majors based on search term
        if search_term:
            filtered_majors = [m for m in all_majors if search_term.lower() in m.lower()]
            if not filtered_majors:
                st.sidebar.warning("No majors found matching your search")
                filtered_majors = all_majors
            else:
                st.sidebar.success(f"Found {len(filtered_majors)} majors matching '{search_term}'")
        else:
            filtered_majors = all_majors
        
        # Show the filtered list of majors
        major = st.sidebar.selectbox(
            f"All Majors ({len(filtered_majors)} shown)",
            filtered_majors + ["Other"],
            help="All available majors at Rice"
        )
    
    # Show additional information about the selected major
    if major and major != "Other":
        # Find which school this major belongs to
        major_school = None
        for school, majors in RICE_MAJORS.items():
            if major in majors:
                major_school = school
                break
        
        # Display confirmation with school affiliation
        if major_school:
            st.sidebar.success(f"✅ {major} ({major_school})")
        
        # Show helpful tip for popular majors
        if major in POPULAR_MAJORS:
            st.sidebar.info("💡 This is a popular major! Great choice!")
    
    return major

# ================================================================
# COURSE SELECTION INTERFACE
# ================================================================

def create_balanced_schedule(completed_courses: List[str], all_departments: Dict, target_credits: int = 15) -> Dict:
    """
    Create a balanced, realistic schedule with courses from different departments.
    
    This function generates a well-balanced semester schedule by:
    1. Analyzing the student's current level based on completed courses
    2. Prioritizing appropriate-level courses from core departments
    3. Ensuring no more than 2 courses per department for balance
    4. Following typical Rice University course progressions
    5. Validating prerequisites and course availability
    
    Args:
        completed_courses (List[str]): List of course codes the student has completed
        all_departments (Dict): Dictionary of all department data with courses
        target_credits (int): Target number of credits for the schedule (default: 15)
    
    Returns:
        Dict: Schedule summary with courses, credits, departments, and balance metrics
    """
    
    # Define typical freshman/sophomore course progressions (Rice-specific)
    # These represent the normal sequence students follow at Rice University
    recommended_progressions = {
        'freshman': {
            'COMP': ['COMP 140', 'COMP 182'],  # Intro programming sequence
            'MATH': ['MATH 101', 'MATH 102', 'MATH 211'],  # Calculus sequence
            'PHYS': ['PHYS 101', 'PHYS 102'],  # Physics sequence
            'CHEM': ['CHEM 121', 'CHEM 122'],  # Chemistry sequence
            'ENGL': ['ENGL 103'],  # Academic writing
            'HIST': ['HIST 159'],  # Survey courses
            'ECON': ['ECON 100'],  # Intro economics
            'STAT': ['STAT 305']   # Statistics
        },
        'sophomore': {
            'COMP': ['COMP 215', 'COMP 280'],  # Advanced programming
            'MATH': ['MATH 212', 'MATH 355'],  # Advanced calculus
            'PHYS': ['PHYS 201', 'PHYS 202'],  # Advanced physics
            'CHEM': ['CHEM 211', 'CHEM 212'],  # Organic chemistry
            'ENGL': ['ENGL 201'],  # Literature
            'HIST': ['HIST 246'],  # Advanced history
            'ECON': ['ECON 212'],  # Intermediate economics
            'STAT': ['STAT 310']   # Advanced statistics
        }
    }
    
    def parse_prerequisites(prereq_text: str) -> List[str]:
        """
        Parse prerequisite text to extract course codes.
        
        This function uses regex to find course codes in prerequisite
        descriptions, handling various formats used in course catalogs.
        
        Args:
            prereq_text (str): Raw prerequisite text from course data
            
        Returns:
            List[str]: List of course codes that are prerequisites
        """
        if not prereq_text or prereq_text.strip() in ['None', 'N/A', '']:
            return []
        import re
        course_codes = re.findall(r'\b[A-Z]{2,4}\s*\d{3}\b', prereq_text.upper())
        return course_codes
    
    def is_course_available(course: Dict, completed: List[str]) -> bool:
        """
        Check if a course is available based on completed prerequisites.
        
        Args:
            course (Dict): Course data dictionary
            completed (List[str]): List of completed course codes
            
        Returns:
            bool: True if all prerequisites are met, False otherwise
        """
        prereqs = parse_prerequisites(course.get('prerequisites', ''))
        return all(prereq in completed for prereq in prereqs)
    
    # Get available courses from all departments
    available_courses = []
    for dept_code, dept_data in all_departments.items():
        # Handle different data structures (some depts have 'courses' key, others are lists)
        if isinstance(dept_data, dict) and 'courses' in dept_data:
            courses = dept_data['courses']
        else:
            courses = dept_data if isinstance(dept_data, list) else []
            
        for course in courses:
            if isinstance(course, dict):
                course_code = course.get('course_code', '')
                if course_code and course_code not in completed_courses:
                    # Filter out courses with numbers below 100 (not real Rice courses)
                    import re
                    course_num_match = re.search(r'(\d+)', course_code)
                    if course_num_match:
                        course_num = int(course_num_match.group(1))
                        if course_num < 100:  # Skip courses numbered below 100
                            continue
                    
                    # Only include courses that are actually available
                    if is_course_available(course, completed_courses):
                        available_courses.append(course)
    
    # Determine student level based on completed courses
    # This helps prioritize appropriate-level courses
    total_completed = len(completed_courses)
    if total_completed < 8:
        student_level = 'freshman'
    elif total_completed < 16:
        student_level = 'sophomore'
    else:
        student_level = 'junior'
    
    def get_course_priority(course: Dict) -> int:
        """
        Calculate priority score for a course based on various factors.
        
        Higher scores indicate higher priority for inclusion in the schedule.
        Factors considered:
        - Department importance (core departments get higher priority)
        - Course level appropriateness for student
        - Inclusion in recommended progressions
        
        Args:
            course (Dict): Course data dictionary
            
        Returns:
            int: Priority score (higher = more important)
        """
        dept = course.get('department', '')
        course_code = course.get('course_code', '')
        
        # Extract course number for level detection
        import re
        course_num_match = re.search(r'(\d+)', course_code)
        course_num = int(course_num_match.group(1)) if course_num_match else 999
        
        priority = 0
        
        # Core departments get higher priority (essential for most majors)
        if dept in ['COMP', 'MATH', 'PHYS', 'CHEM', 'ENGL']:
            priority += 10
        
        # Appropriate level courses get higher priority
        if student_level == 'freshman' and 100 <= course_num < 200:
            priority += 5
        elif student_level == 'sophomore' and 200 <= course_num < 400:
            priority += 5
        elif student_level == 'junior' and 300 <= course_num < 500:
            priority += 5
        
        # Recommended progression courses get extra priority
        if student_level in recommended_progressions:
            if course_code in recommended_progressions[student_level].get(dept, []):
                priority += 15
        
        return priority
    
    # Sort courses by priority (highest first)
    available_courses.sort(key=get_course_priority, reverse=True)
    
    # Build balanced schedule
    schedule = []
    total_credits = 0
    departments_used = set()
    
    # Select courses for the schedule
    for course in available_courses:
        # Stop if we've reached the target credits
        if total_credits >= target_credits:
            break
            
        dept = course.get('department', '')
        credits_str = course.get('credit_hours', '0')
        
        # Parse credits (handle various formats)
        try:
            credits = int(credits_str) if credits_str.isdigit() else 3
        except (ValueError, AttributeError):
            credits = 3  # Default to 3 credits if parsing fails
        
        # Don't exceed target credits by too much
        if total_credits + credits > target_credits + 2:
            continue
            
        # Additional validation for course codes
        course_code = course.get('course_code', '')
        if not course_code or len(course_code) < 6:  # Valid course codes should be like "COMP 140"
            continue
            
        # Limit courses per department for balance (max 2 per department)
        dept_count = sum(1 for c in schedule if c.get('department') == dept)
        if dept_count >= 2:  # Max 2 courses per department
            continue
        
        # Add course to schedule
        schedule.append(course)
        total_credits += credits
        departments_used.add(dept)
        
        # Stop if we have enough courses (typically 4-5 courses per semester)
        if len(schedule) >= 5:
            break
    
    # Create summary with helpful metrics
    summary = {
        'courses': schedule,
        'total_credits': total_credits,
        'departments_used': list(departments_used),
        'student_level': student_level,
        'balance_score': len(departments_used) / max(len(schedule), 1)  # Higher is more balanced
    }
    
    return summary

def setup_course_selection():
    """
    Setup improved hierarchical course selection interface.
    
    This function creates a user-friendly interface for students to select
    completed courses by:
    1. First selecting a department from a searchable dropdown
    2. Then selecting specific courses within that department
    3. Allowing multiple departments to be selected
    4. Providing course counts and helpful information
    5. Managing a cumulative list of selected courses
    
    The interface replaces the old system where students had to scroll
    through thousands of courses in one massive dropdown.
    
    Returns:
        List[str]: List of selected course codes
    """
    st.sidebar.markdown("### 📚 **Course Selection**")
    
    # Load organized data directly (same as standalone app)
    # This ensures we have access to all course data even if the main system fails
    all_departments = {}
    try:
        import json
        import os
        
        # Try to load organized data from the standard location
        if os.path.exists('data/organized/rice_organized_data.json'):
            with open('data/organized/rice_organized_data.json', 'r') as f:
                organized_data = json.load(f)
                all_departments = organized_data.get('departments', {})
        else:
            st.sidebar.warning("📂 Organized course data not found. Using fallback data.")
    except Exception as e:
        st.sidebar.error(f"Error loading course data: {e}")
    
    # Fallback: create sample departments if no data available
    # This ensures the interface still works even without data files
    if not all_departments:
        all_departments = {
            'COMP': [],
            'MATH': [],
            'PHYS': [],
            'CHEM': [],
            'HIST': [],
            'ENGL': [],
            'ECON': [],
            'STAT': []
        }
    
    # Display helpful statistics about available courses
    total_courses = sum(len(courses) for courses in all_departments.values())
    st.sidebar.caption(f"💡 {total_courses} courses across {len(all_departments)} departments")
    
    # Department selection with searchable dropdown
    st.sidebar.markdown("**🏫 Select Department Code**")
    
    # Create department options with course counts for context
    dept_options = []
    for dept_code, courses in all_departments.items():
        dept_options.append(f"{dept_code} ({len(courses)} courses)")
    
    # Sort department options alphabetically
    dept_options.sort()
    
    # Department selection dropdown (searchable by default in Streamlit)
    selected_dept_option = st.sidebar.selectbox(
        "Department (type to search)",
        ["Select a department..."] + dept_options,
        help="Choose a department to see its courses - type to search"
    )
    
    # Extract department code from the formatted option
    selected_dept = None
    if selected_dept_option != "Select a department...":
        selected_dept = selected_dept_option.split(" (")[0]
    
    # Course selection within the selected department
    selected_courses = []
    if selected_dept and selected_dept in all_departments:
        dept_courses = all_departments[selected_dept]
        
        if dept_courses:
            st.sidebar.markdown(f"**📖 {selected_dept} Courses**")
            
            # Create course options with detailed information
            course_options = []
            for course in dept_courses:
                course_code = course.get('course_code', 'N/A')
                course_title = course.get('title', 'No title')
                credit_hours = course.get('credit_hours', 'N/A')
                course_options.append(f"{course_code} - {course_title} ({credit_hours} credits)")
            
            # Course selection (searchable multiselect)
            selected_course_options = st.sidebar.multiselect(
                f"Select {selected_dept} courses (type to search)",
                course_options,
                help=f"Choose courses from {selected_dept} department - type to search"
            )
            
            # Extract just the course codes from the formatted options
            selected_courses = [opt.split(" - ")[0] for opt in selected_course_options]
            
            # Show selection summary
            if selected_courses:
                st.sidebar.success(f"✅ Selected {len(selected_courses)} courses from {selected_dept}")
        else:
            st.sidebar.info(f"No courses available in {selected_dept}")
    
    # Multi-department selection management
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔄 Add More Departments**")
    
    # Keep track of all selected courses across departments
    # This allows students to select courses from multiple departments
    if 'all_selected_courses' not in st.session_state:
        st.session_state.all_selected_courses = []
    
    # Add current selection to the total list
    if 'selected_courses' in locals() and selected_courses:
        # Remove duplicates and add new courses
        for course in selected_courses:
            if course not in st.session_state.all_selected_courses:
                st.session_state.all_selected_courses.append(course)
    
    # Display all selected courses with management options
    if st.session_state.all_selected_courses:
        st.sidebar.markdown("**📋 All Selected Courses**")
        
        # Show each course with option to remove
        for course in st.session_state.all_selected_courses:
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.write(f"• {course}")
            with col2:
                if st.button("❌", key=f"remove_{course}", help="Remove course"):
                    st.session_state.all_selected_courses.remove(course)
                    st.rerun()
        
        # Clear all courses button
        if st.sidebar.button("🗑️ Clear All", help="Clear all selected courses"):
            st.session_state.all_selected_courses = []
            st.rerun()
        
        # Show helpful summary
        st.sidebar.markdown(f"**Total: {len(st.session_state.all_selected_courses)} courses selected**")
    
    # Return the complete list of selected courses
    return st.session_state.all_selected_courses if hasattr(st.session_state, 'all_selected_courses') else []

# ================================================================
# USER PROFILE MANAGEMENT
# ================================================================

def setup_user_profile():
    """
    Setup comprehensive user profile in sidebar.
    
    This function creates a complete student profile that includes:
    1. Basic information (major, academic year)
    2. Academic performance (GPA)
    3. Completed courses (using the hierarchical selection)
    4. Career goals and interests
    5. Learning preferences
    6. Profile completeness tracking
    
    The profile is used throughout the system to provide personalized
    recommendations and appropriate course suggestions.
    
    Returns:
        Dict: Complete user profile with all entered information
    """
    st.sidebar.markdown("## 👤 **Your Academic Profile**")
    
    profile = {}
    
    # Basic Information Section
    st.sidebar.markdown("### 📋 **Basic Info**")
    profile['major'] = setup_major_selection()
    profile['current_year'] = st.sidebar.selectbox(
        "Academic Year",
        ["freshman", "sophomore", "junior", "senior"],
        help="Your current academic year"
    )
    
    # Academic Performance Section
    st.sidebar.markdown("### 📊 **Academic Performance**")
    profile['gpa'] = st.sidebar.slider(
        "GPA", 0.0, 4.0, 3.5, 0.1,
        help="Your current GPA (helps with difficulty recommendations)"
    )
    
    # Add selected advisor to profile
    profile['selected_advisor'] = st.session_state.get('selected_advisor', 'general')
    
    # Use the new improved course selection system
    profile['completed_courses'] = setup_course_selection()
    
    # Career Goals Section
    st.sidebar.markdown("### 💼 **Career Goals**")
    profile['career_goals'] = st.sidebar.multiselect(
        "Career Interests",
        ["software_engineering", "data_science", "machine_learning", "research", 
         "consulting", "finance", "cybersecurity", "product_management", 
         "startup", "academia"],
        help="Your career interests (helps with course recommendations)"
    )
    
    # Learning Preferences Section
    st.sidebar.markdown("### 🎯 **Learning Preferences**")
    profile['time_preferences'] = st.sidebar.selectbox(
        "Time Preferences",
        ["morning", "afternoon", "evening", "flexible"],
        help="When do you prefer to take classes?"
    )
    
    # Profile Completeness Tracking
    profile_completeness = calculate_profile_completeness(profile)
    st.sidebar.markdown("### 📈 **Profile Completeness**")
    st.sidebar.progress(profile_completeness)
    st.sidebar.write(f"**{profile_completeness:.0%} Complete**")
    
    # Provide helpful feedback based on completeness
    if profile_completeness < 0.5:
        st.sidebar.info("💡 Complete more of your profile for better recommendations!")
    elif profile_completeness < 0.8:
        st.sidebar.success("✅ Good profile! Add more details for ML-enhanced recommendations.")
    else:
        st.sidebar.success("🎉 Excellent profile! You'll get the best personalized recommendations.")
    
    return profile

def calculate_profile_completeness(profile: Dict) -> float:
    """
    Calculate how complete the user profile is.
    
    This function evaluates the completeness of a user's profile by
    checking various fields and assigning weights based on importance.
    
    Args:
        profile (Dict): User profile dictionary
        
    Returns:
        float: Completeness percentage (0.0 to 1.0)
    """
    completeness = 0.0
    
    # Major selection (25% weight - very important)
    if profile.get('major') and profile['major'] != 'Other':
        completeness += 0.25
    
    # Academic year (20% weight - important for course level)
    if profile.get('current_year'):
        completeness += 0.2
    
    # GPA (20% weight - helps with difficulty matching)
    if profile.get('gpa') and profile['gpa'] > 0:
        completeness += 0.2
    
    # Completed courses (25% weight - crucial for recommendations)
    if profile.get('completed_courses'):
        completeness += 0.25
    
    # Career goals (10% weight - nice to have)
    if profile.get('career_goals'):
        completeness += 0.1
    
    return min(1.0, completeness)

# ================================================================
# CHAT INTERFACE AND QUERY PROCESSING
# ================================================================

def display_intelligence_level_info():
    """
    Display information about intelligence levels.
    
    This function explains the different intelligence levels available
    in the system and their capabilities. Currently, the system uses
    Expert level (GPT-4) for all queries to ensure maximum quality.
    """
    st.markdown("## 🧠 **Always Using Expert Intelligence Level**")
    st.markdown("*Your advisor now uses GPT-4 for every query to ensure maximum quality*")
    
    # Display the expert level capabilities
    st.markdown("""
    <div class="intelligence-indicator expert-level" style="margin: 20px 0; padding: 20px; border-radius: 10px; background-color: #e8f5e8;">
        <strong>🟢 Expert Intelligence (GPT-4)</strong><br>
        <small>Maximum quality analysis for every query</small><br><br>
        • Expert-level reasoning<br>
        • Complex planning strategies<br>
        • Career optimization<br>
        • Multi-semester planning<br>
        • Advanced prerequisite analysis<br>
        • Personalized academic pathways<br>
        • ~15-20 seconds response time
        </div>
        """, unsafe_allow_html=True)

def render_unified_chat():
    """
    Render the main unified chat interface.
    
    This is the core chat interface that handles all user interactions.
    It processes queries through the unified advisor system and provides
    intelligent responses with appropriate formatting and context.
    
    The chat interface supports:
    - Natural language queries about courses and academic planning
    - Schedule building requests with balanced course selection
    - Course recommendations based on user profile
    - Multi-turn conversations with context preservation
    """
    # Rice University themed header with owl mascot
    st.markdown("""
    <div class="rice-branding">
        <div class="owl-icon" style="font-size: 4rem; margin-bottom: 1rem;">🦉</div>
        <h1 class="main-header" style="color: white; margin-bottom: 0.5rem;">Rice Academic Advisor</h1>
        <p class="subtitle" style="color: #e8f4f8; margin-bottom: 1rem;">Your Intelligent Course Planning Assistant</p>
        <div class="rice-motto">"Unconventional Wisdom" • Est. 1912</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rice-themed welcome message with advisor-specific content
    selected_advisor = st.session_state.get('selected_advisor', 'general')
    
    # Advisor-specific welcome messages
    advisor_welcome_messages = {
        'general': {
            'title': '🎓 Welcome to Rice Academic Advisor!',
            'description': 'Your comprehensive academic planning assistant for all Rice University departments',
            'features': [
                'Answers questions from any department',
                'Suggests specialized advisors for detailed guidance',
                'Cross-departmental course recommendations',
                'Distribution requirement guidance'
            ]
        },
        'computer_science': {
            'title': '💻 Welcome to Your Computer Science Advisor!',
            'description': 'Specialized in COMP, MATH, STAT, and ELEC courses for CS students',
            'features': [
                'Programming course sequences (COMP 140 → 182 → 215)',
                'Math requirements for CS (MATH 101/102, STAT 305)',
                'Software engineering career preparation'
            ]
        },
        'chemistry': {
            'title': '🧪 Welcome to Your Chemistry Advisor!',
            'description': 'Expert in CHEM courses and pre-medical requirements',
            'features': [
                'General chemistry sequence (CHEM 121/123)',
                'Organic chemistry preparation (CHEM 211/212)',
                'Pre-med requirement planning'
            ]
        },
        'physics': {
            'title': '⚛️ Welcome to Your Physics Advisor!',
            'description': 'Specialized in PHYS courses and mathematical physics',
            'features': [
                'Physics fundamentals (PHYS 101/102)',
                'Modern physics pathways (PHYS 201/202)',
                'Research preparation courses'
            ]
        },
        'mathematics': {
            'title': '🔢 Welcome to Your Mathematics Advisor!',
            'description': 'Expert in MATH, STAT, and CAAM courses',
            'features': [
                'Calculus sequences (MATH 101/102, 211/212)',
                'Statistics pathways (STAT 305/310)',
                'Applied mathematics preparation'
            ]
        },
        'business': {
            'title': '📊 Welcome to Your Business Advisor!',
            'description': 'Specialized in MGMT, ECON, and business preparation',
            'features': [
                'Economics foundations (ECON 100)',
                'Business management courses',
                'Entrepreneurship preparation'
            ]
        },
        'music': {
            'title': '🎵 Welcome to Your Music Advisor!',
            'description': 'Expert in MUSI courses from the Shepherd School of Music',
            'features': [
                'Music theory and composition',
                'Performance requirements',
                'Music career preparation'
            ]
        },
        'engineering': {
            'title': '🔧 Welcome to Your Engineering Advisor!',
            'description': 'Specialized in all engineering departments and technical courses',
            'features': [
                'Engineering fundamentals (Math, Physics)',
                'Department-specific course sequences',
                'Design project preparation'
            ]
        },
        'biosciences': {
            'title': '🧬 Welcome to Your Biosciences Advisor!',
            'description': 'Expert in BIOC, BIOS, and life sciences',
            'features': [
                'Molecular biology foundations (BIOC 201)',
                'Biology course sequences',
                'Pre-med and research preparation'
            ]
        },
        'humanities': {
            'title': '📚 Welcome to Your Humanities Advisor!',
            'description': 'Specialized in ENGL, HIST, PHIL, and liberal arts',
            'features': [
                'Writing and literature courses',
                'Philosophy and critical thinking',
                'Cultural studies pathways'
            ]
        },
        'social_sciences': {
            'title': '🌍 Welcome to Your Social Sciences Advisor!',
            'description': 'Expert in POLI, PSYC, ANTH, and social sciences',
            'features': [
                'Political science foundations (POLI 200)',
                'Psychology pathways (PSYC 101)',
                'Social research methods'
            ]
        },
        'architecture': {
            'title': '🏗️ Welcome to Your Architecture Advisor!',
            'description': 'Specialized in ARCH courses and design',
            'features': [
                'Architecture design studios',
                'Theory and history courses',
                'Professional preparation'
            ]
        },
        'pre_med': {
            'title': '⚕️ Welcome to Your Pre-Medical Advisor!',
            'description': 'Expert in medical school requirements and MCAT preparation',
            'features': [
                'Pre-med course requirements (CHEM, BIOS, PHYS)',
                'MCAT preparation guidance',
                'Medical school application support'
            ]
        },
        'pre_law': {
            'title': '⚖️ Welcome to Your Pre-Law Advisor!',
            'description': 'Specialized in law school preparation and critical thinking',
            'features': [
                'Writing and argumentation courses',
                'Critical thinking development',
                'LSAT preparation guidance'
            ]
        }
    }
    
    welcome_info = advisor_welcome_messages.get(selected_advisor, advisor_welcome_messages['general'])
    
    # Always use feature-highlight-blue for consistent styling
    css_class = "feature-highlight-blue"
    
    st.markdown(f"""
    <div class="{css_class}">
        <h3 style="color: #002469; margin-bottom: 1rem;">{welcome_info['title']}</h3>
        <p style="margin-bottom: 1rem; font-style: italic; color: #5E6062;  ">{welcome_info['description']}</p>
        <div style="margin-bottom: 0.5rem; color: #5E6062; "><strong>Specialized Features:</strong></div>
        <ul style="margin-bottom: 0; padding-left: 1.5rem; color: #5E6062; ">
            {"".join([f"<li>{feature}</li>" for feature in welcome_info['features']])}
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history if not exists
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display existing chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                # Display the formatted response
                st.markdown(message["content"])
                
                # Show intelligence level indicator if available
                if "intelligence_level" in message:
                    level = message["intelligence_level"]
                    if level == IntelligenceLevel.BASIC:
                        st.markdown(
                            '<div class="intelligence-indicator basic-level">🔵 Basic Intelligence Used</div>',
                            unsafe_allow_html=True
                        )
                    elif level == IntelligenceLevel.ENHANCED:
                        st.markdown(
                            '<div class="intelligence-indicator enhanced-level">🟡 Enhanced Intelligence Used</div>',
                            unsafe_allow_html=True
                        )
                    elif level == IntelligenceLevel.EXPERT:
                        st.markdown(
                            '<div class="intelligence-indicator expert-level">🟢 Expert Intelligence Used</div>',
                            unsafe_allow_html=True
                        )
                
                # Show performance metrics if available
                if "performance_metrics" in message:
                    metrics = message["performance_metrics"]
                    st.markdown("### 📊 **Response Metrics**")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Processing Time", f"{metrics.get('processing_time', 0):.2f}s")
                    with col2:
                        st.metric("Confidence", f"{metrics.get('confidence', 0):.0%}")
                    with col3:
                        st.metric("Courses Analyzed", f"{metrics.get('courses_analyzed', 0):,}")
                    with col4:
                        st.metric("Intelligence Level", metrics.get('intelligence_level', 'Basic'))
            else:
                st.markdown(message["content"])
    
    # Chat input for new queries
    if user_input := st.chat_input("Ask about courses, planning, career advice, or anything academic..."):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process with unified advisor or fallback to schedule builder
        if st.session_state.unified_advisor:
            with st.chat_message("assistant"):
                with st.spinner("🤔 Processing your query with Expert Intelligence Level (GPT-4)..."):
                    try:
                        # Check if this is a schedule building request
                        # These keywords indicate the user wants a course schedule
                        schedule_keywords = ['schedule', 'semester', 'courses to take', 'next courses', 'recommend courses', 'build schedule']
                        if any(keyword in user_input.lower() for keyword in schedule_keywords):
                            # Use our balanced schedule builder
                            completed_courses = st.session_state.user_profile.get('completed_courses', [])
                            
                            # Load organized data for schedule building
                            all_departments = {}
                            try:
                                import json
                                import os
                                if os.path.exists('data/organized/rice_organized_data.json'):
                                    with open('data/organized/rice_organized_data.json', 'r') as f:
                                        organized_data = json.load(f)
                                        all_departments = organized_data.get('departments', {})
                            except:
                                pass
                            
                            # Generate balanced schedule if data is available
                            if all_departments:
                                schedule_result = create_balanced_schedule(completed_courses, all_departments, 15)
                                
                                # Format and display the schedule response
                                st.markdown("## 📅 **Recommended Schedule**")
                                st.markdown(f"**Student Level:** {schedule_result['student_level'].title()}")
                                st.markdown(f"**Total Credits:** {schedule_result['total_credits']}")
                                st.markdown(f"**Departments:** {', '.join(schedule_result['departments_used'])}")
                                st.markdown(f"**Balance Score:** {schedule_result['balance_score']:.1f}/1.0")
                                
                                st.markdown("### 🎯 **Recommended Courses:**")
                                for course in schedule_result['courses']:
                                    with st.expander(f"📚 {course.get('course_code', 'N/A')} - {course.get('title', 'No title')} ({course.get('credit_hours', 'N/A')} credits)"):
                                        st.write(f"**Department:** {course.get('department', 'N/A')}")
                                        if course.get('prerequisites'):
                                            st.write(f"**Prerequisites:** {course.get('prerequisites', 'None')}")
                                        if course.get('description'):
                                            st.write(f"**Description:** {course.get('description', 'No description')}")
                                
                                # Add to chat history
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": f"I've created a balanced schedule with {len(schedule_result['courses'])} courses from {len(schedule_result['departments_used'])} departments totaling {schedule_result['total_credits']} credits."
                                })
                                return
                        
                        # Get response from unified advisor for other queries
                        response = st.session_state.unified_advisor.process_query(
                            user_input, st.session_state.user_profile
                        )
                        
                        # Format response for display
                        formatted_response = st.session_state.unified_advisor.response_formatter.format_for_display(response)
                        
                        # Display the formatted response
                        st.markdown(formatted_response)
                        
                        # Add expandable course details if recommendations are available
                        if response.recommendations:
                            st.markdown("### 🔍 **Detailed Course Information**")
                            st.markdown("*Expand any course for complete details*")
                            
                            # Show top 5 recommendations with detailed information
                            for i, rec in enumerate(response.recommendations[:5], 1):
                                course_code = rec.get('course_code', 'N/A')
                                title = rec.get('title', 'Course Title')
                                
                                with st.expander(f"📚 {course_code} - {title}"):
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.markdown(f"**Department:** {rec.get('department', 'N/A')}")
                                        st.markdown(f"**Credits:** {rec.get('credit_hours', 'N/A')}")
                                        
                                        # Show full description if available
                                        if 'description' in rec and rec['description']:
                                            description = str(rec['description'])
                                            if description not in ['N/A', 'None', '', 'nan']:
                                                st.markdown(f"**Full Description:**")
                                                st.write(description)
                                        
                                        # Show prerequisites if available
                                        if 'prerequisites' in rec and rec['prerequisites']:
                                            prereqs = str(rec['prerequisites'])
                                            if prereqs not in ['N/A', 'None', '', 'nan']:
                                                st.markdown(f"**Prerequisites:** {prereqs}")
                                    
                                    with col2:
                                        # Show scores and metrics
                                        if 'similarity_score' in rec:
                                            st.metric("Relevance Score", f"{rec['similarity_score']:.2f}")
                                        
                                        if 'success_probability' in rec:
                                            st.metric("Success Rate", f"{rec['success_probability']:.0%}")
                                        
                                        # Course difficulty indicator based on course number
                                        import re
                                        course_num_match = re.search(r'(\d+)', course_code)
                                        if course_num_match:
                                            course_num = int(course_num_match.group(1))
                                            if course_num >= 500:
                                                st.info("🔴 Graduate Level")
                                            elif course_num >= 300:
                                                st.warning("🟡 Upper Level")
                                            else:
                                                st.success("🟢 Lower Level")
                                    
                                    # Show reasoning for the recommendation
                                    if 'reasoning' in rec:
                                        reasoning = str(rec['reasoning'])
                                        if reasoning not in ['N/A', 'None', '', 'nan']:
                                            st.markdown("**💡 Why Recommended:**")
                                            st.info(reasoning)
                        
                        # Show intelligence level indicator
                        level = response.intelligence_level
                        if level == IntelligenceLevel.BASIC:
                            st.markdown(
                                '<div class="intelligence-indicator basic-level">🔵 Basic Intelligence Used - Fast & Reliable</div>',
                                unsafe_allow_html=True
                            )
                        elif level == IntelligenceLevel.ENHANCED:
                            st.markdown(
                                '<div class="intelligence-indicator enhanced-level">🟡 Enhanced Intelligence Used - ML-Powered</div>',
                                unsafe_allow_html=True
                            )
                        elif level == IntelligenceLevel.EXPERT:
                            st.markdown(
                                '<div class="intelligence-indicator expert-level">🟢 Expert Intelligence Used - GPT-Validated</div>',
                                unsafe_allow_html=True
                            )
                        
                        # Show performance metrics
                        st.markdown("### 📊 **Response Metrics**")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Processing Time", f"{response.processing_time:.2f}s")
                        with col2:
                            st.metric("Confidence", f"{response.confidence:.0%}")
                        with col3:
                            st.metric("Courses Analyzed", f"{response.total_courses_analyzed:,}")
                        with col4:
                            st.metric("Intelligence Level", level.value.title())
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": formatted_response,
                            "intelligence_level": level,
                            "performance_metrics": {
                                "processing_time": response.processing_time,
                                "confidence": response.confidence,
                                "courses_analyzed": response.total_courses_analyzed,
                                "intelligence_level": level.value.title()
                            }
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error processing query: {e}")
                        st.info("💡 Try rephrasing your question or check the system status.")
        else:
            # Fallback when unified advisor is not available
            with st.chat_message("assistant"):
                st.error("❌ Unified advisor system is not available. Please check the system status.")

# ================================================================
# QUICK ACTIONS AND UTILITY FUNCTIONS
# ================================================================

def render_quick_actions():
    """
    Render quick action buttons for common requests.
    
    This function provides one-click access to common academic advisor
    tasks like semester planning, course finding, and career preparation.
    """
    st.markdown("## 🎯 **Quick Actions**")
    st.markdown("*Click any button to instantly get recommendations*")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📅 **Plan Next Semester**", help="Get course recommendations for next semester"):
            st.session_state.auto_query = "Plan my next semester based on my academic profile and goals"
    
    with col2:
        if st.button("🔍 **Find Courses**", help="Search for courses matching your interests"):
            st.session_state.auto_query = "Find courses that match my interests and academic background"
    
    with col3:
        if st.button("💼 **Career Prep**", help="Get career-focused course recommendations"):
            st.session_state.auto_query = "What courses should I take to prepare for my career goals?"
    
    with col4:
        if st.button("🧠 **Expert Analysis**", help="Get GPT-powered expert analysis"):
            st.session_state.auto_query = "Provide expert analysis of my academic plan and recommendations"
    
    # Handle auto queries from quick actions
    if hasattr(st.session_state, 'auto_query') and st.session_state.auto_query:
        # Process the auto query
        if st.session_state.unified_advisor:
            with st.spinner("🤔 Processing your request..."):
                try:
                    response = st.session_state.unified_advisor.process_query(
                        st.session_state.auto_query, st.session_state.user_profile
                    )
                    
                    formatted_response = st.session_state.unified_advisor.response_formatter.format_for_display(response)
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "user", 
                        "content": st.session_state.auto_query
                    })
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": formatted_response,
                        "intelligence_level": response.intelligence_level,
                        "performance_metrics": {
                            "processing_time": response.processing_time,
                            "confidence": response.confidence,
                            "courses_analyzed": response.total_courses_analyzed,
                            "intelligence_level": response.intelligence_level.value.title()
                        }
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error processing quick action: {e}")
        
        # Clear auto query after processing
        del st.session_state.auto_query
        st.rerun()

def render_system_status():
    """
    Render system status and performance metrics.
    
    This function displays comprehensive system information including:
    - Performance statistics
    - Intelligence level usage
    - Cache status
    - System controls
    """
    st.markdown("## 📊 **System Status**")
    
    if st.session_state.unified_advisor:
        # Get performance statistics from the unified advisor
        stats = st.session_state.unified_advisor.get_performance_stats()
        
        # Main performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Total Queries</div>
            </div>
            """.format(stats['total_queries']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            """.format(stats.get('success_rate', 0)), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:.2f}s</div>
                <div class="metric-label">Avg Response Time</div>
            </div>
            """.format(stats['avg_response_time']), unsafe_allow_html=True)
        
        with col4:
            cache_stats = stats.get('cache_stats', {})
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Cache Size</div>
            </div>
            """.format(cache_stats.get('cache_size', 0)), unsafe_allow_html=True)
        
        # Intelligence level usage visualization
        st.markdown("### 🧠 **Intelligence Level Usage**")
        
        usage_stats = stats['intelligence_level_usage']
        total_usage = sum(usage_stats.values())
        
        if total_usage > 0:
            # Create pie chart showing intelligence level distribution
            fig = px.pie(
                values=list(usage_stats.values()),
                names=['Basic', 'Enhanced', 'Expert'],
                title="Intelligence Level Distribution",
                color_discrete_map={
                    'Basic': '#2196f3',
                    'Enhanced': '#ff9800',
                    'Expert': '#4caf50'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No queries processed yet. Start asking questions to see usage statistics!")
        
        # System controls
        st.markdown("### ⚙️ **System Controls**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 Clear Cache"):
                st.session_state.unified_advisor.clear_cache()
                st.success("✅ Cache cleared successfully!")
        
        with col2:
            if st.button("📊 Reset Statistics"):
                st.session_state.unified_advisor.reset_stats()
                st.success("✅ Statistics reset successfully!")
        
        with col3:
            if st.button("🔄 Refresh Status"):
                st.rerun()
    
    else:
        st.error("❌ System status unavailable - Unified advisor not loaded")

# ================================================================
# SIDEBAR INFORMATION AND CONTROLS
# ================================================================

with st.sidebar:
    st.markdown("""
    <div class="rice-branding" style="padding: 1.5rem; margin-bottom: 2rem;">
        <div class="owl-icon" style="font-size: 2.5rem; margin-bottom: 0.5rem;">🦉</div>
        <h2 style="color: white; margin-bottom: 0.5rem; font-family: 'Playfair Display', serif;">Rice Advisor</h2>
        <p style="color: #e8f4f8; margin-bottom: 0; font-family: 'Lato', sans-serif;">Unified Intelligence System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Advisor options with emojis and descriptions
    advisor_options = {
        'general': '🎓 General Academic Advisor',
        'computer_science': '💻 Computer Science Advisor',
        'mathematics': '🔢 Mathematics Advisor',
        'chemistry': '🧪 Chemistry Advisor',
        'physics': '⚛️ Physics Advisor',
        'business': '📊 Business Advisor',
        'music': '🎵 Music Advisor (Shepherd School)',
        'engineering': '🔧 Engineering Advisor',
        'biosciences': '🧬 Biosciences Advisor',
        'humanities': '📚 Humanities Advisor',
        'social_sciences': '🌍 Social Sciences Advisor',
        'architecture': '🏗️ Architecture Advisor',
        'pre_med': '⚕️ Pre-Medical Advisor',
        'pre_law': '⚖️ Pre-Law Advisor'
    }
    
    # Create advisor descriptions
    advisor_descriptions = {
        'general': 'Helps with courses from any department',
        'computer_science': 'COMP, MATH, STAT, ELEC courses',
        'mathematics': 'MATH, STAT, CAAM courses',
        'chemistry': 'CHEM courses and pre-med requirements',
        'physics': 'PHYS courses and applied physics',
        'business': 'MGMT, ECON, business courses',
        'music': 'MUSI courses and performance',
        'engineering': 'All engineering departments',
        'biosciences': 'BIOC, BIOS, life sciences',
        'humanities': 'ENGL, HIST, PHIL, languages',
        'social_sciences': 'POLI, PSYC, ANTH, SOCI',
        'architecture': 'ARCH courses and design',
        'pre_med': 'Medical school requirements',
        'pre_law': 'Law school preparation'
    }
    
    # Initialize selected advisor in session state
    if 'selected_advisor' not in st.session_state:
        st.session_state.selected_advisor = 'general'
    
    # Advisor Selection - Use Streamlit container with custom styling
    with st.container():
        st.markdown("### 🎓 Choose Your Advisor")
        
        selected_advisor = st.selectbox(
            "Select Your Advisor:",
            options=list(advisor_options.keys()),
            format_func=lambda x: advisor_options[x],
            index=list(advisor_options.keys()).index(st.session_state.selected_advisor),
            key="advisor_selector_unified"
        )
        
        # Update session state
        st.session_state.selected_advisor = selected_advisor
        
        st.markdown(f"""
        <div class="rice-info" style="margin: 0.5rem 0;">
            <strong>Focus:</strong> {advisor_descriptions[selected_advisor]}
        </div>
        """, unsafe_allow_html=True)
    
    # # Show selected advisor status
    # st.markdown(f"""
    # <div class="rice-success" style="margin-top: 1rem;">
    #     <strong>Active Advisor:</strong> {advisor_options[selected_advisor]}
    # </div>
    # """, unsafe_allow_html=True)
    
    # Special info box for general advisor
    if selected_advisor == 'general':
        st.markdown("""
        <div class="stats-card" style="margin-top: 1rem;">
            <h4 style="color: #002469; margin-bottom: 0.5rem;">💡 How General Advisor Works</h4>
            <p style="margin-bottom: 0.5rem; font-size: 0.9rem; color: #5E6062;">• Answers questions from any department</p>
            <p style="margin-bottom: 0.5rem; font-size: 0.9rem; color: #5E6062;">• Suggests specialized advisors for detailed guidance</p>
            <p style="margin-bottom: 0; font-size: 0.9rem; color: #5E6062;">• Perfect starting point when unsure which advisor to choose</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick advisor switching buttons (only show if not general advisor)
    if selected_advisor != 'general':
        st.markdown("""
        <div class="stats-card" style="margin-top: 1rem;">
            <h4 style="color: #002469; margin-bottom: 0.5rem;">💡 Quick Switch</h4>
            <p style="margin-bottom: 0.5rem; font-size: 0.9rem; color: #5E6062;">Need help from another department?</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show quick switch buttons for related advisors
        related_advisors = {
            'computer_science': ['mathematics', 'engineering', 'general'],
            'mathematics': ['computer_science', 'physics', 'general'],
            'chemistry': ['pre_med', 'biosciences', 'general'],
            'physics': ['mathematics', 'engineering', 'general'],
            'business': ['social_sciences', 'general'],
            'music': ['humanities', 'general'],
            'engineering': ['computer_science', 'mathematics', 'general'],
            'biosciences': ['chemistry', 'pre_med', 'general'],
            'humanities': ['social_sciences', 'general'],
            'social_sciences': ['humanities', 'business', 'general'],
            'architecture': ['engineering', 'general'],
            'pre_med': ['chemistry', 'biosciences', 'general'],
            'pre_law': ['humanities', 'social_sciences', 'general']
        }
        
        quick_switches = related_advisors.get(selected_advisor, ['general'])
        cols = st.columns(len(quick_switches))
        
        for i, advisor_key in enumerate(quick_switches):
            with cols[i]:
                if st.button(f"Switch to {advisor_options[advisor_key]}", key=f"switch_unified_{advisor_key}"):
                    st.session_state.selected_advisor = advisor_key
                    st.rerun()

# ================================================================
# MAIN APPLICATION FUNCTION
# ================================================================

def main():
    """
    Main application function that orchestrates the entire Streamlit app.
    
    This function:
    1. Loads the unified advisor system
    2. Sets up the user profile
    3. Creates the main interface with tabs
    4. Handles error cases and troubleshooting
    """
    
    # Load unified advisor system (cached for performance)
    if 'unified_advisor' not in st.session_state:
        with st.spinner("🚀 Loading Rice Academic Advisor..."):
            st.session_state.unified_advisor = load_unified_advisor()
    
    # Setup user profile in sidebar
    st.session_state.user_profile = setup_user_profile()
    
    # Main content area
    if st.session_state.unified_advisor:
        # Create tabs for different sections of the app
        tab1, tab2, tab3, tab4 = st.tabs([
            "💬 **Chat with Advisor**",
            "🧠 **Intelligence Levels**", 
            "🎯 **Quick Actions**",
            "📊 **System Status**"
        ])
        
        with tab1:
            render_unified_chat()
        
        with tab2:
            display_intelligence_level_info()
        
        with tab3:
            render_quick_actions()
        
        with tab4:
            render_system_status()
    
    else:
        # Handle case when unified advisor fails to load
        st.error("❌ Failed to load the unified advisor system")
        st.info("🔧 Please check the system requirements and try again")
        
        # Show troubleshooting information
        with st.expander("🛠️ Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            1. **Missing dependencies**: Run `pip install -r requirements.txt`
            2. **Course data not found**: Ensure `rice_all_courses.json` exists
            3. **Performance issues**: Clear cache and restart the app
            
            **System Requirements:**
            - Python 3.8+
            - All dependencies from requirements.txt
            - Rice course data files
            
            **Need Help?**
            - Check the README.md for setup instructions
            - Review the PERFORMANCE_OPTIMIZATION_GUIDE.md
            - Contact support if issues persist
            """)

# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main() 