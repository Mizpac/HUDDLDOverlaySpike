import streamlit as st
from datetime import datetime
from core.database import (
    get_pipeline_counts, get_open_flags, get_recent_activity,
    get_daily_api_calls,
)
from config import QPD_LIMIT

# ── Header / status bar ───────────────────────────────────────

now = datetime.now().strftime("%b %d, %Y  %H:%M")
api_calls = get_daily_api_calls()
api_pct = round((api_calls / QPD_LIMIT) * 100, 1)

col_title, col_status = st.columns([3, 2])
with col_title:
    st.markdown("# Noctis")
    st.caption("Your market intelligence platform · Night Owl Printing")
with col_status:
    st.markdown(f"""
    <div style='text-align:right; padding-top: 12px; color: #F0F4F8; font-size: 0.85rem;'>
        🟢 &nbsp;API Active &nbsp;|&nbsp; {now}<br>
        API usage today: <strong>{api_calls:,} / {QPD_LIMIT:,}</strong> ({api_pct}%)
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Three-panel row ───────────────────────────────────────────

left, mid, right = st.columns([1, 2, 1])

with left:
    st.markdown('<p class="noctis-section-header">Live Activity</p>', unsafe_allow_html=True)
    activity = get_recent_activity(limit=1)
    if activity and activity[0]["status"] == "running":
        current = activity[0]
        st.markdown(f"""
        <div style='background:#2E4A6B; border-radius:8px; padding:14px;
                    border-left: 3px solid #4DA6C8;'>
            <span style='color:#4DA6C8; font-weight:700;'>⟳ Running</span><br>
            <span style='font-size:0.85rem; color:#F0F4F8;'>{current['action']}</span><br>
            <span style='font-size:0.75rem; color:#aaa;'>{current['detail']}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:#2E4A6B; border-radius:8px; padding:14px;
                    border-left: 3px solid #4CAF82;'>
            <span style='color:#4CAF82; font-weight:700;'>● Idle</span><br>
            <span style='font-size:0.85rem; color:#F0F4F8;'>No active collection</span><br>
            <span style='font-size:0.75rem; color:#aaa;'>Next run: scheduled</span>
        </div>
        """, unsafe_allow_html=True)

with mid:
    st.markdown('<p class="noctis-section-header">Pipeline</p>', unsafe_allow_html=True)
    counts = get_pipeline_counts()
    total = sum(counts.values())

    stages = [
        ("🔍 Collecting",   "collecting",   "#4DA6C8"),
        ("⏳ Calibrating",  "calibrating",  "#8BA7C4"),
        ("✅ Validated",    "validated",    "#4CAF82"),
        ("⚠️ Blocked",      "blocked",      "#E8A838"),
        ("✏️ In Progress",  "in_progress",  "#F0F4F8"),
        ("🛒 Listed",       "listed",       "#4CAF82"),
        ("📈 With Sales",   "archived",     "#4DA6C8"),
    ]

    for label, key, color in stages:
        count = counts.get(key, 0)
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"<span style='font-size:0.9rem;'>{label}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<span style='color:{color}; font-weight:700; float:right;'>{count}</span>",
                unsafe_allow_html=True,
            )

    st.markdown(f"""
    <div style='margin-top:10px; font-size:0.8rem; color:#aaa;'>
        Total tracked: <strong style='color:#fff;'>{total}</strong>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown('<p class="noctis-section-header">Flagged for Review</p>', unsafe_allow_html=True)
    flags = get_open_flags()
    if not flags:
        st.markdown("""
        <div style='background:#2E4A6B; border-radius:8px; padding:14px;
                    border-left: 3px solid #4CAF82;'>
            <span style='color:#4CAF82;'>✓ Nothing flagged</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        for flag in flags[:5]:
            icon = "⚠️" if flag["flag_type"] in ("calibration_fail", "stale_data") else "💰"
            st.markdown(f"""
            <div style='background:#2E4A6B; border-radius:6px; padding:10px 12px;
                        border-left: 3px solid #E8A838; margin-bottom:6px;'>
                {icon} <span style='font-size:0.82rem;'>{flag['message']}</span>
            </div>
            """, unsafe_allow_html=True)
        if len(flags) > 5:
            st.caption(f"+{len(flags) - 5} more — check Pipeline")

st.divider()

# ── Next Best Move ────────────────────────────────────────────

st.markdown('<p class="noctis-section-header">Next Best Move</p>', unsafe_allow_html=True)

counts = get_pipeline_counts()
flags = get_open_flags()
moves = []

if counts.get("validated", 0) > 0:
    moves.append(f"→ **{counts['validated']} validated item(s)** are ready — start creating content now")
if counts.get("collecting", 0) > 0:
    moves.append(f"→ **{counts['collecting']} item(s)** are in Sample A collection — Sample B window opens in 48h")
if counts.get("blocked", 0) > 0:
    moves.append(f"→ **{counts['blocked']} item(s)** failed calibration — review and adjust keywords or resample")
if flags:
    moves.append(f"→ **{len(flags)} open flag(s)** need your attention before next collection run")

if not moves:
    moves.append("→ Add your first item to the Pipeline to get started")

nbm_col1, nbm_col2 = st.columns([3, 1])
with nbm_col1:
    for move in moves:
        st.markdown(f"""
        <div style='background:#2E4A6B; border-radius:6px; padding:10px 16px;
                    border-left: 3px solid #4DA6C8; margin-bottom:6px;
                    font-size:0.9rem;'>
            {move}
        </div>
        """, unsafe_allow_html=True)
with nbm_col2:
    if st.button("Open Pipeline →", use_container_width=True):
        st.session_state["nav"] = "🔍  Pipeline"
        st.rerun()

st.divider()

# ── Recent Activity ───────────────────────────────────────────

st.markdown('<p class="noctis-section-header">Recent Activity</p>', unsafe_allow_html=True)

recent = get_recent_activity(limit=8)
if not recent:
    st.caption("No activity yet. Run a collection to get started.")
else:
    for entry in recent:
        status_color = {
            "completed": "#4CAF82",
            "running":   "#4DA6C8",
            "failed":    "#E85858",
        }.get(entry["status"], "#aaa")

        ts = entry["started_at"][:16] if entry["started_at"] else "—"
        calls = entry.get("api_calls_used", 0)

        st.markdown(f"""
        <div style='display:flex; align-items:center; padding:7px 0;
                    border-bottom: 1px solid #2E4A6B; font-size:0.85rem;'>
            <span style='color:{status_color}; min-width:80px;'>
                ● {entry['status']}
            </span>
            <span style='color:#F0F4F8; flex:1;'>{entry['action']}</span>
            <span style='color:#aaa; min-width:120px; text-align:right;'>
                {ts} &nbsp;·&nbsp; {calls} calls
            </span>
        </div>
        """, unsafe_allow_html=True)
