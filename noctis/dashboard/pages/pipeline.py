import streamlit as st
import json
from core.database import (
    get_all_niches, create_niche, update_niche_status,
    get_open_flags, resolve_flag,
)

st.markdown("# 🔍 Pipeline")
st.caption("All tracked items — from first collection through to listed products")
st.divider()

# ── Add new item ──────────────────────────────────────────────

with st.expander("＋ Add new item to pipeline"):
    with st.form("add_niche"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Item name", placeholder="e.g. Woodland nursery stationery")
        with col2:
            keywords_raw = st.text_input(
                "Search keywords (comma-separated)",
                placeholder="woodland nursery, forest baby shower, nature nursery decor",
            )
        notes = st.text_area("Notes (optional)", height=80)
        submitted = st.form_submit_button("Add to Pipeline", use_container_width=True)

        if submitted and name and keywords_raw:
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
            create_niche(name, keywords, notes)
            st.success(f"'{name}' added to pipeline at Collecting stage.")
            st.rerun()

# ── Filter ────────────────────────────────────────────────────

STATUS_LABELS = {
    "all":         "All",
    "collecting":  "🔍 Collecting",
    "calibrating": "⏳ Calibrating",
    "validated":   "✅ Validated",
    "blocked":     "⚠️ Blocked",
    "in_progress": "✏️ In Progress",
    "listed":      "🛒 Listed",
    "archived":    "📦 Archived",
}

status_filter = st.selectbox(
    "Filter by stage",
    list(STATUS_LABELS.keys()),
    format_func=lambda k: STATUS_LABELS[k],
    index=0,
)

# ── Items table ───────────────────────────────────────────────

niches = get_all_niches()
if status_filter != "all":
    niches = [n for n in niches if n["status"] == status_filter]

if not niches:
    st.info("No items match this filter. Add one above to get started.")
else:
    for niche in niches:
        status_color = {
            "collecting":  "#4DA6C8",
            "calibrating": "#8BA7C4",
            "validated":   "#4CAF82",
            "blocked":     "#E8A838",
            "in_progress": "#F0F4F8",
            "listed":      "#4CAF82",
            "archived":    "#888",
        }.get(niche["status"], "#aaa")

        score_display = f"{niche['score']:.0f}" if niche["score"] is not None else "—"
        conf_display = f"{niche['confidence']:.0%}" if niche["confidence"] is not None else "—"

        with st.expander(f"{niche['name']}   ·   score: {score_display}   ·   confidence: {conf_display}"):
            c1, c2, c3 = st.columns([2, 1, 1])

            with c1:
                st.markdown(
                    f"**Status:** <span style='color:{status_color};'>"
                    f"{STATUS_LABELS.get(niche['status'], niche['status'])}</span>",
                    unsafe_allow_html=True,
                )
                kw = ", ".join(niche.get("keywords", []))
                st.markdown(f"**Keywords:** {kw}")
                if niche.get("notes"):
                    st.markdown(f"**Notes:** {niche['notes']}")
                st.caption(f"Added: {niche['created_at'][:10]}")

            with c2:
                st.markdown("**Move to stage:**")
                new_status = st.selectbox(
                    "Status",
                    list(STATUS_LABELS.keys())[1:],
                    format_func=lambda k: STATUS_LABELS[k],
                    index=list(STATUS_LABELS.keys())[1:].index(niche["status"])
                    if niche["status"] in list(STATUS_LABELS.keys())[1:]
                    else 0,
                    key=f"status_{niche['id']}",
                    label_visibility="collapsed",
                )
                if st.button("Update", key=f"update_{niche['id']}"):
                    update_niche_status(niche["id"], new_status)
                    st.rerun()

            with c3:
                st.markdown("**Actions:**")
                if st.button("▶ Run Collection", key=f"collect_{niche['id']}"):
                    st.info("Collection will be queued — go to Collection page to manage runs.")
                if st.button("📋 View Report", key=f"report_{niche['id']}"):
                    st.session_state["report_niche_id"] = niche["id"]
                    st.info("Open the Reports page to view the full analysis.")
