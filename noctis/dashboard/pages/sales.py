import streamlit as st
from core.database import get_connection

st.markdown("# 📈 Sales Tracker")
st.caption("Your shop revenue by listing and pipeline item · synced via OAuth")
st.divider()

def get_sales_summary():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT s.*, ml.title, ml.price, n.name as niche_name
            FROM sales s
            LEFT JOIN my_listings ml ON s.my_listing_id = ml.id
            LEFT JOIN niches n ON ml.niche_id = n.id
            ORDER BY s.sale_date DESC
        """).fetchall()
        return [dict(r) for r in rows]

sales = get_sales_summary()

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("⟳ Sync Sales", use_container_width=True):
        st.warning("Sales sync module not yet connected — build Phase 4 first.")

if not sales:
    st.info("No sales data synced yet. Complete OAuth setup and click 'Sync Sales' to pull your shop receipts.")
else:
    total_revenue = sum(s.get("amount_paid", 0) or 0 for s in sales)
    by_niche = {}
    for s in sales:
        key = s.get("niche_name") or "Unlinked"
        by_niche[key] = by_niche.get(key, 0) + (s.get("amount_paid", 0) or 0)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Revenue", f"${total_revenue:,.2f}")
    m2.metric("Total Orders", len(sales))
    m3.metric("Pipeline Items with Sales", len([k for k in by_niche if k != "Unlinked"]))

    st.divider()
    st.markdown('<p class="noctis-section-header">Revenue by Pipeline Item</p>', unsafe_allow_html=True)

    sorted_niches = sorted(by_niche.items(), key=lambda x: x[1], reverse=True)
    for niche_name, revenue in sorted_niches:
        pct = revenue / total_revenue if total_revenue > 0 else 0
        st.markdown(f"""
        <div style='margin-bottom:10px;'>
            <div style='display:flex; justify-content:space-between; margin-bottom:3px;'>
                <span style='font-size:0.9rem;'>{niche_name}</span>
                <span style='font-weight:700;'>${revenue:,.2f}</span>
            </div>
            <div style='background:#1E2D3E; border-radius:4px; overflow:hidden; height:6px;'>
                <div style='background:#4DA6C8; width:{pct*100:.1f}%; height:100%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<p class="noctis-section-header">Recent Orders</p>', unsafe_allow_html=True)

    for sale in sales[:20]:
        date_str = (sale.get("sale_date") or "")[:10]
        st.markdown(f"""
        <div style='display:flex; padding:7px 0; border-bottom:1px solid #2E4A6B; font-size:0.85rem;'>
            <span style='color:#aaa; min-width:100px;'>{date_str}</span>
            <span style='flex:1; color:#F0F4F8;'>{sale.get('title') or 'Unknown listing'}</span>
            <span style='color:#4CAF82; font-weight:700;'>${sale.get('amount_paid', 0):.2f}</span>
        </div>
        """, unsafe_allow_html=True)
