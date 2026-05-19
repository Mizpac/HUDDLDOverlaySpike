import streamlit as st
from core.database import get_all_niches, get_daily_api_calls, get_recent_activity
from config import QPD_LIMIT

st.markdown("# ⚙️ Collection")
st.caption("Manage automated collection runs and monitor API usage")
st.divider()

# ── API usage gauge ───────────────────────────────────────────

st.markdown('<p class="noctis-section-header">API Usage Today</p>', unsafe_allow_html=True)
calls_used = get_daily_api_calls()
calls_remaining = QPD_LIMIT - calls_used
pct = calls_used / QPD_LIMIT

c1, c2, c3 = st.columns(3)
c1.metric("Calls Used", f"{calls_used:,}")
c2.metric("Remaining", f"{calls_remaining:,}")
c3.metric("Daily Limit", f"{QPD_LIMIT:,}")

color = "#4CAF82" if pct < 0.7 else "#E8A838" if pct < 0.9 else "#E85858"
st.markdown(f"""
<div style='background:#2E4A6B; border-radius:6px; overflow:hidden; height:10px; margin:8px 0 16px;'>
    <div style='background:{color}; width:{pct*100:.1f}%; height:100%;'></div>
</div>
<p style='font-size:0.78rem; color:#aaa;'>
    5 QPS · 5,000 QPD · Resets at midnight
</p>
""", unsafe_allow_html=True)

st.divider()

# ── Manual collection trigger ─────────────────────────────────

st.markdown('<p class="noctis-section-header">Manual Collection Run</p>', unsafe_allow_html=True)

niches = get_all_niches()
collecting_niches = [n for n in niches if n["status"] in ("collecting", "calibrating")]

if not collecting_niches:
    st.info("No items are currently in the Collecting or Calibrating stage. Add items via the Pipeline page.")
else:
    selected = st.selectbox(
        "Select item to collect",
        collecting_niches,
        format_func=lambda n: f"{n['name']}  ({n['status']})",
    )

    col1, col2 = st.columns(2)
    with col1:
        sample_type = st.radio("Sample type", ["A — first collection", "B — calibration check"])
    with col2:
        sort_on = st.selectbox("Sort order", ["score", "created", "price_asc", "price_desc"])
        limit = st.slider("Listings to collect", min_value=10, max_value=100, value=25, step=5)

    if st.button("▶ Run Collection Now", use_container_width=True, type="primary"):
        st.warning("Collection module not yet connected — build Phase 2 first. "
                   "This button will trigger `modules/collector.py` when ready.")

st.divider()

# ── Schedule ──────────────────────────────────────────────────

st.markdown('<p class="noctis-section-header">Automated Schedule</p>', unsafe_allow_html=True)
st.markdown("""
<div style='background:#2E4A6B; border-radius:8px; padding:16px;'>
    <p style='margin:0; font-size:0.9rem;'>
        Scheduled collection runs automatically for all active pipeline items.<br><br>
        <strong>Sample A</strong> — runs on demand when a new item is added<br>
        <strong>Sample B</strong> — runs 48h after Sample A, overnight<br>
        <strong>Sales sync</strong> — runs daily at 3:00 AM
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Recent collection activity ────────────────────────────────

st.markdown('<p class="noctis-section-header">Collection History</p>', unsafe_allow_html=True)

history = get_recent_activity(limit=20)
collection_history = [a for a in history if "collection" in a["action"].lower() or "sample" in a["action"].lower()]

if not collection_history:
    st.caption("No collection runs yet.")
else:
    for entry in collection_history:
        status_color = {"completed": "#4CAF82", "running": "#4DA6C8", "failed": "#E85858"}.get(entry["status"], "#aaa")
        st.markdown(f"""
        <div style='display:flex; padding:7px 0; border-bottom:1px solid #2E4A6B; font-size:0.85rem;'>
            <span style='color:{status_color}; min-width:80px;'>● {entry['status']}</span>
            <span style='flex:1; color:#F0F4F8;'>{entry['action']} — {entry['detail']}</span>
            <span style='color:#aaa;'>{entry['started_at'][:16]} · {entry['api_calls_used']} calls</span>
        </div>
        """, unsafe_allow_html=True)
