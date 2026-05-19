import streamlit as st
from core.database import get_connection, get_all_niches

st.markdown("# 🛒 My Listings")
st.caption("Your Etsy listings linked to pipeline items · synced via OAuth")
st.divider()

def get_my_listings():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT ml.*, n.name as niche_name
            FROM my_listings ml
            LEFT JOIN niches n ON ml.niche_id = n.id
            ORDER BY ml.last_synced DESC
        """).fetchall()
        return [dict(r) for r in rows]

listings = get_my_listings()
niches = get_all_niches()

# ── Sync button ───────────────────────────────────────────────

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<p class="noctis-section-header">Your Shop Listings</p>', unsafe_allow_html=True)
with col2:
    if st.button("⟳ Sync from Etsy", use_container_width=True):
        st.warning("Sales sync module not yet connected — build Phase 4 first.")

if not listings:
    st.info("No listings synced yet. Click 'Sync from Etsy' after completing OAuth setup.")
else:
    # ── Summary metrics ───────────────────────────────────────
    total_views = sum(l.get("views", 0) or 0 for l in listings)
    total_favorites = sum(l.get("num_favorers", 0) or 0 for l in listings)
    linked = sum(1 for l in listings if l.get("niche_id"))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Listings", len(listings))
    m2.metric("Total Views", f"{total_views:,}")
    m3.metric("Total Favorites", f"{total_favorites:,}")
    m4.metric("Linked to Pipeline", linked)

    st.divider()

    # ── Listings table ────────────────────────────────────────
    for listing in listings:
        with st.expander(f"{listing['title'] or 'Untitled'} — ${listing.get('price', 0):.2f}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**Views:** {listing.get('views', 0):,}  ·  **Favorites:** {listing.get('num_favorers', 0):,}")
                st.markdown(f"**State:** {listing.get('state', '—')}")
                if listing.get("niche_name"):
                    st.markdown(f"**Linked to:** {listing['niche_name']}")
                else:
                    st.markdown("**Linked to:** *(not linked)*")
            with c2:
                niche_options = ["(none)"] + [n["name"] for n in niches]
                current_idx = 0
                if listing.get("niche_name"):
                    names = [n["name"] for n in niches]
                    if listing["niche_name"] in names:
                        current_idx = names.index(listing["niche_name"]) + 1

                selected_niche = st.selectbox(
                    "Link to pipeline item",
                    niche_options,
                    index=current_idx,
                    key=f"link_{listing['id']}",
                )
                if st.button("Save link", key=f"save_{listing['id']}"):
                    if selected_niche == "(none)":
                        niche_id = None
                    else:
                        niche_id = next((n["id"] for n in niches if n["name"] == selected_niche), None)
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE my_listings SET niche_id=? WHERE id=?",
                            (niche_id, listing["id"]),
                        )
                    st.rerun()
