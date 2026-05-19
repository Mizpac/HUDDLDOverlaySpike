import streamlit as st
import anthropic
from core.database import (
    get_pipeline_counts, get_all_niches, get_open_flags,
    get_connection, create_dream_session, save_dream_messages, get_dream_sessions,
    get_dream_session, stage_idea, get_staged_ideas, promote_idea_to_pipeline,
    create_niche,
)
from config import ANTHROPIC_API_KEY, DREAM_LAB_MODEL, DREAM_LAB_MAX_TOKENS

st.markdown("# 🧪 Dream Lab")
st.caption("Explore new ideas with Claude · powered by your real pipeline data")
st.divider()

if not ANTHROPIC_API_KEY:
    st.error("ANTHROPIC_API_KEY not set. Add it to your Replit Secrets or .env file.")
    st.stop()

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Build live context from database ─────────────────────────

def build_context(counts: dict, niches: list, flags: list) -> str:
    validated = [n for n in niches if n["status"] == "validated"]
    listed = [n for n in niches if n["status"] == "listed"]
    top_scored = sorted(
        [n for n in niches if n["score"] is not None],
        key=lambda x: x["score"],
        reverse=True,
    )[:3]

    lines = [
        "You are Noctis, a market intelligence assistant for Night Owl Printing, an Etsy shop.",
        "You have access to the seller's real pipeline data. Use it to give grounded, specific advice.",
        "",
        f"PIPELINE SUMMARY:",
        f"  Collecting: {counts.get('collecting', 0)}",
        f"  Calibrating: {counts.get('calibrating', 0)}",
        f"  Validated (ready for content): {counts.get('validated', 0)}",
        f"  In Progress: {counts.get('in_progress', 0)}",
        f"  Listed on Etsy: {counts.get('listed', 0)}",
        f"  Open flags needing review: {len(flags)}",
    ]

    if validated:
        lines.append(f"\nVALIDATED ITEMS READY FOR CONTENT:")
        for n in validated:
            lines.append(f"  - {n['name']} (keywords: {', '.join(n.get('keywords', [])[:3])})")

    if listed:
        lines.append(f"\nCURRENTLY LISTED ON ETSY:")
        for n in listed:
            lines.append(f"  - {n['name']}")

    if top_scored:
        lines.append(f"\nTOP SCORING PIPELINE ITEMS:")
        for n in top_scored:
            lines.append(f"  - {n['name']}: score {n['score']:.0f}, confidence {n['confidence']:.0%}")

    lines.append("""
INSTRUCTIONS:
- When the seller shares a new product idea, evaluate it against the pipeline data above.
- Point out overlaps with existing validated items as opportunities, not conflicts.
- Highlight gaps the new idea fills that current items don't cover.
- Keep responses concise and action-oriented.
- When an idea is worth pursuing, say so clearly and suggest what keywords to research.
- If you identify a concrete idea ready to add to the pipeline, end your message with:
  IDEA_READY: [idea name] | [comma-separated keywords]
""")
    return "\n".join(lines)


QUICK_PROMPTS = {
    "New idea check":    "I have a new product idea I'd like to explore. Based on my current pipeline, does it make sense to pursue?",
    "Map a concept":     "Help me map out what this product concept looks like — who buys it, what they search for, and what signals to watch.",
    "Price angle":       "Looking at my current pipeline, what pricing strategy makes sense for a new product in this space?",
    "Marketing angle":   "Given what's working in my pipeline, what's the best marketing angle for a new idea I'm considering?",
    "Risk check":        "Walk me through the risks of pursuing this idea before I commit it to the pipeline.",
}

# ── Session management ────────────────────────────────────────

sessions = get_dream_sessions()
session_names = {s["id"]: s["title"] for s in sessions}

col_sess, col_new = st.columns([3, 1])
with col_sess:
    if sessions:
        session_options = [s["id"] for s in sessions]
        selected_session_id = st.selectbox(
            "Session",
            session_options,
            format_func=lambda sid: session_names.get(sid, f"Session {sid}"),
        )
    else:
        selected_session_id = None

with col_new:
    new_title = st.text_input("New session name", placeholder="My idea...")
    if st.button("＋ Start", use_container_width=True) and new_title.strip():
        selected_session_id = create_dream_session(new_title.strip())
        st.rerun()

if not selected_session_id:
    st.info("Start a new session above to begin.")
    st.stop()

session = get_dream_session(selected_session_id)
messages = session.get("messages", [])

st.divider()

# ── Main layout ───────────────────────────────────────────────

left, right = st.columns([2, 1])

counts = get_pipeline_counts()
flags = get_open_flags()
niches = get_all_niches()

with right:
    st.markdown('<p class="noctis-section-header">Live Context</p>', unsafe_allow_html=True)
    validated_count = counts.get("validated", 0)
    listed_count = counts.get("listed", 0)
    top = sorted([n for n in niches if n["score"]], key=lambda x: x["score"], reverse=True)

    st.markdown(f"""
    <div style='background:#2E4A6B; border-radius:8px; padding:14px; font-size:0.85rem;'>
        <strong style='color:#4DA6C8;'>What Claude knows:</strong><br><br>
        ✅ {validated_count} validated item(s)<br>
        🛒 {listed_count} listed on Etsy<br>
        ⚠️ {len(flags)} open flag(s)<br>
        {'<br>🏆 Top: ' + top[0]['name'] if top else ''}
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="noctis-section-header" style="margin-top:16px;">Quick Prompts</p>', unsafe_allow_html=True)
    for label in QUICK_PROMPTS:
        if st.button(label, use_container_width=True, key=f"qp_{label}"):
            st.session_state["dream_prefill"] = QUICK_PROMPTS[label]
            st.rerun()

    st.divider()
    st.markdown('<p class="noctis-section-header">Staged Ideas</p>', unsafe_allow_html=True)
    staged = get_staged_ideas(selected_session_id)
    if not staged:
        st.caption("Ideas identified during this session will appear here.")
    else:
        for idea in staged:
            st.markdown(f"""
            <div style='background:#2E4A6B; border-radius:6px; padding:10px;
                        border-left:3px solid #4DA6C8; margin-bottom:6px;
                        font-size:0.82rem;'>
                {idea['idea_text']}
            </div>
            """, unsafe_allow_html=True)

            promo_col, drop_col = st.columns(2)
            with promo_col:
                if st.button("Add to Pipeline", key=f"promote_{idea['id']}"):
                    parts = idea["idea_text"].split("|")
                    name = parts[0].strip()
                    keywords = [k.strip() for k in parts[1].split(",")] if len(parts) > 1 else [name]
                    niche_id = create_niche(name, keywords)
                    promote_idea_to_pipeline(idea["id"], niche_id)
                    st.success(f"'{name}' added to pipeline!")
                    st.rerun()
            with drop_col:
                if st.button("Drop", key=f"drop_{idea['id']}"):
                    with get_connection() as conn:
                        conn.execute("UPDATE staged_ideas SET status='dropped' WHERE id=?", (idea["id"],))
                    st.rerun()

with left:
    st.markdown('<p class="noctis-section-header">Conversation</p>', unsafe_allow_html=True)

    # Display message history
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        bubble_bg = "#1E2D3E" if role == "assistant" else "#2E4A6B"
        label = "🦉 Noctis" if role == "assistant" else "You"
        st.markdown(f"""
        <div style='background:{bubble_bg}; border-radius:8px; padding:12px 16px;
                    margin-bottom:8px; font-size:0.88rem;'>
            <strong style='color:#4DA6C8;'>{label}</strong><br>
            {content.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    # Input
    prefill = st.session_state.pop("dream_prefill", "")
    user_input = st.text_area(
        "Your message",
        value=prefill,
        height=100,
        placeholder="Share an idea, ask a question, or use a Quick Prompt →",
        label_visibility="collapsed",
    )

    if st.button("Send →", use_container_width=True, type="primary") and user_input.strip():
        messages.append({"role": "user", "content": user_input.strip()})

        with st.spinner("Thinking..."):
            system_prompt = build_context(counts, niches, flags)
            response = client.messages.create(
                model=DREAM_LAB_MODEL,
                max_tokens=DREAM_LAB_MAX_TOKENS,
                system=system_prompt,
                messages=messages,
            )
            reply = response.content[0].text

        messages.append({"role": "assistant", "content": reply})
        save_dream_messages(selected_session_id, messages)

        # Auto-detect staged ideas
        if "IDEA_READY:" in reply:
            for line in reply.split("\n"):
                if line.strip().startswith("IDEA_READY:"):
                    idea_text = line.replace("IDEA_READY:", "").strip()
                    stage_idea(selected_session_id, idea_text)

        st.rerun()
