import streamlit as st
import json
from core.database import (
    get_all_niches, get_niche, get_samples_for_niche,
    get_listings_for_sample, get_connection,
)

st.markdown("# 📋 Reports")
st.caption("Deep dive on any pipeline item — samples, signals, calibration results")
st.divider()

niches = get_all_niches()
if not niches:
    st.info("No pipeline items yet. Add items via the Pipeline page.")
    st.stop()

selected = st.selectbox(
    "Select a pipeline item",
    niches,
    format_func=lambda n: f"{n['name']}  ({n['status']})",
)

niche = get_niche(selected["id"])
samples = get_samples_for_niche(niche["id"])

st.divider()
st.markdown(f"## {niche['name']}")

c1, c2, c3 = st.columns(3)
c1.metric("Status", niche["status"].replace("_", " ").title())
c2.metric("Score", f"{niche['score']:.0f}" if niche["score"] else "—")
c3.metric("Confidence", f"{niche['confidence']:.0%}" if niche["confidence"] else "—")

st.markdown(f"**Keywords:** {', '.join(niche.get('keywords', []))}")
if niche.get("notes"):
    st.markdown(f"**Notes:** {niche['notes']}")

st.divider()

# ── Samples ───────────────────────────────────────────────────

sample_a = [s for s in samples if s["sample_type"] == "A"]
sample_b = [s for s in samples if s["sample_type"] == "B"]

col_a, col_b = st.columns(2)

for col, sample_list, label in [(col_a, sample_a, "Sample A"), (col_b, sample_b, "Sample B")]:
    with col:
        st.markdown(f'<p class="noctis-section-header">{label}</p>', unsafe_allow_html=True)
        if not sample_list:
            st.markdown(f"""
            <div style='background:#2E4A6B; border-radius:8px; padding:16px;
                        border: 1px dashed #4DA6C8; text-align:center; color:#aaa;'>
                Not yet collected
            </div>
            """, unsafe_allow_html=True)
        else:
            for s in sample_list:
                listings = get_listings_for_sample(s["id"])
                prices = [l["price"] for l in listings if l["price"]]
                avg_price = sum(prices) / len(prices) if prices else 0
                all_tags = []
                for l in listings:
                    all_tags.extend(l.get("tags", []))
                top_tags = sorted(set(all_tags), key=lambda t: all_tags.count(t), reverse=True)[:8]

                st.markdown(f"""
                <div style='background:#2E4A6B; border-radius:8px; padding:14px; margin-bottom:8px;'>
                    <strong>{s['listing_count']} listings</strong> · {s['sort_on']} sort<br>
                    <span style='font-size:0.8rem; color:#aaa;'>
                        Query: {s['query_variant']}<br>
                        Collected: {s['collected_at'][:16]}
                    </span><br><br>
                    <strong>Avg price:</strong> ${avg_price:.2f}<br>
                    <strong>Price range:</strong> ${min(prices):.2f} – ${max(prices):.2f}<br>
                    <strong>Top tags:</strong> {', '.join(top_tags)}
                </div>
                """, unsafe_allow_html=True)

# ── Calibration result ────────────────────────────────────────

with get_connection() as conn:
    cal = conn.execute(
        "SELECT * FROM calibrations WHERE niche_id=? ORDER BY created_at DESC LIMIT 1",
        (niche["id"],),
    ).fetchone()

if cal:
    cal = dict(cal)
    st.divider()
    st.markdown('<p class="noctis-section-header">Calibration Result</p>', unsafe_allow_html=True)

    passed_color = "#4CAF82" if cal["passed"] else "#E8A838"
    passed_label = "PASSED" if cal["passed"] else "BLOCKED"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Result", passed_label)
    c2.metric("Overall Overlap", f"{cal['overlap_score']:.0%}")
    c3.metric("Tag Jaccard", f"{cal['tag_jaccard']:.0%}")
    c4.metric("Price Similarity", f"{cal['price_similarity']:.0%}")
