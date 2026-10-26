import streamlit as st
import sys
import os
import tempfile

# Make sure the shopping agent module is importable
sys.path.insert(0, os.path.dirname(__file__))
from shopping_agent import agent, describe_image

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopBot – AI Shopping Assistant",
    page_icon="🛍️",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: linear-gradient(135deg, #0d0f1a 0%, #111420 100%);
    color: #e2e8f0;
}

/* Header bar */
.shopbot-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 24px;
    background: rgba(20,24,40,0.9);
    border-radius: 16px;
    border: 1px solid #252c45;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
}

.shopbot-logo {
    font-size: 36px;
    background: linear-gradient(135deg,#6c63ff,#a78bfa);
    border-radius: 50%;
    width: 54px;
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px rgba(108,99,255,0.4);
    flex-shrink: 0;
}

.shopbot-info h2 {
    font-size: 20px;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0 0 2px;
}

.shopbot-info p {
    font-size: 12px;
    color: #64748b;
    margin: 0;
}

.online-badge {
    margin-left: auto;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.3);
    color: #22c55e;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}

/* Chat message bubbles */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 8px 0;
}

.msg-bot {
    display: flex;
    justify-content: flex-start;
    margin: 8px 0;
    align-items: flex-end;
    gap: 10px;
}

.bubble-user {
    background: linear-gradient(135deg, #6c63ff, #a78bfa);
    color: #fff;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    max-width: 75%;
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
}

.bubble-bot {
    background: #1b2035;
    border: 1px solid #252c45;
    color: #e2e8f0;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    max-width: 78%;
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
}

.bot-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg,#6c63ff,#a78bfa);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    flex-shrink: 0;
    box-shadow: 0 0 12px rgba(108,99,255,0.35);
}

/* Image preview box in chat */
.msg-image-preview {
    display: flex;
    justify-content: flex-end;
    margin: 4px 0 8px 0;
}

.image-preview-label {
    font-size: 11px;
    color: #64748b;
    text-align: right;
    margin-bottom: 4px;
}

/* Upload zone styling */
.upload-hint {
    font-size: 11px;
    color: #64748b;
    margin-top: 4px;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid #252c45;
    margin: 12px 0;
}

/* Welcome screen */
.welcome-box {
    text-align: center;
    padding: 40px 20px;
    color: #64748b;
}

.welcome-box .big-icon {
    font-size: 56px;
    margin-bottom: 12px;
}

.welcome-box h3 {
    font-size: 20px;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 8px;
}

.welcome-box p {
    font-size: 14px;
    line-height: 1.7;
    max-width: 360px;
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # {role, content, image_path (optional)}
if "uploaded_image_path" not in st.session_state:
    st.session_state.uploaded_image_path = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="shopbot-header">
  <div class="shopbot-logo">🛍️</div>
  <div class="shopbot-info">
    <h2>ShopBot</h2>
    <p>AI-powered Shopping Assistant</p>
  </div>
  <div class="online-badge">● Online</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_image_path = None
        st.rerun()

    st.markdown("---")

    # ── Image Upload Section ──────────────────────────────────────────────────
    st.markdown("### 📷 Search by Image")
    st.markdown(
        "<span class='upload-hint'>Upload a product photo and ShopBot will identify it and search for it.</span>",
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader(
        "Upload product image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        # Save to a temp file so describe_image can read it
        ext = os.path.splitext(uploaded_file.name)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(uploaded_file.read())
        tmp.flush()
        tmp.close()
        st.session_state.uploaded_image_path = tmp.name

        st.image(uploaded_file, caption="Uploaded image", use_container_width=True)

        if st.button("🔍 Search with this Image", use_container_width=True):
            st.session_state._pending_image = st.session_state.uploaded_image_path
            st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Quick Suggestions")
    suggestions = [
        "Running shoes with 4+ rating",
        "Gaming keyboard under $100",
        "Water bottle",
        "Walking shoes",
        "Wireless headphones",
        "Office chair",
    ]
    for s in suggestions:
        if st.button(f"→ {s}", use_container_width=True, key=f"chip_{s}"):
            st.session_state.messages.append({"role": "user", "content": s})
            st.session_state._pending_query = s
            st.rerun()

    st.markdown("---")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown("**Model:** Qwen3.8-27B via Groq")

# ── Chat history display ──────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-box">
          <div class="big-icon">🛍️</div>
          <h3>Hey! I'm ShopBot 👋</h3>
          <p>Tell me what you're looking for — or <strong>upload a product photo</strong> in the sidebar and I'll identify it, search for it, check ratings, and help you place your order!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                # Show image preview if this message had an image
                if msg.get("image_path"):
                    st.markdown(
                        "<div class='image-preview-label'>📷 Image sent</div>",
                        unsafe_allow_html=True
                    )
                    st.image(msg["image_path"], width=220)

                st.markdown(f"""
                <div class="msg-user">
                  <div class="bubble-user">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-bot">
                  <div class="bot-avatar">🛍️</div>
                  <div class="bubble-bot">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)

# ── Handle pending image search ───────────────────────────────────────────────
pending_image = st.session_state.pop("_pending_image", None)

# ── Handle pending query from sidebar chip ────────────────────────────────────
pending = st.session_state.pop("_pending_query", None)

# ── Chat input ────────────────────────────────────────────────────────────────
user_query = st.chat_input("Search products, check ratings, place an order…")

# ── Execute: Image search ─────────────────────────────────────────────────────
if pending_image:
    user_label = "Find products matching this image."
    st.session_state.messages.append({
        "role": "user",
        "content": user_label,
        "image_path": pending_image
    })

    with st.spinner("ShopBot is analyzing your image…"):
        try:
            # Step 1: Describe image to get search_query
            # describe_image is a StructuredTool, so use .invoke()
            image_description = describe_image.invoke({"image_path": pending_image})

            # Step 2: Pass result to agent with context
            agent_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]   # history without last
            ]
            agent_messages.append({
                "role": "user",
                "content": (
                    f"I have uploaded a product image. Here are the extracted attributes:\n"
                    f"{image_description}\n\n"
                    f"Please search for this product, show me results with ratings, and help me order."
                )
            })
            result = agent.invoke({"messages": agent_messages})
            reply = result["messages"][-1].content
        except Exception as e:
            reply = f"Error processing image: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ── Execute: Text search (chip or chat input) ─────────────────────────────────
query_to_run = pending or user_query

if query_to_run:
    if user_query and not pending:
        st.session_state.messages.append({"role": "user", "content": query_to_run})

    with st.spinner("ShopBot is thinking…"):
        try:
            result = agent.invoke({"messages": [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]})
            reply = result["messages"][-1].content
        except Exception as e:
            reply = f"Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
