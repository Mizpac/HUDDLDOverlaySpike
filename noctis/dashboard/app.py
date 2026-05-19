import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.database import init_db

st.set_page_config(
    page_title="Noctis",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS — reinforces the 60/30/10 palette and tightens default Streamlit spacing
st.markdown("""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #2E4A6B;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #F0F4F8;
        font-size: 0.95rem;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #2E4A6B;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 3px solid #4DA6C8;
    }
    [data-testid="stMetricValue"] { color: #FFFFFF; font-size: 1.8rem; }
    [data-testid="stMetricLabel"] { color: #F0F4F8; font-size: 0.8rem; }

    /* Info / warning / success boxes */
    .stAlert { border-radius: 6px; }

    /* Dividers */
    hr { border-color: #2E4A6B; }

    /* Section headers */
    .noctis-section-header {
        color: #4DA6C8;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* Flag badge */
    .flag-badge {
        display: inline-block;
        background-color: #E8A838;
        color: #1E2D3E;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    /* Status dot */
    .status-dot-idle  { color: #F0F4F8; }
    .status-dot-running { color: #4DA6C8; }
    .status-dot-ok { color: #4CAF82; }
    .status-dot-warn { color: #E8A838; }
</style>
""", unsafe_allow_html=True)

init_db()

# ── Navigation ────────────────────────────────────────────────

pages = {
    "🏠  Dashboard":      "dashboard/pages/home.py",
    "🔍  Pipeline":       "dashboard/pages/pipeline.py",
    "⚙️   Collection":    "dashboard/pages/collection.py",
    "🛒  My Listings":    "dashboard/pages/my_listings.py",
    "📈  Sales Tracker":  "dashboard/pages/sales.py",
    "📋  Reports":        "dashboard/pages/reports.py",
    "🧪  Dream Lab":      "dashboard/pages/dream_lab.py",
}

with st.sidebar:
    st.markdown("## 🦉 Noctis")
    st.markdown("*Night Owl Printing*")
    st.divider()
    selection = st.radio("", list(pages.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("Night Owl Printing · Personal use only")

# Load the selected page
page_file = os.path.join(os.path.dirname(__file__), "..", pages[selection])
with open(page_file) as f:
    exec(compile(f.read(), page_file, "exec"), {"__name__": "__main__"})
