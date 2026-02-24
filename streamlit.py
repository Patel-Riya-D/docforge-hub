import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
from datetime import datetime, date
import json
import pandas as pd

API_BASE_URL = "http://127.0.0.1:8000"

# ---------------- UI CONFIG & ENHANCED STYLING ----------------
st.set_page_config(
    page_title="DocForge Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Elegant light theme (same as before)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp {
        background: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    .main > div {
        background: #ffffff;
        border-radius: 24px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
        border: 1px solid #eef2f6;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #eef2f6;
        box-shadow: 2px 0 20px rgba(0, 0, 0, 0.02);
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #eef2f6 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f1f5f9;
        padding: 4px;
        border-radius: 40px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 8px 20px;
        font-weight: 500;
        color: #64748b;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
        color: #0f172a;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #2563eb !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
        border: 1px solid #e2e8f0;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2563eb, #3b82f6) !important;
        border-radius: 10px;
    }
    .step-container {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin: 20px 0 30px;
        padding: 15px;
        background: #f8fafc;
        border-radius: 60px;
        border: 1px solid #eef2f6;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 5px 15px;
        border-radius: 30px;
        transition: all 0.3s ease;
    }
    .step-item.active {
        background: rgba(37, 99, 235, 0.1);
        border: 1px solid rgba(37, 99, 235, 0.3);
    }
    .step-number {
        width: 32px; height: 32px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; font-size: 0.9rem;
    }
    .step-number.active   { background: #2563eb; color: white; }
    .step-number.completed { background: #10b981; color: white; }
    .step-number.pending  { background: #e2e8f0; color: #64748b; }
    .step-text { font-size: 0.9rem; font-weight: 500; color: #64748b; }
    .step-text.active { color: #2563eb; }
    .group-card {
        background: #ffffff;
        border: 1px solid #eef2f6;
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    }
    .group-card:hover {
        border-color: #2563eb40;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.05);
    }
    .group-header {
        display: flex; align-items: center; gap: 15px;
        margin-bottom: 20px; padding-bottom: 15px;
        border-bottom: 1px solid #eef2f6;
    }
    .group-icon {
        width: 48px; height: 48px;
        background: #f1f5f9;
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        color: #2563eb; font-size: 1.6rem;
    }
    .group-title { font-size: 1.2rem; font-weight: 600; color: #0f172a; }
    .group-description { font-size: 0.85rem; color: #64748b; }
    .document-paper {
        background: #ffffff;
        padding: 60px 80px;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
        font-family: 'Inter', sans-serif;
        line-height: 1.7;
        color: #1e293b;
        max-width: 900px;
        margin: 30px auto;
        border: 1px solid #eef2f6;
    }
    .document-paper h1 {
        font-size: 2.5rem; font-weight: 700;
        color: #0f172a; margin-bottom: 25px; text-align: center;
    }
    .document-paper h2 {
        font-size: 1.6rem; font-weight: 600;
        color: #0f172a; margin-top: 30px; margin-bottom: 15px;
        border-bottom: 2px solid #eef2f6; padding-bottom: 8px;
    }
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    .stDateInput input, input[type="text"], input[type="number"], textarea {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        color: #0f172a !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus,
    input:focus, textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }
    input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        color: #0f172a !important;
    }
    [data-baseweb="popover"] li {
        background: #ffffff !important;
        color: #0f172a !important;
    }
    [data-baseweb="popover"] li:hover {
        background: #f1f5f9 !important;
    }
    .draft-card {
        background: #ffffff;
        padding: 20px; border-radius: 16px; margin-bottom: 15px;
        transition: all 0.2s ease;
        border: 1px solid #eef2f6;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }
    .draft-card:hover {
        border-color: #2563eb80;
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.1);
    }
    .draft-card strong { color: #0f172a !important; }
    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: 500;
    }
    .badge-draft {
        background: #fef3c7; color: #92400e !important;
        border: 1px solid #fbbf24;
    }
    .badge-published {
        background: #d1fae5; color: #065f46 !important;
        border: 1px solid #10b981;
    }
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 10px 25px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.3) !important;
    }
    .stAlert {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary {
        background: #f8fafc !important;
        border-radius: 12px !important;
        color: #0f172a !important;
    }
    .footer {
        text-align: center; color: #94a3b8 !important;
        padding: 30px 0 10px; font-size: 0.8rem;
    }
    .footer::before {
        content: ''; position: absolute; top: 0; left: 25%; width: 50%; height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
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

# ---------------- HELPER FUNCTIONS ----------------
def format_date(date_string):
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        return date_string

def get_status_badge(status):
    colors = {
        "draft": ("badge-draft", "📝 Draft"),
        "published": ("badge-published", "✅ Published"),
        "archived": ("badge-draft", "📦 Archived")
    }
    badge_class, text = colors.get(status.lower(), ("badge-draft", status))
    return f'<span class="status-badge {badge_class}">{text}</span>'

def render_field(label, field, key):
    field_type = field["type"]
    if field_type == "text": 
        return st.text_input(label, key=key, placeholder=f"Enter {label.lower()}...")
    elif field_type == "textarea": 
        return st.text_area(label, key=key, height=80, placeholder=f"Enter {label.lower()}...")
    elif field_type == "number": 
        return st.number_input(label, key=key, min_value=0)
    elif field_type == "boolean": 
        return st.checkbox(label, key=key)
    elif field_type == "date": 
        return st.date_input(label, key=key)
    elif field_type == "dropdown": 
        return st.selectbox(label, field.get("options", []), key=key)
    elif field_type == "multiselect": 
        return st.multiselect(label, field.get("options", []), key=key)
    else: 
        return st.text_input(label, key=key, placeholder=f"Enter {label.lower()}...")

def render_company_step():
    """Render the company profile step with a card layout"""
    st.markdown("""
        <div class="group-card">
            <div class="group-header">
                <div class="group-icon">🏢</div>
                <div>
                    <div class="group-title">Company Profile</div>
                    <div class="group-description">Mandatory: Profile details are embedded into the document.</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name *", key="company_name", value=st.session_state.company_profile.get("company_name", ""))
        industry = st.text_input("Industry *", key="industry", value=st.session_state.company_profile.get("industry", ""))
        employee_count = st.number_input("Employee Count", min_value=1, key="employee_count", value=st.session_state.company_profile.get("employee_count", 100))
        region = st.text_input("Operating Region *", key="region", value=st.session_state.company_profile.get("region", ""))
        compliance = st.text_input("Compliance Framework", key="compliance", value=st.session_state.company_profile.get("compliance", ""))
        jurisdiction = st.text_input("Jurisdiction *", key="jurisdiction", value=st.session_state.company_profile.get("jurisdiction", ""))
    with col2:
        founded_year = st.text_input("Founded Year", key="founded_year", value=st.session_state.company_profile.get("founded_year", ""))
        headquarters_location = st.text_input("Headquarters Location", key="headquarters_location", value=st.session_state.company_profile.get("headquarters_location", ""))
        ceo_name = st.text_input("CEO Name", key="ceo_name", value=st.session_state.company_profile.get("ceo_name", ""))
        cto_name = st.text_input("CTO Name", key="cto_name", value=st.session_state.company_profile.get("cto_name", ""))
        founders = st.text_area("Founders", key="founders", value=st.session_state.company_profile.get("founders", ""))
        company_background = st.text_area("Company Background", key="company_background", value=st.session_state.company_profile.get("company_background", ""))
    
    # Update session state
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

def render_document_step(step_idx, group, doc_name):
    """Render a document group step (base or doc)"""
    st.markdown(f"""
        <div class="group-card">
            <div class="group-header">
                <div class="group-icon">{group['icon']}</div>
                <div>
                    <div class="group-title">{group['group_name']}</div>
                    <div class="group-description">{group.get('description', '')}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    fields = group["fields"]
    cols = st.columns(2)
    user_inputs = {}
    validation_errors = []
    for idx, field in enumerate(fields):
        key, label = field["key"], field["label"]
        if field.get("required"): 
            label = f"{label} *"
        with cols[idx % 2]:
            value = render_field(label, field, f"step_{step_idx}_{key}")
            user_inputs[key] = value
            if field.get("required") and not value:
                validation_errors.append(f"{field['label']} is required.")
    return user_inputs, validation_errors

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <div style='font-size: 2.5rem;'>⚡</div>
            <h1 style='color: #0f172a; font-size: 1.5rem;'>DocForge Hub</h1>
            <p style='color: #64748b; font-size: 0.8rem;'>AI-Powered Document Generation</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("### 📍 Document")
    departments = [
        "HR", "IT Operations", "Legal", "Marketing", "Finance & Accounting",
        "Engineering", "Quality Assurance", "Security & Compliance",
        "Customer Success", "Product Management"
    ]
    department = st.selectbox("Department", departments, key="sidebar_department")

    try:
        response = requests.get(f"{API_BASE_URL}/documents/list", params={"department": department})
        documents_meta = response.json() if response.status_code == 200 else []
    except:
        documents_meta = []
        st.warning("⚠️ Backend connection failed")

    document_types = sorted(set(doc["internal_type"] for doc in documents_meta))
    selected_type = st.selectbox("Document Type", ["ALL"] + document_types, key="sidebar_doc_type")

    filtered_docs = documents_meta if selected_type == "ALL" else [doc for doc in documents_meta if doc["internal_type"] == selected_type]
    document_filename = st.selectbox("Document Template", [doc["document_name"] for doc in filtered_docs], key="sidebar_document") if filtered_docs else None

# ---------------- MAIN CONTENT ----------------
st.markdown("""
    <div class='welcome-header'>
        <div style='text-align: center; padding: 20px 0;'>
            <h1>⚡ Document Forge</h1>
            <p style='color: #64748b;'>Intelligent document generation platform powered by AI</p>
        </div>
    </div>
""", unsafe_allow_html=True)

tab_gen, tab_lib = st.tabs(["✨ Generate Draft", "📚 Draft Library"])

with tab_gen:
    if document_filename:
        try:
            # Fetch document configuration
            response = requests.post(f"{API_BASE_URL}/documents/preview", 
                                   json={"department": department, "document_filename": document_filename})
            
            if response.status_code == 200:
                doc_config = response.json()
                merged_groups = merge_input_groups(doc_config)
                
                base_groups = [g for g in merged_groups if g.get("source") == "base"]
                doc_groups = [g for g in merged_groups if g.get("source") != "base"]
                
                # Total steps: 1 (company) + base + doc
                doc_step_count = len(base_groups) + len(doc_groups)
                total_steps = 1 + doc_step_count
                current_step = st.session_state.current_step
                
                # Progress bar
                st.progress((current_step + 1) / total_steps, text=f"Step {current_step + 1} of {total_steps}")
                
                # Step indicators
                step_names = ["Company Profile"] + ["Document Info"] + [f"Section {i+2}" for i in range(doc_step_count-1)] if doc_step_count > 1 else ["Company Profile", "Document Info"]
                st.markdown('<div class="step-container">', unsafe_allow_html=True)
                cols = st.columns(total_steps)
                for i, col in enumerate(cols):
                    with col:
                        if i == current_step:
                            number_class = "active"
                            text_class = "active"
                        elif i < current_step:
                            number_class = "completed"
                            text_class = "pending"
                        else:
                            number_class = "pending"
                            text_class = "pending"
                        st.markdown(f"""
                            <div class='step-item {text_class}'>
                                <div class='step-number {number_class}'>{i+1}</div>
                                <div class='step-text {text_class}'>{step_names[i]}</div>
                            </div>
                        """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Render current step
                if current_step == 0:
                    # Company profile step
                    render_company_step()
                    validation_errors = []  # no doc validation yet
                    # Check required fields later on generate
                else:
                    # Document step (index current_step - 1 in merged groups)
                    doc_idx = current_step - 1
                    all_groups = base_groups + doc_groups
                    group = all_groups[doc_idx]
                    # Add icon if missing
                    if 'icon' not in group:
                        group['icon'] = "📄"
                    if 'description' not in group:
                        group['description'] = f"{doc_config['document_name']} details"
                    user_inputs, validation_errors = render_document_step(doc_idx, group, doc_config['document_name'])
                    # Save inputs to session state
                    for key, value in user_inputs.items():
                        st.session_state.form_data[f"{doc_idx}_{key}"] = value
                
                # Navigation buttons
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if current_step > 0:
                        if st.button("◀ Previous", use_container_width=True):
                            st.session_state.current_step -= 1
                            st.rerun()
                with col3:
                    if current_step < total_steps - 1:
                        if st.button("Next ▶", use_container_width=True, type="primary"):
                            # Validate only if on a document step (not company)
                            if current_step > 0 and validation_errors:
                                for err in validation_errors:
                                    st.error(f"❌ {err}")
                            else:
                                st.session_state.current_step += 1
                                st.rerun()
                    else:
                        # Last step: Generate
                        if st.button("🚀 Generate Draft", use_container_width=True, type="primary"):
                            # Validate company profile mandatory fields
                            company = st.session_state.company_profile
                            if not all([company["company_name"], company["industry"], company["region"], company["jurisdiction"]]):
                                st.error("❌ Please complete all mandatory Company Profile fields (Name, Industry, Region, Jurisdiction).")
                            elif validation_errors:
                                for err in validation_errors:
                                    st.error(f"❌ {err}")
                            else:
                                # Collect all document inputs
                                all_inputs = {}
                                for step in range(doc_step_count):
                                    for field in all_groups[step]["fields"]:
                                        key = f"step_{step}_{field['key']}"
                                        if key in st.session_state:
                                            all_inputs[field['key']] = st.session_state[key]
                                
                                # Convert dates to ISO
                                for key, value in all_inputs.items():
                                    if hasattr(value, "isoformat"): 
                                        all_inputs[key] = value.isoformat()
                                
                                with st.spinner("🎨 Crafting your document..."):
                                    try:
                                        gen_resp = requests.post(f"{API_BASE_URL}/documents/generate", json={
                                            "department": department.lower(),
                                            "document_filename": document_filename,
                                            "company_profile": company,
                                            "document_inputs": all_inputs
                                        })
                                        if gen_resp.status_code == 200:
                                            st.success("✅ Draft Generated Successfully!")
                                            st.balloons()
                                            st.session_state.selected_draft_id = gen_resp.json()["draft_id"]
                                            st.session_state.current_step = 0  # reset
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Generation failed. Please try again. (Status {gen_resp.status_code})")
                                    except Exception as e:
                                        st.error(f"❌ Backend connection error: {e}")
            else:
                st.error("Failed to load document configuration.")
        except Exception as e:
            st.error(f"❌ Backend connection error: {e}")
    else:
        st.info("👈 Select a document template from sidebar")

with tab_lib:
    st.markdown("### 📚 Document Library")
    
    search = st.text_input("🔍 Search", placeholder="Type to search...", key="lib_search")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents/drafts")
        if response.status_code == 200:
            drafts = response.json()
            if drafts:
                # Keep only latest version per document
                unique_docs = {}
                for draft in drafts:
                    name = draft["document_name"]
                    if name not in unique_docs or draft["version"] > unique_docs[name]["version"]:
                        unique_docs[name] = draft
                filtered_drafts = list(unique_docs.values())
                
                if search:
                    filtered_drafts = [d for d in filtered_drafts if search.lower() in d['document_name'].lower()]
                
                if filtered_drafts:
                    for i in range(0, len(filtered_drafts), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(filtered_drafts):
                                draft = filtered_drafts[i + j]
                                with cols[j]:
                                    st.markdown(f"""
                                        <div class="draft-card">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                <div>
                                                    <strong style="color: #0f172a;">{draft['document_name'][:25]}{'...' if len(draft['document_name']) > 25 else ''}</strong>
                                                    <div style="font-size: 0.8rem; color: #64748b;">v{draft.get('version', '1.0')}</div>
                                                </div>
                                                {get_status_badge(draft['status'])}
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("👁️ View", key=f"v_{draft['id']}", use_container_width=True):
                                            st.session_state.selected_draft_id = draft["id"]
                                            st.rerun()
                                    with col2:
                                        if st.button("🗑️", key=f"d_{draft['id']}", use_container_width=True):
                                            requests.delete(f"{API_BASE_URL}/documents/draft/{draft['id']}")
                                            st.rerun()
                else:
                    st.info("No matching documents found")
            else:
                st.info("No documents found in library")
    except Exception as e:
        st.error(f"❌ Failed to load drafts: {e}")

# ---------------- DOCUMENT PREVIEW ----------------
if st.session_state.selected_draft_id:
    st.markdown("<hr style='margin: 30px 0; border-color: #eef2f6;'>", unsafe_allow_html=True)
    
    try:
        resp = requests.get(f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}")
        if resp.status_code == 200:
            draft_detail = resp.json()
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"<span style='color: #0f172a; font-weight: 600;'>{draft_detail['document_name']}  v{draft_detail.get('version', '1.0')}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/pdf" target="_blank"><button style="width:100%; background: linear-gradient(135deg, #2563eb, #3b82f6); color: white; border: none; border-radius: 30px; padding: 10px; font-weight: 600;">📥 PDF</button></a>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/docx" target="_blank"><button style="width:100%; background: linear-gradient(135deg, #2563eb, #3b82f6); color: white; border: none; border-radius: 30px; padding: 10px; font-weight: 600;">📥 DOCX</button></a>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/xls" target="_blank"><button style="width:100%; background: linear-gradient(135deg, #2563eb, #3b82f6); color: white; border: none; border-radius: 30px; padding: 10px; font-weight: 600;">📥 XLS</button></a>', unsafe_allow_html=True)
            
            st.markdown('<div class="document-paper">', unsafe_allow_html=True)
            st.markdown(f"<h1>{draft_detail['document_name']}</h1>", unsafe_allow_html=True)
            company = st.session_state.company_profile
            st.markdown(f"<p style='text-align:center; color: #64748b;'>Company: {company.get('company_name', 'N/A')}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color: #eef2f6;'>", unsafe_allow_html=True)
            
            for section in draft_detail["sections"]:
                st.markdown(f"<h2>{section['section_name']}</h2>", unsafe_allow_html=True)
                
                raw_content = section["content"]
                try:
                    blocks = json.loads(raw_content)
                    if isinstance(blocks, str):
                        blocks = json.loads(blocks)
                except:
                    blocks = []
                
                if not isinstance(blocks, list):
                    st.markdown(raw_content)
                else:
                    for block in blocks:
                        if isinstance(block, dict):
                            if block.get("type") == "paragraph":
                                st.markdown(block.get("content", ""))
                            elif block.get("type") == "table":
                                df = pd.DataFrame(
                                    block.get("rows", []),
                                    columns=block.get("headers", [])
                                )
                                st.table(df)
                st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Failed to load document preview: {e}")

# ---------------- FOOTER ----------------
st.markdown("""
    <div class="footer">
        <p>⚡ DocForge Hub - AI-Powered Intelligent Document Generation Platform</p>
        <p style='font-size: 0.7rem; margin-top: 5px;'>© 2024 All rights reserved</p>
    </div>
""", unsafe_allow_html=True)