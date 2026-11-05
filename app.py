# ============================================================================
# app.py — Streamlit Frontend (Main UI)
# ============================================================================
# YEH FILE KYA KARTI HAI?
# -----------------------
# Ye BrandGuard ka USER INTERFACE hai — web app jo browser mein chalti hai.
# Streamlit use karke 3 screens banayenge:
#
#   🎨 CREATOR VIEW   → Draft submit karo, scores dekho, feedback dekho, resubmit karo
#   ✅ REVIEWER VIEW  → Qualifying posts dekho, approve/reject karo
#   ⚙️ ADMIN VIEW     → Knowledge base manage karo, documents upload karo, stats dekho
#
# STREAMLIT KYA HAI? (Detailed)
# ─────────────────────────────
# Streamlit ek Python library hai jo web apps banati hai BINA HTML/CSS/JS ke.
# Tum sirf Python likhte ho aur Streamlit automatically UI bana deta hai.
#
# st.title("Hello")         → <h1>Hello</h1>
# st.text_input("Name")     → <input type="text">
# st.button("Click")        → <button>Click</button>
# st.file_uploader("File")  → <input type="file">
#
# Run kaise karte hain:
#   streamlit run app.py
# Browser mein http://localhost:8501 pe khulega
#
# SIDEBAR KYA HAI?
# ─────────────────
# Streamlit mein left side mein ek panel hota hai (sidebar) jahan
# navigation/settings rakh sakte ho. st.sidebar.xxx() se access karte hain.
# ============================================================================

import streamlit as st      # Streamlit — web UI library
import os                   # File operations
import json                 # JSON handling
import tempfile             # Temporary files banane ke liye

import db                   # Database operations
import ingest               # Knowledge base ingestion
import evaluate             # AI evaluation engine
import scoring              # Scoring utilities

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
# Ye page ki basic settings hai — title, icon, layout
st.set_page_config(
    page_title="BrandGuard — AI Brand Compliance",
    page_icon="🛡️",
    layout="wide",       # Full-width layout (default is centered/narrow)
    initial_sidebar_state="expanded",  # Sidebar open state mein shuru ho
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
# Streamlit mein custom CSS bhi laga sakte ho for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a73e8;
        margin-bottom: 0.5rem;
    }
    .score-big {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)
# unsafe_allow_html=True → Streamlit ko bolo ki HTML render karo
# (by default Streamlit raw HTML nahi dikhata for security)


# ─── SIDEBAR NAVIGATION ────────────────────────────────────────────────────
# Sidebar mein navigation menu — user choose karega kaunsa view chahiye

st.sidebar.markdown("# 🛡️ BrandGuard")
st.sidebar.markdown("*AI-powered brand compliance*")
st.sidebar.markdown("---")

# Radio buttons = ek mein se ek select karo
page = st.sidebar.radio(
    "Navigate to:",
    ["🎨 Creator — Submit Content", 
     "✅ Reviewer — Approve Posts",
     "⚙️ Admin — Knowledge Base",
     "📊 Dashboard"],
    index=0,  # Default selection (0 = first option)
)
# index=0 → pehla option by default selected

st.sidebar.markdown("---")

# Knowledge base stats sidebar mein dikhao
try:
    kb_stats = ingest.get_collection_stats()
    st.sidebar.metric("📚 KB Chunks", kb_stats["total_chunks"])
except Exception:
    st.sidebar.metric("📚 KB Chunks", 0)

stats = db.get_dashboard_stats()
st.sidebar.metric("📝 Total Submissions", stats["total_submissions"])
st.sidebar.metric("📊 Avg Score", stats["average_score"])


# ============================================================================
# 🎨 CREATOR VIEW — Content Submit & Review
# ============================================================================

def creator_page():
    """
    CREATOR PAGE — Content creators yahan apna draft submit karte hain.
    
    Features:
    1. Text aur/ya image upload karo
    2. Campaign objective select karo
    3. Submit for AI evaluation
    4. Scores aur feedback dekho
    5. Fix karke resubmit karo
    """
    st.markdown('<p class="main-header">🎨 Content Creator</p>', 
                unsafe_allow_html=True)
    st.markdown("Submit your social media content for AI-powered brand compliance review.")
    
    st.markdown("---")
    
    # ─── INPUT FORM ─────────────────────────────────────────────────────
    # st.form() → ek form banao jismein saare inputs ek saath submit hon
    # (nahi toh Streamlit har input change pe page reload karta hai)
    
    with st.form("submission_form", clear_on_submit=False):
        st.subheader("📝 Submit Your Draft")
        
        # Two columns mein layout karo
        col1, col2 = st.columns([2, 1])
        # [2, 1] → pehla column 2x wide, dusra 1x wide
        
        with col1:
            # Creator name
            creator_name = st.text_input(
                "Your Name", 
                value="Creator",
                placeholder="Enter your name"
            )
            
            # Post text
            post_text = st.text_area(
                "Post Text Content",
                height=200,
                placeholder=(
                    "Paste your social media post text here...\n\n"
                    "Example: '🚀 Excited to announce our NEW SuperWidget Pro! "
                    "It's 10x faster than any competitor and guaranteed to boost "
                    "your productivity by 500%! #Innovation #BestInClass'"
                ),
            )
        
        with col2:
            # Campaign objective dropdown
            campaign_objective = st.selectbox(
                "Campaign Objective",
                options=[
                    "brand_awareness",
                    "lead_generation",
                    "engagement",
                    "product_launch",
                    "promotional_offer",
                    "educational",
                    "event_promotion",
                ],
                # selectbox → dropdown menu
                format_func=lambda x: x.replace("_", " ").title(),
                # format_func → display value ko format karo
                # "brand_awareness" → "Brand Awareness"
            )
            
            # Image upload
            uploaded_image = st.file_uploader(
                "Post Image (Optional)",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                # type → allowed file types
            )
            
            if uploaded_image:
                st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
        
        # Submit button
        submitted = st.form_submit_button(
            "🔍 Evaluate My Content", 
            use_container_width=True,
            type="primary",   # Blue highlighted button
        )
    
    # ─── EVALUATION LOGIC ───────────────────────────────────────────────
    # Jab user submit button dabaaye, tab evaluate karo
    
    if submitted:
        if not post_text.strip() and not uploaded_image:
            st.error("❌ Please provide at least text content or an image!")
            return
        
        # Image ko temporary file mein save karo (agar hai toh)
        image_path = None
        if uploaded_image:
            # Temporary file mein save karo
            temp_dir = os.path.join(os.path.dirname(__file__), "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            # os.makedirs → folder banao (exist_ok=True → agar hai toh error mat do)
            
            image_path = os.path.join(temp_dir, uploaded_image.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_image.getbuffer())
        
        # Database mein submission save karo
        submission_id = db.create_submission(
            creator_name=creator_name,
            text_content=post_text,
            image_path=image_path,
            campaign_objective=campaign_objective,
        )
        
        # AI Evaluation start karo
        with st.spinner("🤖 AI is evaluating your content... This may take 15-30 seconds."):
            # st.spinner → loading animation dikhao jab tak kaam ho raha hai
            result = evaluate.evaluate_post(
                text_content=post_text,
                campaign_objective=campaign_objective,
                image_path=image_path,
                submission_id=submission_id,
            )
        
        if result.get("status") == "error":
            st.error(f"❌ Evaluation failed: {result.get('message', 'Unknown error')}")
            return
        
        # ─── RESULTS DISPLAY ────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 Evaluation Results")
        
        # Decision banner
        decision = result["decision"]
        if decision == "pass":
            st.success(f"✅ {result['decision_reason']}")
        elif decision == "needs_improvement":
            st.warning(f"⚠️ {result['decision_reason']}")
        else:
            st.error(f"❌ {result['decision_reason']}")
        
        # Overall score — bada dikhao
        score_col1, score_col2, score_col3 = st.columns(3)
        
        with score_col1:
            st.metric(
                "Overall Score",
                f"{result['overall_score']}/100",
                delta=None,
            )
            # st.metric → ek number ko highlight karke dikhao
        
        with score_col2:
            st.metric(
                "Critical Issues",
                len(result["critical_flags"]),
                delta=None,
            )
        
        with score_col3:
            st.metric(
                "Can Send for Review",
                "Yes ✅" if result["can_send_for_review"] else "No ❌",
            )
        
        # Category-wise scores
        st.markdown("---")
        st.subheader("📈 Category Scores")
        
        category_labels = {
            "factual_accuracy": "📋 Factual Accuracy (20%)",
            "regulatory_compliance": "⚖️ Regulatory Compliance (20%)",
            "brand_identity": "🏷️ Brand Identity (15%)",
            "visual_consistency": "🎨 Visual Consistency (15%)",
            "campaign_effectiveness": "🎯 Campaign Effectiveness (10%)",
            "accessibility": "♿ Accessibility (10%)",
            "overall_design": "✨ Overall Design (10%)",
        }
        
        # Scores ko 2 rows mein dikhao
        scores = result.get("category_scores", {})
        cat_keys = list(category_labels.keys())
        
        # Row 1: first 4 categories
        cols_row1 = st.columns(4)
        for i, key in enumerate(cat_keys[:4]):
            with cols_row1[i]:
                score = scores.get(key, 0)
                color = scoring.get_score_color(score)
                st.metric(category_labels[key], f"{color} {score}/100")
        
        # Row 2: last 3 categories
        cols_row2 = st.columns(4)
        for i, key in enumerate(cat_keys[4:]):
            with cols_row2[i]:
                score = scores.get(key, 0)
                color = scoring.get_score_color(score)
                st.metric(category_labels[key], f"{color} {score}/100")
        
        # Category-wise detailed feedback
        st.markdown("---")
        st.subheader("💬 Detailed Feedback")
        
        category_feedback = result.get("category_feedback", {})
        for cat, label in category_labels.items():
            feedback = category_feedback.get(cat, "No feedback available.")
            with st.expander(f"{label}"):
                # st.expander → click to expand/collapse section
                st.write(feedback)
        
        # Critical issues
        if result["critical_flags"]:
            st.markdown("---")
            st.subheader("🚨 Critical Issues")
            for flag in result["critical_flags"]:
                st.error(f"🔴 {flag}")
        
        # Suggestions
        suggestions = result.get("suggestions", [])
        if suggestions:
            st.markdown("---")
            st.subheader("💡 Actionable Suggestions")
            for i, sug in enumerate(suggestions, 1):
                if isinstance(sug, dict):
                    with st.expander(f"Suggestion {i}: {sug.get('issue', 'Issue')}"):
                        st.markdown(f"**🔍 Issue:** {sug.get('issue', 'N/A')}")
                        st.markdown(f"**⚠️ Risk:** {sug.get('risk', 'N/A')}")
                        st.markdown(f"**📋 Guideline:** {sug.get('guideline_reference', 'N/A')}")
                        st.markdown(f"**✅ Fix:** {sug.get('fix', 'N/A')}")
                else:
                    st.info(f"💡 {sug}")
        
        # Overall summary
        summary = result.get("overall_summary", "")
        if summary:
            st.markdown("---")
            st.info(f"📝 **Summary:** {summary}")
        
        # Send for Review button (agar eligible hai)
        if result["can_send_for_review"]:
            st.markdown("---")
            if st.button("📤 Send for Human Review", type="primary", 
                         use_container_width=True):
                db.update_submission_status(submission_id, "sent_for_review")
                st.success("✅ Post sent for human review! A reviewer will check it soon.")
                st.balloons()  # 🎈 Celebration animation!
    
    # ─── SUBMISSION HISTORY ─────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📜 Your Submission History")
    
    all_subs = db.get_all_submissions()
    if all_subs:
        for sub in all_subs[:10]:  # Last 10 show karo
            status_emoji = {
                "pending": "⏳", "evaluated": "📊", 
                "sent_for_review": "📤", "approved": "✅", "rejected": "❌"
            }.get(sub["status"], "❓")
            
            with st.expander(
                f"{status_emoji} Submission #{sub['id']} — "
                f"{sub['status'].upper()} — {sub['created_at'][:16]}"
            ):
                st.write(f"**Creator:** {sub['creator_name']}")
                st.write(f"**Objective:** {sub['campaign_objective']}")
                if sub["text_content"]:
                    st.write(f"**Text:** {sub['text_content'][:200]}...")
                
                # Latest evaluation dikhao
                latest_eval = db.get_latest_evaluation(sub["id"])
                if latest_eval:
                    st.write(f"**Score:** {latest_eval['overall_score']}/100")
                    st.write(f"**Critical Issues:** {len(latest_eval['critical_flags'])}")
    else:
        st.info("No submissions yet. Submit your first content above! ☝️")


# ============================================================================
# ✅ REVIEWER VIEW — Human Approval
# ============================================================================

def reviewer_page():
    """
    REVIEWER PAGE — Managers/reviewers yahan posts approve/reject karte hain.
    
    Sirf wo posts dikhenge jo:
    1. AI evaluation pass kar chuki hain (score >= 85)
    2. No critical issues
    3. Creator ne "Send for Review" kiya hai
    """
    st.markdown('<p class="main-header">✅ Content Reviewer</p>', 
                unsafe_allow_html=True)
    st.markdown("Review and approve content that has passed AI evaluation.")
    
    st.markdown("---")
    
    # Reviewer name
    reviewer_name = st.text_input("Your Name (Reviewer)", value="Manager")
    
    st.markdown("---")
    
    # Review ke liye ready submissions lo
    reviewable = db.get_reviewable_submissions()
    
    if not reviewable:
        st.info("📭 No content is waiting for review right now.")
        st.markdown("Posts will appear here when creators submit content that passes "
                     "AI evaluation (score ≥ 85, no critical issues).")
        return
    
    st.subheader(f"📋 {len(reviewable)} Post(s) Awaiting Review")
    
    for sub in reviewable:
        with st.expander(
            f"📄 Submission #{sub['id']} — Score: {sub['overall_score']}/100 — "
            f"{sub['created_at'][:16]}",
            expanded=True,
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Creator:** {sub.get('creator_name', 'Unknown')}")
                st.markdown(f"**Objective:** {sub.get('campaign_objective', 'N/A')}")
                
                if sub.get("text_content"):
                    st.markdown("**Post Text:**")
                    st.text(sub["text_content"])
                
                if sub.get("image_path") and os.path.exists(sub["image_path"]):
                    st.image(sub["image_path"], caption="Post Image", width=300)
            
            with col2:
                st.metric("AI Score", f"{sub['overall_score']}/100")
                st.metric("Critical Issues", 
                          "None ✅" if not sub.get("has_critical_issues") else "Yes ❌")
            
            # Show latest evaluation details
            latest_eval = db.get_latest_evaluation(sub["id"])
            if latest_eval:
                st.markdown("**Category Scores:**")
                for cat in ["factual_accuracy", "regulatory_compliance", "brand_identity",
                            "visual_consistency", "campaign_effectiveness", 
                            "accessibility", "overall_design"]:
                    score = latest_eval.get(cat, 0)
                    color = scoring.get_score_color(score)
                    st.write(f"  {color} {cat.replace('_', ' ').title()}: {score}/100")
            
            # Review actions
            st.markdown("---")
            review_col1, review_col2, review_col3 = st.columns(3)
            
            with review_col1:
                if st.button(f"✅ Approve", key=f"approve_{sub['id']}",
                             type="primary"):
                    eval_id = sub.get("eval_id", latest_eval["id"] if latest_eval else 0)
                    db.save_review(sub["id"], eval_id, reviewer_name, 
                                  "approved", "Approved by reviewer.")
                    st.success("✅ Post approved!")
                    st.rerun()  # Page reload karo taaki list update ho
            
            with review_col2:
                if st.button(f"❌ Reject", key=f"reject_{sub['id']}"):
                    eval_id = sub.get("eval_id", latest_eval["id"] if latest_eval else 0)
                    reject_reason = st.text_input(
                        "Reason for rejection", 
                        key=f"reject_reason_{sub['id']}"
                    )
                    db.save_review(sub["id"], eval_id, reviewer_name,
                                  "rejected", reject_reason or "Rejected by reviewer.")
                    st.error("❌ Post rejected.")
                    st.rerun()
            
            with review_col3:
                if st.button(f"🔄 Request Revision", key=f"revise_{sub['id']}"):
                    eval_id = sub.get("eval_id", latest_eval["id"] if latest_eval else 0)
                    db.save_review(sub["id"], eval_id, reviewer_name,
                                  "revision_needed", "Please revise and resubmit.")
                    st.warning("🔄 Revision requested. Creator will be notified.")
                    st.rerun()


# ============================================================================
# ⚙️ ADMIN VIEW — Knowledge Base Management
# ============================================================================

def admin_page():
    """
    ADMIN PAGE — Knowledge base manage karo.
    
    Features:
    1. Documents upload karo (brand guidelines, product facts, legal rules)
    2. Direct text paste karke guidelines add karo
    3. Uploaded documents dekho
    4. Knowledge base search karo
    """
    st.markdown('<p class="main-header">⚙️ Knowledge Base Admin</p>', 
                unsafe_allow_html=True)
    st.markdown("Upload and manage your organisation's brand guidelines, product facts, "
                "and compliance rules.")
    
    st.markdown("---")
    
    # ─── TAB LAYOUT ─────────────────────────────────────────────────────
    # Tabs = multiple sections in same page (like browser tabs)
    tab1, tab2, tab3 = st.tabs([
        "📤 Upload Documents", 
        "✍️ Add Text Guidelines", 
        "📚 View Knowledge Base"
    ])
    
    # ─── TAB 1: FILE UPLOAD ─────────────────────────────────────────────
    with tab1:
        st.subheader("Upload Brand Documents")
        
        doc_type = st.selectbox(
            "Document Type",
            ["guideline", "factsheet", "legal", "template"],
            format_func=lambda x: {
                "guideline": "📋 Brand Guidelines",
                "factsheet": "📊 Product Fact Sheet",
                "legal": "⚖️ Legal/Regulatory Rules",
                "template": "📄 Content Template",
            }.get(x, x),
            key="upload_doc_type",
        )
        
        uploaded_files = st.file_uploader(
            "Upload files (.txt or .pdf)",
            type=["txt", "pdf"],
            accept_multiple_files=True,  # Multiple files ek saath upload karo
            key="kb_upload",
        )
        
        if uploaded_files and st.button("📥 Ingest Documents", type="primary"):
            for uploaded_file in uploaded_files:
                # Temporary file mein save karo
                temp_dir = os.path.join(os.path.dirname(__file__), "temp_uploads")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Ingest karo
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    result = ingest.ingest_document(temp_path, doc_type)
                
                if result["status"] == "success":
                    st.success(
                        f"✅ {uploaded_file.name}: {result['chunk_count']} chunks "
                        f"ingested ({result['char_count']} characters)"
                    )
                else:
                    st.error(f"❌ {uploaded_file.name}: {result.get('message', 'Error')}")
    
    # ─── TAB 2: TEXT INPUT ──────────────────────────────────────────────
    with tab2:
        st.subheader("Add Guidelines as Text")
        st.markdown("Directly paste your brand guidelines, rules, or product facts below.")
        
        with st.form("text_ingest_form"):
            title = st.text_input(
                "Document Title", 
                placeholder="e.g., Brand Voice Guidelines 2026"
            )
            
            text_doc_type = st.selectbox(
                "Document Type",
                ["guideline", "factsheet", "legal", "template"],
                format_func=lambda x: x.replace("_", " ").title(),
                key="text_doc_type",
            )
            
            guidelines_text = st.text_area(
                "Guidelines Text",
                height=300,
                placeholder=(
                    "Paste your brand guidelines here...\n\n"
                    "Example:\n"
                    "BRAND VOICE:\n"
                    "- Our tone is professional yet approachable\n"
                    "- We never use slang or informal abbreviations\n"
                    "- Always address the customer with respect\n\n"
                    "PRODUCT FACTS:\n"
                    "- SuperWidget was launched in March 2026\n"
                    "- It supports up to 1000 concurrent users\n"
                    "- Available in 3 tiers: Basic, Pro, Enterprise"
                ),
            )
            
            if st.form_submit_button("📥 Ingest Text", type="primary"):
                if title.strip() and guidelines_text.strip():
                    with st.spinner("Processing text..."):
                        result = ingest.ingest_text_directly(
                            guidelines_text, title, text_doc_type
                        )
                    
                    if result["status"] == "success":
                        st.success(
                            f"✅ '{title}': {result['chunk_count']} chunks ingested!"
                        )
                    else:
                        st.error(f"❌ {result.get('message', 'Error')}")
                else:
                    st.error("Please provide both a title and guidelines text.")
    
    # ─── TAB 3: VIEW KNOWLEDGE BASE ────────────────────────────────────
    with tab3:
        st.subheader("Knowledge Base Contents")
        
        # Stats dikhao
        col1, col2 = st.columns(2)
        kb_stats = ingest.get_collection_stats()
        
        with col1:
            st.metric("Total Chunks in Vector DB", kb_stats["total_chunks"])
        with col2:
            docs = db.get_all_documents()
            st.metric("Total Documents", len(docs))
        
        # Documents list
        if docs:
            st.markdown("---")
            st.markdown("### 📄 Uploaded Documents")
            for doc in docs:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f"**{doc['filename']}** ({doc['doc_type']}) — "
                        f"{doc['chunk_count']} chunks — "
                        f"v{doc['version']} — {doc['uploaded_at'][:16]}"
                    )
                    if doc.get("content_preview"):
                        st.caption(doc["content_preview"][:200] + "...")
                with col2:
                    if st.button("🗑️", key=f"del_doc_{doc['id']}"):
                        db.delete_document(doc["id"])
                        st.warning(f"Document '{doc['filename']}' deactivated.")
                        st.rerun()
        else:
            st.info("📭 No documents uploaded yet. Use the tabs above to add guidelines!")
        
        # Search in knowledge base
        st.markdown("---")
        st.markdown("### 🔍 Search Knowledge Base")
        search_query = st.text_input(
            "Search query", 
            placeholder="e.g., What is our brand color?"
        )
        
        if search_query:
            with st.spinner("Searching..."):
                from retrive import search_knowledge_base
                results = search_knowledge_base(search_query, n_results=5)
            
            if results:
                for i, r in enumerate(results, 1):
                    with st.expander(
                        f"Result {i} — {r['source']} "
                        f"(relevance: {r['relevance_score']:.4f})"
                    ):
                        st.write(r["text"])
            else:
                st.info("No matching results found.")


# ============================================================================
# 📊 DASHBOARD — Analytics & Overview
# ============================================================================

def dashboard_page():
    """
    DASHBOARD — Overall stats aur analytics.
    
    Ye page managers ke liye hai — high-level overview:
    1. Total submissions, approval rate
    2. Average scores
    3. Common issues
    """
    st.markdown('<p class="main-header">📊 BrandGuard Dashboard</p>', 
                unsafe_allow_html=True)
    st.markdown("Overview of content evaluation activity and brand compliance metrics.")
    
    st.markdown("---")
    
    # Stats
    stats = db.get_dashboard_stats()
    
    # Top-level metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📝 Total Submissions", stats["total_submissions"])
    with col2:
        st.metric("✅ Approved", stats.get("approved_count", 0))
    with col3:
        st.metric("❌ Rejected", stats.get("rejected_count", 0))
    with col4:
        st.metric("⏳ Pending", stats.get("pending_count", 0))
    with col5:
        st.metric("📊 Avg Score", stats.get("average_score", 0))
    
    # Knowledge base stats
    st.markdown("---")
    st.subheader("📚 Knowledge Base")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", stats.get("total_documents", 0))
    with col2:
        kb_stats = ingest.get_collection_stats()
        st.metric("Guideline Chunks", kb_stats["total_chunks"])
    
    # Recent submissions
    st.markdown("---")
    st.subheader("📜 Recent Submissions")
    
    all_subs = db.get_all_submissions()
    if all_subs:
        for sub in all_subs[:20]:
            status_emoji = {
                "pending": "⏳", "evaluated": "📊",
                "sent_for_review": "📤", "approved": "✅", "rejected": "❌"
            }.get(sub["status"], "❓")
            
            latest_eval = db.get_latest_evaluation(sub["id"])
            score_text = f"{latest_eval['overall_score']}/100" if latest_eval else "N/A"
            
            st.markdown(
                f"{status_emoji} **#{sub['id']}** — {sub['creator_name']} — "
                f"Score: {score_text} — {sub['status'].upper()} — "
                f"{sub['created_at'][:16]}"
            )
    else:
        st.info("No submissions yet.")


# ============================================================================
# 🚀 MAIN — Page Router
# ============================================================================
# Page variable ke basis pe sahi page function call karo

if "Creator" in page:
    creator_page()
elif "Reviewer" in page:
    reviewer_page()
elif "Admin" in page:
    admin_page()
elif "Dashboard" in page:
    dashboard_page()
