import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"

# ---------------- UI CONFIG & ENHANCED STYLING ----------------
st.set_page_config(
    page_title="DocForge Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced CSS with modern design system
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main content area with glass morphism effect */
    .main > div {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.5);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #fff;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #fff !important;
    }
    
    /* Modern Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background: transparent;
        padding: 10px 20px;
        border-bottom: 2px solid rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: transparent;
        border-radius: 25px;
        padding: 10px 30px;
        font-weight: 600;
        color: #666;
        border: none;
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.1);
        color: #667eea;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 10px 20px -5px rgba(102, 126, 234, 0.4);
    }
    
    /* Professional Document Paper */
    .document-paper {
        background: white;
        padding: 60px 80px;
        border-radius: 20px;
        box-shadow: 0 30px 60px -20px rgba(0,0,0,0.3);
        font-family: 'Playfair Display', serif;
        line-height: 1.8;
        color: #2d3748;
        max-width: 900px;
        margin: 30px auto;
        border: 1px solid rgba(255,255,255,0.3);
        position: relative;
    }
    
    .document-paper::before {
        content: '';
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        bottom: 20px;
        border: 2px solid #f0f0f0;
        border-radius: 15px;
        pointer-events: none;
    }
    
    .document-paper h1 {
        font-family: 'Inter', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px;
        text-align: center;
        letter-spacing: -0.5px;
    }
    
    .document-paper h2 {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-top: 40px;
        margin-bottom: 20px;
        border-bottom: 3px solid #667eea;
        padding-bottom: 10px;
    }
    
    .document-paper p {
        font-size: 1.1rem;
        color: #4a5568;
        margin-bottom: 20px;
    }
    
    /* Modern Action Bar */
    .preview-toolbar {
        background: white;
        padding: 15px 25px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        position: sticky;
        top: 70px;
        z-index: 1000;
        backdrop-filter: blur(10px);
        background: rgba(255, 255, 255, 0.9);
    }
    
    /* Library Cards */
    .draft-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 15px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
    }
    
    .draft-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .draft-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    /* Animated Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 30px -10px rgba(102, 126, 234, 0.5);
    }
    
    /* Form Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 12px !important;
        transition: all 0.3s ease !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    
    .streamlit-expanderContent {
        background: white;
        border-radius: 0 0 12px 12px;
        padding: 20px !important;
        border: 1px solid #e2e8f0;
        border-top: none;
    }
    
    /* Group header styling */
    .group-header {
        font-size: 1rem;
        font-weight: 600;
        color: #4a5568;
        margin: 15px 0 10px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #e2e8f0;
    }
    
    /* Required field indicator */
    .required-field {
        color: #ef4444;
        font-size: 0.9rem;
        margin-left: 5px;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 6px 15px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-draft {
        background: #fff3cd;
        color: #856404;
    }
    
    .badge-published {
        background: #d4edda;
        color: #155724;
    }
    
    .badge-archived {
        background: #f8d7da;
        color: #721c24;
    }
    
    /* Welcome Header */
    .welcome-header {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 30px;
    }
    
    .welcome-header h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    
    .welcome-header p {
        color: #666;
        font-size: 1.1rem;
    }
    
    /* Divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 30px 0;
    }
    
    /* Validation message */
    .validation-error {
        background: #fee2e2;
        color: #dc2626;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #dc2626;
        margin: 10px 0;
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

# ---------------- HELPER FUNCTIONS ----------------
def format_date(date_string):
    """Format date string nicely"""
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        return date_string

def get_status_badge(status):
    """Return HTML for status badge"""
    colors = {
        "draft": ("badge-draft", "📝 Draft"),
        "published": ("badge-published", "✅ Published"),
        "archived": ("badge-archived", "📦 Archived")
    }
    badge_class, text = colors.get(status.lower(), ("badge-draft", status))
    return f'<span class="status-badge {badge_class}">{text}</span>'

# ---------------- FIELD RENDERING ----------------
def render_field(label, field, key):
    field_type = field["type"]
    if field_type == "text": 
        return st.text_input(label, key=key, placeholder=f"Enter {label.lower()}...")
    elif field_type == "textarea": 
        return st.text_area(label, key=key, height=100, placeholder=f"Enter {label.lower()}...")
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

# ---------------- DYNAMIC FORM ----------------
def render_dynamic_form(base_groups, doc_groups, document_name):
    user_inputs = {}
    validation_errors = []
    
    st.markdown(f"### ⚙️ Configure: {document_name}")
    
    if base_groups:
        with st.expander("📋 1. General Information", expanded=True):
            for group in base_groups:
                st.markdown(f"**{group['group_name']}**")
                for field in group["fields"]:
                    key, label = field["key"], field["label"]
                    if field.get("required"): 
                        label = f"{label} <span class='required-field'>*</span>"
                    value = render_field(label, field, f"base_{key}")
                    user_inputs[key] = value
                    if field.get("required") and not value:
                        validation_errors.append(f"{field['label']} is required.")
                st.markdown("---")

    if doc_groups:
        with st.expander(f"📄 2. {document_name} Details", expanded=True):
            for group in doc_groups:
                st.markdown(f"**{group['group_name']}**")
                for field in group["fields"]:
                    key, label = field["key"], field["label"]
                    if field.get("required"): 
                        label = f"{label} <span class='required-field'>*</span>"
                    value = render_field(label, field, f"doc_{key}")
                    user_inputs[key] = value
                    if field.get("required") and not value:
                        validation_errors.append(f"{field['label']} is required.")
                st.markdown("---")
    return user_inputs, validation_errors

# ---------------- SIDEBAR: SELECTION & MANDATORY PROFILE ----------------
with st.sidebar:
    # Logo and Header
    st.markdown("""
        <div style='text-align: center; padding: 30px 0 20px 0;'>
            <div style='font-size: 3rem; margin-bottom: 10px;'>⚡</div>
            <h1 style='color: white; font-size: 1.8rem; margin: 0;'>DocForge Hub</h1>
            <p style='color: #a0aec0; font-size: 0.8rem; margin-top: 5px;'>Intelligent Document Generation</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    st.subheader("📍 Document Selection")
    departments = ["HR", "IT Operations", "Legal", "Marketing", "Finance & Accounting", "Engineering", "Quality Assurance", "Security & Compliance", "Customer Success", "Product Management"]
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

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    st.subheader("🏢 Company Profile")
    st.caption("Mandatory: Profile details are embedded into the document.")
    
    company_name = st.text_input("Company Name *", key="sidebar_company_name")
    industry = st.text_input("Industry *", key="sidebar_industry")
    employee_count = st.number_input("Employee Count", min_value=1, key="sidebar_employee_count", value=100)
    region = st.text_input("Operating Region *", key="sidebar_region")
    compliance = st.text_input("Compliance Framework", key="sidebar_compliance")
    jurisdiction = st.text_input("Jurisdiction *", key="sidebar_jurisdiction")
    
    # Profile completion indicator
    required_fields = [company_name, industry, region, jurisdiction]
    completion = sum(1 for f in required_fields if f) / len(required_fields) if any(required_fields) else 0
    st.progress(completion, text=f"Profile {int(completion*100)}% complete")

# ---------------- MAIN CONTENT ----------------
st.markdown("""
    <div class='welcome-header'>
        <h1>⚡ Document Forge</h1>
        <p>Intelligent document generation and management platform</p>
    </div>
""", unsafe_allow_html=True)

# Tabs
tab_gen, tab_lib = st.tabs(["✨ Generate Draft", "📚 Draft Library"])

with tab_gen:
    if document_filename:
        try:
            response = requests.post(f"{API_BASE_URL}/documents/preview", 
                                   json={"department": department, "document_filename": document_filename})
            
            if response.status_code == 200:
                doc_config = response.json()
                merged_groups = merge_input_groups(doc_config)
                
                base_groups = [g for g in merged_groups if g.get("source") == "base"]
                doc_groups = [g for g in merged_groups if g.get("source") != "base"]

                user_inputs, validation_errors = render_dynamic_form(base_groups, doc_groups, doc_config["document_name"])

                st.markdown("---")
                
                # Generate button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🚀 Generate Draft", use_container_width=True, type="primary", key="generate_btn"):
                        # MANDATORY PROFILE VALIDATION
                        if not all([company_name, industry, region, jurisdiction]):
                            st.error("❌ Please complete all mandatory Company Profile fields in the sidebar.")
                        elif validation_errors:
                            for err in validation_errors:
                                st.error(f"❌ {err}")
                        else:
                            # Logic for ISO format and API Post
                            for key, value in user_inputs.items():
                                if hasattr(value, "isoformat"): 
                                    user_inputs[key] = value.isoformat()
                            
                            with st.spinner("🎨 Crafting your document..."):
                                try:
                                    gen_resp = requests.post(f"{API_BASE_URL}/documents/generate", json={
                                        "department": department.lower(),
                                        "document_filename": document_filename,
                                        "company_profile": {
                                            "company_name": company_name, 
                                            "industry": industry, 
                                            "employee_count": employee_count,
                                            "regions": [region], 
                                            "compliance_frameworks": [compliance] if compliance else [], 
                                            "default_jurisdiction": jurisdiction
                                        },
                                        "document_inputs": user_inputs
                                    })
                                    if gen_resp.status_code == 200:
                                        st.success("✅ Draft Generated Successfully!")
                                        st.balloons()
                                        st.session_state.selected_draft_id = gen_resp.json()["draft_id"]
                                        st.rerun()
                                    else:
                                        st.error("❌ Generation failed. Please try again.")
                                except:
                                    st.error("❌ Backend connection error")
            else:
                st.error("Failed to load document configuration.")
        except:
            st.error("❌ Backend connection error")
    else:
        st.info("👈 Please select a document template from the sidebar.")

with tab_lib:
    st.markdown("### 📚 Draft Library")
    
    # Search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search drafts", placeholder="Type to search...", key="library_search")
    with col2:
        status_filter = st.multiselect("Filter by status", ["draft", "published", "archived"], 
                                      default=["draft"], key="library_status_filter")
    with col3:
        sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Name A-Z", "Name Z-A"], key="library_sort")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents/drafts")
        if response.status_code == 200:
            drafts = response.json()
            if drafts:
                # Filter and sort logic
                if search:
                    drafts = [d for d in drafts if search.lower() in d['document_name'].lower()]
                
                filtered_drafts = [d for d in drafts if d['status'] in status_filter]
                
                # Sort drafts
                if sort_by == "Newest":
                    filtered_drafts.sort(key=lambda x: x['created_at'], reverse=True)
                elif sort_by == "Oldest":
                    filtered_drafts.sort(key=lambda x: x['created_at'])
                elif sort_by == "Name A-Z":
                    filtered_drafts.sort(key=lambda x: x['document_name'])
                elif sort_by == "Name Z-A":
                    filtered_drafts.sort(key=lambda x: x['document_name'], reverse=True)
                
                # Display drafts
                if filtered_drafts:
                    for draft in filtered_drafts:
                        with st.container():
                            st.markdown(f"""
                                <div class="draft-card">
                                    <div style="display: flex; justify-content: space-between; align-items: start;">
                                        <div style="flex: 1;">
                                            <h3 style="margin: 0 0 10px 0;">{draft['document_name']}</h3>
                                            <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                                                <span style="color: #666;">📁 {draft.get('department', 'N/A')}</span>
                                                <span style="color: #666;">📌 v{draft.get('version', '1.0')}</span>
                                                <span style="color: #666;">📅 {format_date(draft['created_at'])}</span>
                                            </div>
                                        </div>
                                        <div>
                                            {get_status_badge(draft['status'])}
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                            with col2:
                                if st.button("👁️ View", key=f"view_{draft['id']}", use_container_width=True):
                                    st.session_state.selected_draft_id = draft["id"]
                                    st.rerun()
                            with col3:
                                if st.button("📥 Export", key=f"export_{draft['id']}", use_container_width=True):
                                    st.info("Choose format below")
                            with col4:
                                if st.button("🗑️ Delete", key=f"del_{draft['id']}", use_container_width=True):
                                    if requests.delete(f"{API_BASE_URL}/documents/draft/{draft['id']}").status_code == 200:
                                        st.success("Deleted!")
                                        st.rerun()
                            st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.info("📭 No drafts match your filters")
            else:
                st.info("📭 Your draft library is empty. Generate your first document!")
    except:
        st.error("❌ Failed to load drafts")

# ---------------- DOCUMENT PREVIEW ----------------
if st.session_state.selected_draft_id:
    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
    
    try:
        resp = requests.get(f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}")
        if resp.status_code == 200:
            draft_detail = resp.json()
            
            # Preview toolbar
            st.markdown(f"""
                <div class="preview-toolbar">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 1.8rem;">📄</span>
                        <div>
                            <span style="font-weight:bold; font-size:1.3rem;">{draft_detail['document_name']}</span>
                            <span style="margin-left: 15px;">{get_status_badge(draft_detail['status'])}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([1,1,1,1,4])
            with btn_col1:
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/pdf" target="_blank"><button style="width:100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 12px 25px; font-weight: 600;">📥 PDF</button></a>', unsafe_allow_html=True)
            with btn_col2:
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/docx" target="_blank"><button style="width:100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 12px 25px; font-weight: 600;">📥 DOCX</button></a>', unsafe_allow_html=True)
            with btn_col3:
                if st.button("📧 Share", use_container_width=True, key="preview_share"):
                    st.info("Sharing feature coming soon!")
            with btn_col4:
                if st.button("✖️ Close", use_container_width=True, key="preview_close"):
                    st.session_state.selected_draft_id = None
                    st.rerun()
            
            # Document content
            st.markdown('<div class="document-paper">', unsafe_allow_html=True)
            
            # Title
            st.markdown(f"<h1>{draft_detail['document_name']}</h1>", unsafe_allow_html=True)
            
            # Company info
            if company_name:
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 30px;">
                        <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                     color: white; padding: 8px 25px; border-radius: 25px;
                                     font-size: 0.9rem;">
                            {company_name} • Version {draft_detail.get('version', '1.0')}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Render sections
            for section in draft_detail["sections"]:
                st.markdown(f"<h2>{section['section_name']}</h2>", unsafe_allow_html=True)
                st.markdown(section['content'])
                st.markdown("<br>", unsafe_allow_html=True)
            
            # Footer
            st.markdown("---")
            st.markdown(f"""
                <div style="text-align: center; color: #718096; font-size: 0.8rem;">
                    Generated by DocForge Hub • {datetime.now().strftime('%B %d, %Y')}
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.error("❌ Failed to load document preview")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #718096; padding: 20px;">
        <p>⚡ DocForge Hub - Intelligent Document Generation Platform</p>
        <p style="font-size: 0.8rem;">© 2024 All rights reserved</p>
    </div>
""", unsafe_allow_html=True)
