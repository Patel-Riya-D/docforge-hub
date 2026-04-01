"""
ui.py

Frontend module for DocForge Hub built using Streamlit.

This module provides an interactive user interface for:
- AI-powered document generation
- Draft review and approval workflows
- RAG-based document querying and comparison
- Conversational assistant (StateCase)
- Ticket management system integrated with Notion

Core Features:
- Multi-step document generation wizard
- Session-based state management using Streamlit session_state
- Caching to optimize API calls and UI responsiveness
- Conversational AI interface with memory and ticket escalation
- Real-time ticket tracking and filtering

Key Fixes & Improvements:
- Stable chat UI using st.chat_input (no layout issues)
- Session caching to prevent unnecessary API calls
- Improved state handling for draft generation workflow
- Proper chat rendering order (history → input)
- Ticket status alignment with Notion (Open, In Progress, Closed)

Dependencies:
- Streamlit for UI
- Requests for backend API communication
- Pandas for table rendering

Notes:
- Backend API must be running for full functionality
- Uses environment variable `API_BASE_URL` for API routing

StateCase Assistant Chat Flow:

1. Display previous chat history from session_state
2. User enters query via st.chat_input
3. Build conversation_context from recent messages
4. Send request to backend API (/statecase-chat)
5. Receive:
    - answer
    - confidence
    - sources
6. Store both user and assistant messages in session_state
7. Trigger st.rerun() to re-render chat correctly

Key Advantages:
- Maintains conversational memory
- Supports follow-up queries
- Integrates RAG + LLM + ticketing
- Clean UI without CSS hacks

My Tickets Tab:

Displays support tickets fetched from Notion database.

Features:
- Refresh tickets from Notion API
- Display ticket metrics:
    • Total
    • Open
    • In Progress
    • Closed
- Filtering:
    • Status
    • Priority
    • Search by title
- Card-based UI layout

Data Fields:
- Title
- Status
- Priority
- Category
- Owner

Notes:
- Uses Notion API directly
- Syncs with backend ticket creation system
"""

import os
import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
import pandas as pd
from backend.generation.question_label_enhancer import enhance_label
from datetime import datetime, date
import json

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# -------------------- UI CONFIG --------------------
st.set_page_config(
    page_title="DocForge Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- SESSION STATE --------------------
if "selected_draft_id" not in st.session_state:
    st.session_state.selected_draft_id = None
if "last_generated_id" not in st.session_state:
    st.session_state.last_generated_id = None
if "generation_in_progress" not in st.session_state:
    st.session_state.generation_in_progress = False
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "company_profile" not in st.session_state:
    st.session_state.company_profile = {
        "company_name": "",
        "industry": "",
        "employee_count": 100,
        "region": "",
        "compliance": "",
        "jurisdiction": "",
        "founded_year": "",
        "headquarters_location": "",
        "ceo_name": "",
        "cto_name": "",
        "founders": "",
        "company_background": ""
    }
if "pending_questions" not in st.session_state:
    st.session_state.pending_questions = []
if "question_answers" not in st.session_state:
    st.session_state.question_answers = {}
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = False
if "questions_initialized" not in st.session_state:
    st.session_state.questions_initialized = False

# Draft detail cache — keyed by draft_id
# Structure: { draft_id: { ...draft_detail dict... } }
if "draft_cache" not in st.session_state:
    st.session_state.draft_cache = {}

# Documents meta cache per department
if "documents_meta_cache" not in st.session_state:
    st.session_state.documents_meta_cache = {}

# Drafts library cache
if "drafts_library_cache" not in st.session_state:
    st.session_state.drafts_library_cache = None

# StateCase — must be initialized at top level before any tab renders
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "sc_tickets" not in st.session_state:
    st.session_state.sc_tickets = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "user1" 

# -------------------- HELPER FUNCTIONS --------------------

def format_date(date_string):
    """
    Convert ISO date string into human-readable format.

    Args:
        date_string (str): ISO formatted datetime string

    Returns:
        str: Formatted date string (e.g., "March 10, 2025 at 05:30 PM")

    Notes:
        - Returns original string if parsing fails
    """
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        return date_string


def get_draft_detail(draft_id):
    """
    Fetch draft details from backend API with caching.

    Args:
        draft_id (str): Unique identifier of the draft

    Returns:
        dict | None: Draft data if successful, else None

    Behavior:
        - Uses session_state cache to avoid repeated API calls
        - Stores fetched draft in cache
        - Displays error if API request fails
    """

    if draft_id in st.session_state.draft_cache:
        return st.session_state.draft_cache[draft_id]
    try:
        resp = requests.get(f"{API_BASE_URL}/documents/draft/{draft_id}")
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.draft_cache[draft_id] = data
            return data
    except Exception as e:
        st.error(f"❌ Failed to load draft: {e}")
    return None


def invalidate_draft_cache(draft_id):
    """
    Remove a draft from local cache.

    Args:
        draft_id (str): Draft identifier

    Returns:
        None

    Purpose:
        - Ensures fresh data is fetched after updates (edit, approve, delete)
    """
    if draft_id in st.session_state.draft_cache:
        del st.session_state.draft_cache[draft_id]


def render_field(label, field, key):
    """
    Dynamically render input fields based on field type.

    Args:
        label (str): Display label for the field
        field (dict): Field configuration (type, options, etc.)
        key (str): Unique Streamlit key

    Returns:
        Any: User input value

    Supported Types:
        - text, textarea, number, boolean
        - date, dropdown, multiselect

    Notes:
        - Automatically restores previous values from session_state
    """
    field_type = field["type"]
    existing_value = st.session_state.get(key, None)

    if field_type == "text":
        return st.text_input(label, key=key, value=existing_value if existing_value else "")
    elif field_type == "textarea":
        return st.text_area(label, key=key, value=existing_value if existing_value else "", height=100)
    elif field_type == "number":
        return st.number_input(label, key=key, value=existing_value if existing_value else 0)
    elif field_type == "boolean":
        return st.checkbox(label, key=key, value=existing_value if existing_value else False)
    elif field_type == "date":
        return st.date_input(label, key=key, value=existing_value if existing_value else None)
    elif field_type == "dropdown":
        return st.selectbox(
            label, field.get("options", []), key=key,
            index=field.get("options", []).index(existing_value) if existing_value in field.get("options", []) else 0
        )
    elif field_type == "multiselect":
        return st.multiselect(label, field.get("options", []), key=key, default=existing_value if existing_value else [])
    else:
        return st.text_input(label, key=key, value=existing_value if existing_value else "")


def render_company_step():
    """
    Render the company profile input form.

    Captures:
        - Company details (name, industry, region, etc.)
        - Leadership and background information

    Behavior:
        - Updates session_state.company_profile
        - Used as Step 1 in document generation workflow

    Notes:
        - Mandatory fields marked with '*'
    """
    with st.container(border=True):
        col1, col2 = st.columns([1, 11])
        with col1:
            st.markdown("# 🏢")
        with col2:
            st.subheader("Company Profile")
            st.caption("Fields marked with * are mandatory and will be embedded into the document.")

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name *", key="company_name",
                                     value=st.session_state.company_profile.get("company_name", ""))
        industry = st.text_input("Industry *", key="industry",
                                 value=st.session_state.company_profile.get("industry", ""))
        employee_count = st.number_input("Employee Count", min_value=1, key="employee_count",
                                         value=st.session_state.company_profile.get("employee_count", 100))
        region = st.text_input("Operating Region *", key="region",
                               value=st.session_state.company_profile.get("region", ""))
        compliance = st.text_input("Compliance Framework", key="compliance",
                                   value=st.session_state.company_profile.get("compliance", ""))
        jurisdiction = st.text_input("Jurisdiction *", key="jurisdiction",
                                     value=st.session_state.company_profile.get("jurisdiction", ""))
    with col2:
        founded_year = st.text_input("Founded Year", key="founded_year",
                                     value=st.session_state.company_profile.get("founded_year", ""))
        headquarters_location = st.text_input("Headquarters Location", key="headquarters_location",
                                              value=st.session_state.company_profile.get("headquarters_location", ""))
        ceo_name = st.text_input("CEO Name", key="ceo_name",
                                 value=st.session_state.company_profile.get("ceo_name", ""))
        cto_name = st.text_input("CTO Name", key="cto_name",
                                 value=st.session_state.company_profile.get("cto_name", ""))
        founders = st.text_area("Founders", key="founders",
                                value=st.session_state.company_profile.get("founders", ""))
        company_background = st.text_area("Company Background", key="company_background",
                                          value=st.session_state.company_profile.get("company_background", ""))

    st.session_state.company_profile.update({
        "company_name": company_name,
        "industry": industry,
        "employee_count": employee_count,
        "region": region,
        "compliance": compliance,
        "jurisdiction": jurisdiction,
        "founded_year": founded_year,
        "headquarters_location": headquarters_location,
        "ceo_name": ceo_name,
        "cto_name": cto_name,
        "founders": founders,
        "company_background": company_background
    })
    st.session_state.formatted_company_name = company_name.title() if company_name else ""


def render_document_step(step_idx, group, doc_name):
    """
    Render dynamic form fields for document generation.

    Args:
        step_idx (int): Step index in workflow
        group (dict): Field group configuration
        doc_name (str): Document name

    Returns:
        tuple:
            - user_inputs (dict): Collected field values
            - validation_errors (list): Missing required fields

    Features:
        - Dynamic label enhancement using AI
        - Field validation for required inputs
        - Supports multiple field types

    Notes:
        - Used in multi-step document generation pipeline
    """
    with st.container(border=True):
        col1, col2 = st.columns([1, 11])
        with col1:
            st.markdown(f"# {group.get('icon', '📄')}")
        with col2:
            st.subheader(group['group_name'])
            st.caption(group.get('description', ''))

    fields = group["fields"]
    user_inputs = {}
    validation_errors = []

    for idx, field in enumerate(fields):
        key = field["key"]
        raw_label = field["label"]

        cache_key = f"enhanced_{doc_name}_{raw_label}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = enhance_label(raw_label, doc_name)

        label = st.session_state[cache_key]
        if field.get("required"):
            label = f"{label} *"

        value = render_field(label, field, f"step_{step_idx}_{key}")
        user_inputs[key] = value

        if field.get("required") and not value:
            validation_errors.append(f"{field['label']} is required.")

        st.divider()

    return user_inputs, validation_errors


# -------------------- DRAFT REVIEW RENDERING FUNCTION --------------------

def render_draft_section_blocks(blocks, section_name, draft_id, prefix):
    """Render block content for a section and return accumulated paragraph text."""
    paragraph_text = ""
    for block in blocks:
        if isinstance(block, dict):
            if block.get("type") == "paragraph":
                paragraph_text += block.get("content", "") + "\n\n"
            elif block.get("type") in ["bullet", "bulleted_list_item"]:
                paragraph_text += f"- {block.get('content')}\n"
            elif block.get("type") == "table":
                df = pd.DataFrame(block.get("rows", []), columns=block.get("headers", []))
                st.table(df)
            elif block.get("type") == "diagram":
                diagram_url = block.get("diagram_url")
                image_path = block.get("render_path")
                if diagram_url:
                    full_url = diagram_url if diagram_url.startswith(('http://', 'https://')) \
                        else f"{API_BASE_URL}{diagram_url}"
                    col_l, col_m, col_r = st.columns([1, 3, 1])
                    with col_m:
                        st.image(full_url, width=600)
                elif image_path and os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        st.image(f.read(), width=600)
                else:
                    st.warning("Diagram not available")
    return paragraph_text


def render_draft_review(draft_detail, prefix=""):
    """
    Render draft review and approval interface.

    Args:
        draft_detail (dict): Draft data including sections
        prefix (str): UI key prefix to avoid conflicts

    Features:
        - Section-wise preview
        - Approve / Edit / Regenerate options
        - Progress tracking (approved vs pending)
        - Export to DOCX
        - Publish to Notion

    Behavior:
        - Uses API calls for section updates
        - Updates cache after modifications

    Notes:
        - All sections must be approved before export
    """
    st.divider()
    st.subheader("Section Review & Approval")

    total_sections = len(draft_detail["sections"])
    approved_sections = sum(1 for s in draft_detail["sections"] if s.get("status") == "approved")
    progress_ratio = approved_sections / total_sections if total_sections else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sections", total_sections)
    with col2:
        st.metric("Approved", approved_sections)
    with col3:
        st.metric("Pending", total_sections - approved_sections)

    st.progress(progress_ratio, text=f"{approved_sections} of {total_sections} sections confirmed")
    st.divider()

    all_approved = True
    for section in draft_detail["sections"]:
        section_name = section["section_name"]
        section_status = section.get("status", "draft")
        blocks = section.get("blocks", [])

        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = []
        if not isinstance(blocks, list):
            blocks = []

        with st.container(border=True):
            col1, col2 = st.columns([10, 2])
            with col1:
                st.markdown(f"## {section_name}")
            with col2:
                if section_status == "approved":
                    st.success("✅ Approved")
                else:
                    st.warning("📝 Draft")
                    all_approved = False

            paragraph_text = render_draft_section_blocks(blocks, section_name, draft_detail['id'], prefix)

            st.markdown("##### Preview")
            if paragraph_text.strip():
                with st.container(border=True):
                    st.markdown(paragraph_text)

            action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
            edit_key = f"{prefix}_edit_mode_{draft_detail['id']}_{section_name}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False
            is_editing = st.session_state[edit_key]

            with action_col1:
                if section_status != "approved":
                    if st.button("✏ Edit",
                                 key=f"{prefix}_toggle_edit_{draft_detail['id']}_{section_name}"):
                        st.session_state[edit_key] = True
                        st.rerun()

            with action_col2:
                if section_status != "approved":
                    if st.button("✓ Confirm",
                                 key=f"{prefix}_approve_{draft_detail['id']}_{section_name}"):
                        with st.spinner("Approving..."):
                            requests.post(
                                f"{API_BASE_URL}/documents/approve-section",
                                params={"draft_id": draft_detail['id'], "section_name": section_name}
                            )
                        invalidate_draft_cache(draft_detail['id'])
                        st.success("Section Locked")
                        st.rerun()

            structured_sections = [
                "review & revision history",
                "acknowledgement",
                "acknowledgement and acceptance",
                "form", "title", "signature"
            ]
            if section_status != "approved" and section_name.lower() not in structured_sections:
                with action_col3:
                    feedback = st.text_input(
                        "Improvement Note",
                        key=f"{prefix}_regen_input_{draft_detail['id']}_{section_name}"
                    )
                    if st.button("🔄 Regenerate",
                                 key=f"{prefix}_regen_button_{draft_detail['id']}_{section_name}"):
                        with st.spinner("Regenerating section..."):
                            regen_response = requests.post(
                                f"{API_BASE_URL}/documents/regenerate-section",
                                params={
                                    "draft_id": draft_detail['id'],
                                    "section_name": section_name,
                                    "improvement_note": feedback
                                }
                            )
                        if regen_response.status_code == 200:
                            invalidate_draft_cache(draft_detail['id'])
                            st.success("Section Regenerated")
                            st.rerun()
                        else:
                            st.error(regen_response.text)

            if is_editing and section_status != "approved":
                edited_text = st.text_area(
                    "Edit Section Content",
                    value=paragraph_text.strip(),
                    height=200,
                    key=f"{prefix}_edit_content_{draft_detail['id']}_{section_name}"
                )
                save_col1, save_col2 = st.columns([1, 3])
                with save_col1:
                    if st.button("Save Changes",
                                 key=f"{prefix}_save_edit_{draft_detail['id']}_{section_name}"):
                        with st.spinner("Saving..."):
                            save_response = requests.post(
                                f"{API_BASE_URL}/documents/save-section-edit",
                                json={
                                    "draft_id": draft_detail['id'],
                                    "section_name": section_name,
                                    "updated_text": edited_text
                                }
                            )
                        if save_response.status_code == 200:
                            invalidate_draft_cache(draft_detail['id'])
                            st.success("Changes Saved")
                            st.session_state[edit_key] = False
                            text_key = f"{prefix}_edit_content_{draft_detail['id']}_{section_name}"
                            if text_key in st.session_state:
                                del st.session_state[text_key]
                            st.rerun()
                        else:
                            st.error(save_response.text)

    # ----- Export buttons -----
    st.subheader("Final Document Export")
    col1, col2, col3 = st.columns([1, 1, 3])
    if all_approved:
        with col1:
            docx_url = f"{API_BASE_URL}/documents/export/{draft_detail['id']}/docx"
            response = requests.get(docx_url)
            if response.status_code == 200:
                st.download_button(
                    "📥 Download DOCX",
                    data=response.content,
                    file_name="document.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key=f"{prefix}_download_{draft_detail['id']}"
                )
            else:
                st.error(f"❌ Download failed: {response.text}")
    else:
        st.info("All sections must be approved before export.")

    # ----- Full Document Preview -----
    if all_approved:
        st.divider()
        st.subheader("Full Document Preview")
        expand_all = st.checkbox("Expand all sections", value=False,
                                 key=f"{prefix}_expand_all_{draft_detail['id']}")
        for section in draft_detail["sections"]:
            section_name = section["section_name"]
            with st.expander(f"📄 {section_name}", expanded=expand_all):
                blocks = section.get("blocks", [])
                if isinstance(blocks, str):
                    try:
                        blocks = json.loads(blocks)
                    except:
                        blocks = []
                if not isinstance(blocks, list):
                    st.markdown("Invalid section format")
                    continue
                for block in blocks:
                    if isinstance(block, dict):
                        if block.get("type") == "paragraph":
                            st.markdown(block.get("content", ""))
                        elif block.get("type") in ["bullet", "bulleted_list_item"]:
                            st.markdown(f"- {block.get('content')}")
                        elif block.get("type") == "table":
                            if section_name.lower() in ["acknowledgement", "acknowledgement and acceptance"]:
                                for row in block.get("rows", []):
                                    label = row[0]
                                    st.markdown(f"**{label}:** ____________________________")
                            else:
                                df = pd.DataFrame(block.get("rows", []), columns=block.get("headers", []))
                                st.table(df)
                        elif block.get("type") == "diagram":
                            diagram_url = block.get("diagram_url")
                            image_path = block.get("render_path")
                            if diagram_url:
                                full_url = diagram_url if diagram_url.startswith(('http://', 'https://')) \
                                    else f"{API_BASE_URL}{diagram_url}"
                                st.image(full_url, width=600)
                            elif image_path and os.path.exists(image_path):
                                with open(image_path, "rb") as f:
                                    st.image(f.read(), width=600)
                            else:
                                st.warning("Diagram not available")
    else:
        st.divider()
        st.info("Full document preview will be available after all sections are approved.")

    if all_approved:
        st.divider()
        st.subheader("Publish Document")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Publish to Notion", use_container_width=True,
                         key=f"{prefix}_publish_{draft_detail['id']}"):
                with st.spinner("Publishing document to Notion..."):
                    publish_response = requests.post(
                        f"{API_BASE_URL}/documents/publish-notion/{draft_detail['id']}"
                    )
                if publish_response.status_code == 200:
                    st.success("Document successfully published to Notion 🎉")
                else:
                    st.error("Failed to publish document to Notion")


# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.title("⚡ DocForge Hub")
    st.caption("AI-Powered Document Generation")
    st.divider()

    st.subheader("📍 Document")
    departments = [
        "HR", "IT Operations", "Legal", "Marketing", "Finance & Accounting",
        "Engineering", "Quality Assurance", "Security & Compliance",
        "Customer Success", "Product Management"
    ]
    department = st.selectbox("Department", departments, key="sidebar_department",
                              label_visibility="collapsed")

    # Cache documents meta per department to avoid re-fetching on every rerun
    if department not in st.session_state.documents_meta_cache:
        try:
            response = requests.get(f"{API_BASE_URL}/documents/list", params={"department": department})
            st.session_state.documents_meta_cache[department] = \
                response.json() if response.status_code == 200 else []
        except:
            st.session_state.documents_meta_cache[department] = []
            st.warning("⚠️ Backend connection failed – using cached data (if any)")

    documents_meta = st.session_state.documents_meta_cache.get(department, [])

    document_types = sorted(set(doc["internal_type"] for doc in documents_meta))
    selected_type = st.selectbox("Document Type", ["ALL"] + document_types, key="sidebar_doc_type",
                                 label_visibility="collapsed")

    filtered_docs = documents_meta if selected_type == "ALL" else \
        [doc for doc in documents_meta if doc["internal_type"] == selected_type]

    document_filename = st.selectbox(
        "Document Template",
        [doc["document_name"] for doc in filtered_docs],
        key="sidebar_document",
        label_visibility="collapsed"
    ) if filtered_docs else None

    if document_filename:
        st.info(f"Selected: {document_filename}")

    st.caption("💡 Default is Latest (recommended). Select a specific version only if needed.")


# -------------------- MAIN CONTENT --------------------
st.header("⚡ DocForge Hub")
st.caption("Intelligent document generation platform powered by AI")

tabs = st.tabs(["✨ Generate Draft", "📚 Draft Library", "🔎 CiteRag Lab", "🤖 StateCase Assistant", "🎫 My Tickets"])
tab_gen       = tabs[0]
tab_lib       = tabs[1]
tab_rag       = tabs[2]
tab_statecase = tabs[3]
tab_tickets   = tabs[4]


# ==================== GENERATE DRAFT TAB ====================
with tab_gen:
    if document_filename:
        # Reset wizard when document changes
        if st.session_state.get("current_doc") != document_filename:
            st.session_state.current_doc = document_filename
            st.session_state.current_step = 0
            st.session_state.form_data = {}
            st.session_state.pending_questions = []
            st.session_state.question_answers = {}
            st.session_state.questions_generated = False
            st.session_state.questions_initialized = False
            for k in list(st.session_state.keys()):
                if k.startswith("aiq_"):
                    del st.session_state[k]

        # Cache doc config per document filename
        doc_config_key = f"doc_config_{document_filename}"
        if doc_config_key not in st.session_state:
            try:
                with st.spinner("Loading document configuration..."):
                    response = requests.post(
                        f"{API_BASE_URL}/documents/preview",
                        json={"department": department, "document_filename": document_filename}
                    )
                if response.status_code == 200:
                    st.session_state[doc_config_key] = response.json()
                else:
                    st.error("Failed to load document configuration.")
                    st.stop()
            except Exception as e:
                st.error(f"❌ Backend connection error: {e}")
                st.stop()

        doc_config = st.session_state[doc_config_key]
        merged_groups = merge_input_groups(doc_config)

        base_groups = [g for g in merged_groups if g.get("source") == "base"]
        doc_groups = [g for g in merged_groups if g.get("source") != "base"]
        all_doc_groups = base_groups + doc_groups

        doc_step_count = 2
        total_steps = 1 + doc_step_count
        current_step = st.session_state.current_step

        progress_text = f"Step {current_step + 1} of {total_steps}"
        st.progress((current_step + 1) / total_steps, text=progress_text)

        step_names = ["🏢 Company"] + [f"📄 Section {i + 1}" for i in range(doc_step_count)]
        cols = st.columns(total_steps)
        for i, col in enumerate(cols):
            with col:
                if i == current_step:
                    st.info(f"**{step_names[i]}**")
                elif i < current_step:
                    st.success(f"✅ {step_names[i]}")
                else:
                    st.write(f"⏳ {step_names[i]}")

        st.divider()

        validation_errors = []

        if current_step == 0:
            render_company_step()

        elif current_step == 1:
            for idx, group in enumerate(all_doc_groups):
                if 'icon' not in group:
                    group['icon'] = "📄"
                if 'description' not in group:
                    group['description'] = f"{doc_config['document_name']} details"

                user_inputs, errs = render_document_step(idx, group, doc_config['document_name'])
                validation_errors.extend(errs)
                for key, value in user_inputs.items():
                    st.session_state.form_data[f"{idx}_{key}"] = value

        elif current_step == 2:
            st.subheader("🤖 AI Generated Questions")
            st.info("Answer AI-generated questions based on your inputs.")

            # Only call the API once; guard with questions_generated flag
            if not st.session_state.questions_generated:
                all_inputs = {}
                for step in range(len(all_doc_groups)):
                    for field in all_doc_groups[step]["fields"]:
                        key = f"step_{step}_{field['key']}"
                        if key in st.session_state:
                            all_inputs[field['key']] = st.session_state[key]

                safe_inputs = {
                    k: v.isoformat() if hasattr(v, "isoformat") else v
                    for k, v in all_inputs.items()
                }

                with st.spinner("Generating AI questions..."):
                    try:
                        questions_response = requests.post(
                            f"{API_BASE_URL}/documents/generate-questions",
                            json={
                                "department": department.lower(),
                                "document_filename": document_filename,
                                "company_profile": st.session_state.company_profile,
                                "document_inputs": safe_inputs
                            }
                        )
                        if questions_response.status_code == 200:
                            st.session_state.pending_questions = \
                                questions_response.json().get("questions", [])
                            st.session_state.questions_generated = True
                    except Exception as e:
                        st.error(f"❌ Failed to generate questions: {e}")

            for i, q in enumerate(st.session_state.pending_questions):
                key = q["key"]
                question_text = q["question"]
                unique_key = f"aiq_{i}_{key}"
                if q.get("type") == "textarea":
                    st.text_area(question_text, key=unique_key)
                else:
                    st.text_input(question_text, key=unique_key)

        st.divider()
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if current_step > 0:
                if st.button("◀ Previous", use_container_width=True):
                    st.session_state.current_step -= 1
                    st.rerun()

        with col5:
            if current_step < total_steps - 1:
                if st.button("Next ▶", use_container_width=True, type="primary"):
                    if 0 < current_step <= doc_step_count and validation_errors:
                        for err in validation_errors:
                            st.error(f"❌ {err}")
                    else:
                        st.session_state.current_step += 1
                        st.rerun()
            else:
                # FIX: All generation logic is INSIDE the button block
                if st.button("🚀 Generate Draft", use_container_width=True, type="primary"):
                    company = st.session_state.company_profile
                    missing = []
                    if not company["company_name"]:
                        missing.append("Company Name")
                    if not company["industry"]:
                        missing.append("Industry")
                    if not company["region"]:
                        missing.append("Region")
                    if not company["jurisdiction"]:
                        missing.append("Jurisdiction")
                    if missing:
                        st.error(f"❌ Please complete all mandatory Company Profile fields: "
                                 f"{', '.join(missing)}.")
                        st.stop()

                    question_answers = {}
                    unanswered = []
                    for i, q in enumerate(st.session_state.pending_questions):
                        key = q["key"]
                        unique_key = f"aiq_{i}_{key}"
                        value = st.session_state.get(unique_key, "")
                        question_answers[key] = value
                        if not value:
                            unanswered.append(q["question"])

                    if unanswered:
                        st.error("❌ Please answer the following questions:")
                        for q in unanswered:
                            st.error(f"  - {q}")
                        st.stop()

                    all_inputs = {}
                    for step in range(len(all_doc_groups)):
                        for field in all_doc_groups[step]["fields"]:
                            key = f"step_{step}_{field['key']}"
                            if key in st.session_state:
                                all_inputs[field['key']] = st.session_state[key]

                    for key, value in list(all_inputs.items()):
                        if hasattr(value, "isoformat"):
                            all_inputs[key] = value.isoformat()

                    all_inputs.update(question_answers)

                    with st.spinner("🎨 Crafting your document..."):
                        try:
                            gen_resp = requests.post(
                                f"{API_BASE_URL}/documents/generate",
                                json={
                                    "department": department.lower(),
                                    "document_filename": document_filename,
                                    "company_profile": company,
                                    "document_inputs": all_inputs
                                }
                            )
                            result = gen_resp.json()
                            if result.get("status") == "draft_saved":
                                st.success("✅ Draft Generated Successfully!")
                                st.balloons()
                                st.session_state.selected_draft_id = result["draft_id"]
                                # Invalidate drafts library cache so it refreshes
                                st.session_state.drafts_library_cache = None
                                st.rerun()
                            elif result.get("status") == "questions_required":
                                st.error("Some information is still missing. Please review and try again.")
                            else:
                                st.error("Draft generation failed")
                        except Exception as e:
                            st.error(f"❌ Backend connection error: {e}")

    else:
        st.info("👈 Please select a document template from the sidebar to begin generating a draft.")

    # Show draft review if a draft is selected
    if st.session_state.selected_draft_id:
        draft_detail = get_draft_detail(st.session_state.selected_draft_id)
        if draft_detail:
            render_draft_review(draft_detail, prefix="gen")
        else:
            st.error("Failed to load draft.")


# ==================== DRAFT LIBRARY TAB ====================
with tab_lib:
    st.subheader("📚 Document Library")

    # Reload button to manually refresh library
    if st.button("🔄 Refresh Library", key="lib_refresh_btn"):
        st.session_state.drafts_library_cache = None

    # Cache drafts list
    if st.session_state.drafts_library_cache is None:
        try:
            response = requests.get(f"{API_BASE_URL}/documents/drafts")
            if response.status_code == 200:
                st.session_state.drafts_library_cache = response.json()
            else:
                st.session_state.drafts_library_cache = []
        except Exception as e:
            st.session_state.drafts_library_cache = []
            st.error(f"❌ Failed to load drafts: {e}")

    drafts = st.session_state.drafts_library_cache or []

    if drafts:
        total_drafts = len(drafts)
        published = sum(1 for d in drafts if d.get('status') == 'published')
        draft_count = total_drafts - published

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Drafts", total_drafts)
        with col2:
            st.metric("Published", published)
        with col3:
            st.metric("In Progress", draft_count)

        st.divider()
        search = st.text_input("🔍 Search documents", placeholder="Type to search...", key="lib_search")

        unique_docs = {}
        for draft in drafts:
            name = draft["document_name"]
            if name not in unique_docs or draft["version"] > unique_docs[name]["version"]:
                unique_docs[name] = draft
        filtered_drafts = list(unique_docs.values())

        if search:
            filtered_drafts = [d for d in filtered_drafts
                               if search.lower() in d['document_name'].lower()]

        if filtered_drafts:
            for i in range(0, len(filtered_drafts), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(filtered_drafts):
                        draft = filtered_drafts[i + j]
                        with cols[j]:
                            with st.container(border=True):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"**{draft['document_name'][:25]}"
                                             f"{'...' if len(draft['document_name']) > 25 else ''}**")
                                    st.caption(f"v{draft.get('version', '1.0')}")
                                with col2:
                                    if draft['status'] == 'published':
                                        st.success("✅ Published")
                                    else:
                                        st.warning("📝 Draft")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("👁️ View", key=f"v_{draft['id']}",
                                                 use_container_width=True):
                                        st.session_state.selected_draft_id = draft["id"]
                                        st.rerun()
                                with col2:
                                    if st.button("🗑️ Delete", key=f"d_{draft['id']}",
                                                 use_container_width=True):
                                        with st.spinner("Deleting..."):
                                            response = requests.delete(
                                                f"{API_BASE_URL}/documents/draft/{draft['id']}"
                                            )
                                            if response.status_code == 200:
                                                st.success("Deleted successfully")
                                                # Invalidate caches
                                                invalidate_draft_cache(draft['id'])
                                                st.session_state.drafts_library_cache = None
                                                if st.session_state.selected_draft_id == draft["id"]:
                                                    st.session_state.selected_draft_id = None
                                                st.rerun()
                                            else:
                                                st.error("Delete failed")
        else:
            st.info("No matching documents found")
    else:
        st.info("No documents found in library")

    if st.session_state.selected_draft_id:
        draft_detail = get_draft_detail(st.session_state.selected_draft_id)
        if draft_detail:
            render_draft_review(draft_detail, prefix="lib")
        else:
            st.error("Failed to load draft.")


# ==================== CITERAG LAB TAB ====================
with tab_rag:
    st.subheader("🔎 CiteRAG Knowledge Search")

    with st.container(border=True):
        st.markdown("### Filters")
        col1, col2, col3 = st.columns(3)

        with col1:
            doc_type = st.selectbox(
                "Document Type",
                ["All", "Policy", "Runbook", "Handbook", "Template", "SOP", "FORM"]
            )
        with col2:
            industry = st.radio("Industry", ["All", "SaaS"], horizontal=True)
        with col3:
            from backend.rag.notion_reader import get_all_versions
            # Cache versions list
            if "rag_versions" not in st.session_state:
                try:
                    st.session_state.rag_versions = get_all_versions()
                except:
                    st.session_state.rag_versions = []
            versions = st.session_state.rag_versions
            version_options = ["Latest"] + [str(v) for v in versions]
            selected_version = st.selectbox("Version", version_options, key="version_filter")

    doc_type_filter = None if doc_type == "All" else doc_type
    industry_filter = None if industry == "All" else industry
    version_filter = "latest" if selected_version == "Latest" else int(selected_version)

    tool_tabs = st.tabs(["🔎 Search", "📘 Compare", "📝 Summarize"])

    with tool_tabs[0]:
        st.caption("Ask questions about company documents stored in Notion")
        question = st.text_input("Ask a question about company policies or procedures",
                                 key="rag_question")
        ask_clicked = st.button("Ask", use_container_width=False)

        # Cache last RAG result so it persists across reruns
        if "rag_last_result" not in st.session_state:
            st.session_state.rag_last_result = None
        if "rag_last_question" not in st.session_state:
            st.session_state.rag_last_question = ""

        if ask_clicked:
            if not question:
                st.warning("Please enter a question")
            else:
                with st.spinner("Searching knowledge base..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/documents/rag-query",
                            json={
                                "question": question,
                                "doc_type": doc_type_filter,
                                "industry": industry_filter,
                                "version": version_filter
                            }
                        )
                        if response.status_code != 200:
                            st.error(f"❌ API Error: {response.text}")
                        else:
                            try:
                                st.session_state.rag_last_result = response.json()
                                st.session_state.rag_last_question = question
                            except Exception:
                                st.error("❌ Invalid response from backend")
                                st.text(response.text)
                    except Exception as e:
                        st.error(f"Query failed: {e}")

        # Always render the last result (persists across reruns)
        if st.session_state.rag_last_result:
            result = st.session_state.rag_last_result
            st.markdown("### 🔍 Refined Query")
            st.write(result.get("refined_query", st.session_state.rag_last_question))
            st.markdown("### 📌 Answer")
            st.write(result.get("answer", "No answer found"))
            st.markdown("### 📊 Confidence")
            confidence_score = result.get("confidence_score", 0)
            st.markdown(f"**Confidence Score:** {confidence_score}%")
            st.progress(confidence_score / 100)
            st.markdown("### 📚 Sources")
            for source in result.get("sources", []):
                st.write(f"• {source}")
            st.markdown("### 🔎 Retrieved Context")
            for chunk in result.get("chunks", []):
                with st.expander(f"{chunk['doc_title']} → {chunk['section']}"):
                    st.write(chunk["text"])
                    st.caption(f"Score: {chunk.get('score', 0):.3f}")

    with tool_tabs[1]:
        st.subheader("Compare Documents")
        # Cache available docs for compare tab
        if "rag_available_docs" not in st.session_state:
            try:
                from backend.rag.notion_reader import get_all_document_titles
                st.session_state.rag_available_docs = get_all_document_titles()
            except Exception as e:
                st.session_state.rag_available_docs = []
                st.warning(f"⚠️ Unable to fetch documents from Notion: {e}")

        available_docs = st.session_state.rag_available_docs
        st.caption(f"📚 {len(available_docs)} documents available")

        col1, col2 = st.columns(2)
        with col1:
            doc_a = st.selectbox("Document A", available_docs, key="compare_doc_a_dropdown")
        with col2:
            doc_b = st.selectbox("Document B", available_docs, key="compare_doc_b_dropdown")

        topic = st.text_input("Comparison Topic", key="compare_topic")

        # Cache compare result
        if "rag_compare_result" not in st.session_state:
            st.session_state.rag_compare_result = None

        if st.button("Compare", use_container_width=False):
            if not doc_a or not doc_b:
                st.warning("Please select both documents")
            else:
                with st.spinner("Comparing documents..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/documents/rag-compare",
                            json={"doc_a": doc_a, "doc_b": doc_b, "topic": topic,
                                  "version": version_filter}
                        )
                        if response.status_code != 200:
                            st.error(f"❌ API Error: {response.text}")
                        else:
                            st.session_state.rag_compare_result = {
                                "result": response.json(),
                                "doc_a": doc_a,
                                "doc_b": doc_b,
                                "topic": topic
                            }
                    except Exception as e:
                        st.error(f"Comparison failed: {e}")

        if st.session_state.rag_compare_result:
            cached = st.session_state.rag_compare_result
            result = cached["result"]
            st.markdown("### 📌 Comparison")
            st.markdown(f"**Document A:** {cached['doc_a']}")
            st.markdown(f"**Document B:** {cached['doc_b']}")
            st.markdown(f"**Comparison Topic:** {cached['topic'] if cached['topic'] else '-'}")
            st.divider()
            st.write(result.get("answer", ""))

    with tool_tabs[2]:
        st.subheader("Summarize Document")
        if "rag_available_docs" not in st.session_state:
            try:
                from backend.rag.notion_reader import get_all_document_titles
                st.session_state.rag_available_docs = get_all_document_titles()
            except:
                st.session_state.rag_available_docs = []

        available_docs = st.session_state.rag_available_docs
        summary_query = st.selectbox("Select document to summarize", available_docs,
                                     key="summary_query")

        # Cache summary result
        if "rag_summary_result" not in st.session_state:
            st.session_state.rag_summary_result = None

        if st.button("Summarize", use_container_width=False):
            if not summary_query:
                st.warning("Please select a document")
            else:
                with st.spinner("Generating summary..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/documents/rag-summarize",
                            json={
                                "query": summary_query,
                                "doc_type": doc_type_filter,
                                "industry": industry_filter,
                                "version": version_filter
                            }
                        )
                        if response.status_code != 200:
                            st.error(f"❌ API Error: {response.text}")
                        else:
                            st.session_state.rag_summary_result = {
                                "result": response.json(),
                                "doc": summary_query
                            }
                    except Exception as e:
                        st.error(f"Summarization failed: {e}")

        if st.session_state.rag_summary_result:
            cached = st.session_state.rag_summary_result
            result = cached["result"]
            st.markdown(f"### 📝 Summary: {cached['doc']}")
            st.divider()
            summary_text = result.get("summary", "No summary available")
            if summary_text:
                st.markdown(summary_text)
            else:
                st.warning("No summary could be generated for this document.")

    st.divider()
    st.subheader("📊 RAG Evaluation")

    # Cache eval result
    if "rag_eval_result" not in st.session_state:
        st.session_state.rag_eval_result = None

    if st.button("Run Evaluation", use_container_width=False):
        with st.spinner("Running evaluation... ⏳"):
            response = requests.post(f"{API_BASE_URL}/documents/rag-evaluate")
        if response.status_code == 200:
            st.session_state.rag_eval_result = response.json()
        else:
            st.error("Evaluation failed")
            st.write(response.text)

    if st.session_state.rag_eval_result:
        result = st.session_state.rag_eval_result
        st.subheader("📋 Detailed Results")
        st.dataframe(result["data"])
        st.subheader("📈 Average Scores")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Faithfulness", f"{result['avg_faithfulness']:.3f}")
        col2.metric("Relevancy", f"{result['avg_relevancy']:.3f}")
        col3.metric("Context Precision", f"{result['avg_context_precision']:.3f}")
        col4.metric("Context Recall", f"{result['avg_context_recall']:.3f}")


# ==================== STATECASE ASSISTANT TAB ====================
with tab_statecase:

    # session_id, chat_history, sc_tickets initialized at top level

    # ── Helper: build conversation context for backend ────────────
    def build_chat_context(history, max_turns=6):
        """
        Build conversation context string for backend.

        Args:
            history (list): Chat history [(role, message), ...]
            max_turns (int): Number of recent turns to include

        Returns:
            str: Formatted conversation string

        Example:
            User: What is remote policy?
            Assistant: It allows employees...

        Purpose:
            - Provides context to backend for better LLM responses
            - Enables follow-up question understanding
        """
        lines  = []
        recent = history[-(max_turns * 2):]
        for role, msg in recent:
            if role == "user":
                lines.append(f"User: {msg}")
            elif role == "assistant" and isinstance(msg, dict):
                lines.append(f"Assistant: {msg.get('answer', '')}")
        return "\n".join(lines)

    # ── Helper: render one assistant message ──────────────────────
    def render_assistant_message(msg):
        """
        Render assistant response in chat UI.

        Args:
            msg (dict):
                - answer (str): Response text
                - confidence (float): Confidence score
                - sources (list): Source documents

        Features:
            - Displays formatted answer
            - Shows sources in expandable section
            - Displays confidence score with color indicator
            - Handles ticket-related responses
            - Handles out-of-domain messages

        Notes:
            - Enhances UX with visual feedback
        """
        raw_answer = msg.get("answer", "")
        confidence = msg.get("confidence", 0)
        sources    = msg.get("sources", [])

        answer_text    = raw_answer
        inline_sources = []
        if "\n---\n📚 **Sources:**\n" in raw_answer:
            parts = raw_answer.split("\n---\n📚 **Sources:**\n", 1)
            answer_text = parts[0].strip()
            for line in parts[1].splitlines():
                line = line.strip().lstrip("•").strip()
                if line:
                    inline_sources.append(line)

        all_sources = list(dict.fromkeys(inline_sources + [
            (s if isinstance(s, str) else s.get("title", str(s))) for s in sources
        ]))

        st.markdown(answer_text)

        if all_sources:
            with st.expander("📚 Sources", expanded=True):
                for src in all_sources:
                    st.markdown(f"• {src}")

        ticket_keywords    = ["created in notion", "already exists in notion",
                              "ticket has been", "support ticket"]
        is_ticket_response = any(kw in answer_text.lower() for kw in ticket_keywords)
        is_out_of_domain   = "outside the scope" in answer_text.lower()

        if confidence > 0 and not is_ticket_response and not is_out_of_domain:
            conf_icon = "🟢" if confidence > 70 else "🟡" if confidence > 40 else "🔴"
            st.progress(confidence / 100, text=f"{conf_icon} Confidence: {confidence}%")

        if is_out_of_domain:
            st.info("🌐 This question is outside our internal knowledge base.", icon="ℹ️")
        if "created in notion" in answer_text.lower() and "already exists" not in answer_text.lower():
            st.warning("📌 A new ticket was created in Notion. Check the My Tickets tab.", icon="🎫")
        if "already exists in notion" in answer_text.lower():
            st.info("🔁 This ticket already exists in Notion — no duplicate created.", icon="📋")

    # ── Filters ───────────────────────────────────────────────────
    with st.expander("⚙️ Filters", expanded=False):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            sc_doc_type = st.selectbox("Doc type",
                ["All","Policy","Runbook","Handbook","SOP","FORM"], key="sc_doc_type")
        with f_col2:
            sc_industry = st.radio("Industry", ["All","SaaS"], horizontal=True, key="sc_industry")
        with f_col3:
            sc_version = st.selectbox("Version", ["Latest"], key="sc_version")

    sc_doc_type_filter = None if sc_doc_type == "All" else sc_doc_type
    sc_industry_filter = None if sc_industry == "All" else sc_industry
    sc_version_filter  = "latest"

    # ── Title row ─────────────────────────────────────────────────
    title_col, clear_col = st.columns([8, 1])
    with title_col:
        st.subheader("🤖 StateCase Assistant")
        st.caption("Conversational AI with memory + ticketing")
    with clear_col:
        st.write("")
        if st.button("🗑 Clear", key="sc_clear_chat_btn", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # ── STEP 1: Render full chat history above the input ──────────
    if not st.session_state.chat_history:
        st.info("👋 Ask me anything about company policies, procedures, or raise a support ticket.",
                icon="🤖")
    else:
        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                if role == "user":
                    st.markdown(msg)
                else:
                    render_assistant_message(msg)

        last_role, last_msg = st.session_state.chat_history[-1]
        if last_role == "assistant" and isinstance(last_msg, dict):
            txt = last_msg.get("answer", "").lower()
            if any(p in txt for p in ("more details", "could you clarify", "could you provide")):
                st.caption("ℹ️ Assistant needs more context — type your follow-up below.")

    # ── STEP 2: Input box — declared LAST so it sits at the bottom ─
    user_input = st.chat_input(
        placeholder="Ask anything about policies, procedures, or raise a ticket...",
        key="sc_chat_input"
    )

    # ── STEP 3: Handle submission — show spinner inline, then rerun ─
    if user_input:
        # Save user message
        st.session_state.chat_history.append(("user", user_input))

        # Render user bubble immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build context from everything before the current message
        conversation_context = build_chat_context(st.session_state.chat_history[:-1])

        # Render assistant bubble with spinner while waiting
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/documents/statecase-chat",
                        json={
                            "session_id":           st.session_state.session_id,
                            "question":             user_input,
                            "conversation_context": conversation_context,
                            "doc_type":             sc_doc_type_filter,
                            "industry":             sc_industry_filter,
                            "version":              sc_version_filter
                        }
                    )
                    result = resp.json()
                    assistant_msg = {
                        "answer":     result.get("answer", ""),
                        "confidence": result.get("confidence", 0),
                        "sources":    result.get("sources", [])
                    }
                except Exception as e:
                    assistant_msg = {"answer": f"❌ Error: {e}", "confidence": 0, "sources": []}

            # Render response inline (spinner replaced by actual content)
            render_assistant_message(assistant_msg)

        # Save assistant response and rerun to persist in history
        st.session_state.chat_history.append(("assistant", assistant_msg))
        st.rerun()


# ==================== MY TICKETS TAB ====================
with tab_tickets:

    if "sc_tickets" not in st.session_state:
        st.session_state.sc_tickets = []

    st.subheader("🎫 My Tickets")

    # ── Header row: refresh + clear buttons ───────────────────────
    hdr1, hdr2, hdr3 = st.columns([4, 1, 1])
    with hdr1:
        st.caption("All support tickets raised via StateCase Assistant")
    with hdr2:
        if st.button("↻ Refresh", use_container_width=True, key="tab_refresh_tickets"):
            try:
                url = (f"https://api.notion.com/v1/databases/"
                       f"{os.getenv('NOTION_TICKET_DATABASE_ID')}/query")
                headers_notion = {
                    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
                    "Notion-Version": "2022-06-28"
                }
                resp = requests.post(url, headers=headers_notion)
                if resp.status_code == 200:
                    st.session_state.sc_tickets = resp.json().get("results", [])
                    st.success(f"Loaded {len(st.session_state.sc_tickets)} tickets")
                else:
                    st.error("Failed to fetch tickets")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    if not st.session_state.sc_tickets:
        st.info("No tickets yet. Click **↻ Refresh** to load tickets from Notion.")
    else:
        tickets_data = []
        for item in st.session_state.sc_tickets:
            props = item["properties"]

            title = "No title"
            if props.get("Title") and props["Title"].get("title"):
                td = props["Title"]["title"]
                if td:
                    title = td[0]["plain_text"]
            if title == "No title":
                continue

            status = "N/A"
            if props.get("Status") and props["Status"].get("select"):
                status = props["Status"]["select"]["name"]

            priority = "N/A"
            if props.get("Priority") and props["Priority"].get("select"):
                priority = props["Priority"]["select"]["name"]

            category = "N/A"
            if props.get("Category") and props["Category"].get("select"):
                category = props["Category"]["select"]["name"]

            owner = ""
            if props.get("Owner") and props["Owner"].get("rich_text"):
                ot = props["Owner"]["rich_text"]
                if ot:
                    owner = ot[0]["plain_text"]

            tickets_data.append({
                "Title": title,
                "Status": status,
                "Priority": priority,
                "Category": category,
                "Owner": owner,
            })

        if tickets_data:
            total       = len(tickets_data)
            open_       = sum(1 for t in tickets_data if t["Status"] == "Open")
            in_progress = sum(1 for t in tickets_data if t["Status"] == "In Progress")
            closed      = sum(1 for t in tickets_data if t["Status"] == "Closed")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total",       total)
            m2.metric("Open",        open_)
            m3.metric("In Progress", in_progress)
            m4.metric("Closed",      closed)
            st.divider()

            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                f_status = st.selectbox("Filter by Status",
                    ["All", "Open", "In Progress", "Closed"], key="ticket_filter_status")
            with fc2:
                f_priority = st.selectbox("Filter by Priority",
                    ["All", "High", "Medium", "Low"], key="ticket_filter_priority")
            with fc3:
                f_search = st.text_input("Search tickets",
                    placeholder="Type to search...", key="ticket_search")

            filtered = tickets_data
            if f_status   != "All": filtered = [t for t in filtered if t["Status"]   == f_status]
            if f_priority != "All": filtered = [t for t in filtered if t["Priority"] == f_priority]
            if f_search:            filtered = [t for t in filtered if f_search.lower() in t["Title"].lower()]

            st.caption(f"Showing {len(filtered)} of {total} tickets")
            st.divider()

            status_colors = {
                "Open":        ("#dbeafe", "#1e40af", "🔵"),
                "In Progress": ("#fef9c3", "#92400e", "🟡"),
                "Closed":      ("#dcfce7", "#166534", "🟢"),
                "N/A":         ("#f3f4f6", "#374151", "⚪"),
            }
            priority_colors = {
                "High":   ("#fee2e2", "#991b1b", "↑"),
                "Medium": ("#fef9c3", "#92400e", "→"),
                "Low":    ("#f0fdf4", "#166534", "↓"),
                "N/A":    ("#f3f4f6", "#374151", "—"),
            }


            for i in range(0, len(filtered), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j >= len(filtered):
                        break
                    t = filtered[i + j]
                    s_bg, s_fg, s_ico = status_colors.get(t["Status"],   ("#f3f4f6","#374151","⚪"))
                    p_bg, p_fg, p_ico = priority_colors.get(t["Priority"],("#f3f4f6","#374151","—"))
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(
                                f"**{t['Title'][:60]}{'...' if len(t['Title']) > 60 else ''}**",
                                help=t["Title"]
                            )
                            col_a, col_b, col_c, col_d = st.columns(4)
                            with col_a: st.caption(f"{s_ico} Status: {t['Status']}")
                            with col_b: st.caption(f"{p_ico} Priority: {t['Priority']}")
                            with col_c:
                                if t["Category"] != "N/A": st.caption(f"📂 {t['Category']}")
                            with col_d:
                                if t["Owner"]: st.caption(f"👤 {t['Owner']}")

# -------------------- FOOTER --------------------
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    st.caption("⚡ DocForge Hub - AI-Powered Intelligent Document Generation Platform")
    st.caption("© 2024 All rights reserved")