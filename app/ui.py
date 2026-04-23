"""
Shared UI components and styling for all pages.
"""
# Complexity overview:
# - Time: O(1) helper calls, excluding browser rendering performed by Streamlit.
# - Space: O(1) helper-local state.
import streamlit as st


def apply_custom_css():
    """Apply custom CSS matching the earthy theme."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600&family=Outfit:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..500,0..1,-25..200&display=swap');

        .mat {
            font-family: 'Material Symbols Rounded';
            font-weight: normal;
            font-style: normal;
            font-size: 1.1em;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
            vertical-align: -0.2em;
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif !important;
            color: #2C302B !important;
            letter-spacing: -0.01em;
        }

        /* App background */
        .stApp {
            background-color: #F9F8F6;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E8E6E1;
        }

        /* Primary button */
        .stButton > button {
            background-color: #4A6741;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.25rem;
            font-weight: 500;
            transition: background-color 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #3D5535;
            color: white;
            border: none;
        }
        .stButton > button:focus:not(:active) {
            background-color: #3D5535;
            color: white;
            border: none;
            box-shadow: 0 0 0 3px rgba(74, 103, 65, 0.2);
        }

        /* Download button */
        .stDownloadButton > button {
            background-color: #C07C5F;
            color: white;
            border: none;
            border-radius: 8px;
        }
        .stDownloadButton > button:hover {
            background-color: #A96A4F;
            color: white;
        }

        /* Inputs */
        .stTextInput input, .stNumberInput input, .stDateInput input {
            border-radius: 8px !important;
            border: 1px solid #E8E6E1 !important;
            background-color: white !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #4A6741 !important;
            box-shadow: 0 0 0 3px rgba(74, 103, 65, 0.1) !important;
        }

        /* Select */
        [data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid #E8E6E1 !important;
            background-color: white !important;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E8E6E1;
            padding: 1.25rem;
            border-radius: 8px;
        }
        [data-testid="stMetricValue"] {
            font-family: 'Outfit', sans-serif !important;
            color: #2C302B !important;
            font-weight: 600;
        }
        [data-testid="stMetricLabel"] {
            color: #797D78 !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 8px;
            color: #797D78;
            padding: 8px 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4A6741 !important;
            color: white !important;
        }

        /* DataFrame */
        .stDataFrame {
            border: 1px solid #E8E6E1;
            border-radius: 8px;
            overflow: hidden;
        }

        /* Info/success/error boxes */
        .stAlert {
            border-radius: 8px !important;
        }

        /* Hide streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Keep the top header visible so collapsed sidebar reopen control (>>) remains usable. */
        [data-testid="collapsedControl"] {
            visibility: visible !important;
            display: flex !important;
        }

        /* Card container */
        .finance-card {
            background: #FFFFFF;
            border: 1px solid #E8E6E1;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        /* Logo */
        .app-logo {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #4A6741;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 1.5rem;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: #F2F0EB !important;
            border-radius: 8px !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            background-color: white;
            border: 2px dashed #E8E6E1;
            border-radius: 8px;
            padding: 1rem;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #4A6741;
            background-color: rgba(74, 103, 65, 0.03);
        }
        </style>
    """, unsafe_allow_html=True)


def icon(name: str, size: str = "1.1em", color: str = "currentColor") -> str:
    """Return HTML for a Material Symbols Rounded icon.

    Example: icon("dashboard") -> '<span class="mat">dashboard</span>'
    """
    return (
        f'<span class="mat" style="font-size: {size}; color: {color};">'
        f'{name}</span>'
    )


def render_header(page_title: str, subtitle: str = ""):
    """Render a consistent page header."""
    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h1 style="margin: 0; font-size: 2.25rem; font-weight: 500;">{page_title}</h1>
            {f'<p style="color: #797D78; margin-top: 0.25rem;">{subtitle}</p>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)


def render_sidebar_user(user_name: str, user_email: str):
    """Render user info at the bottom of the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; padding: 8px 0;">
            <div style="
                width: 36px; height: 36px; border-radius: 50%;
                background: #4A6741; color: white;
                display: flex; align-items: center; justify-content: center;
                font-weight: 600;">
                {user_name[0].upper() if user_name else 'U'}
            </div>
            <div style="flex: 1; min-width: 0;">
                <div style="font-weight: 500; font-size: 0.9rem; color: #2C302B;
                    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {user_name}
                </div>
                <div style="font-size: 0.75rem; color: #797D78;
                    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {user_email}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


CHART_COLORS = ["#4A6741", "#C07C5F", "#D4A373", "#8BA888", "#E8D5C4", "#9CAE9C", "#B08968", "#DEB887"]
