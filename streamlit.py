import streamlit as st
import requests
from backend.utils.schema_merger import merge_input_groups
from datetime import datetime, date

API_BASE_URL = "http://127.0.0.1:8000"

# ---------------- UI CONFIG & ENHANCED STYLING ----------------
st.set_page_config(
    page_title="DocForge Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* ── GLOBAL BASE ── */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%) !important;
        color: #e2e8f0 !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* Main block container glass */
    .main > div {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 30px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* ── ALL TEXT → LIGHT ── */
    /* Covers Streamlit-generated markdown, paragraphs, headings, spans */
    .stApp p,
    .stApp span,
    .stApp label,
    .stApp h1, .stApp h2, .stApp h3,
    .stApp h4, .stApp h5, .stApp h6,
    .stApp li,
    .stApp div.stMarkdown,
    .stApp .stMarkdown p,
    .stApp [data-testid="stText"],
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] span {
        color: #e2e8f0 !important;
    }

    /* ── FORM LABELS ── */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stDateInput label,
    .stNumberInput label,
    .stCheckbox label,
    .stMultiSelect label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }

    /* ── INPUTS ── */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input,
    input[type="text"],
    input[type="number"],
    textarea {
        background: #1e2d3d !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        caret-color: #00d2ff !important;
        font-size: 0.95rem !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
    }

    /* Keep dark background AND light text when focused/active/typing */
    .stTextInput input:focus,
    .stTextInput input:active,
    .stTextArea textarea:focus,
    .stTextArea textarea:active,
    .stNumberInput input:focus,
    .stNumberInput input:active,
    .stDateInput input:focus,
    input[type="text"]:focus,
    input[type="text"]:active,
    input[type="number"]:focus,
    textarea:focus,
    textarea:active {
        background: #1e2d3d !important;
        color: #e2e8f0 !important;
        caret-color: #00d2ff !important;
        border-color: #00d2ff !important;
        box-shadow: 0 0 0 3px rgba(0,210,255,0.2) !important;
        outline: none !important;
        -webkit-text-fill-color: #e2e8f0 !important;
    }

    /* Override browser autofill which forces white bg */
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus,
    textarea:-webkit-autofill {
        -webkit-box-shadow: 0 0 0px 1000px #1e2d3d inset !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        caret-color: #00d2ff !important;
    }

    /* ── PLACEHOLDERS ── */
    input::placeholder,
    textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }

    /* ── SELECTBOX ── */
    /* The visible value text inside a selectbox */
    [data-testid="stSelectbox"] div[data-baseweb="select"] span,
    [data-testid="stSelectbox"] [data-baseweb="select"] div {
        color: #ffffff !important;
        background: transparent !important;
    }

    [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }

    /* Dropdown list items */
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="option"] {
        background: #1e293b !important;
        color: #e2e8f0 !important;
    }

    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background: rgba(0,210,255,0.15) !important;
        color: #ffffff !important;
    }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2634 0%, #0f172a 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.1);
        box-shadow: 10px 0 30px -15px rgba(0,0,0,0.5);
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #e2e8f0 !important;
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stCaption p,
    [data-testid="stSidebar"] small {
        color: #94a3b8 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.05) !important;
        border-color: rgba(255,255,255,0.2) !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] span {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] input {
        color: #ffffff !important;
        background: rgba(255,255,255,0.07) !important;
        border-color: rgba(255,255,255,0.15) !important;
    }

    hr {
        border-color: rgba(255,255,255,0.1) !important;
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background: rgba(255,255,255,0.03);
        padding: 8px 15px;
        border-radius: 50px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background: transparent;
        border-radius: 30px;
        padding: 8px 25px;
        font-weight: 600;
        color: #94a3b8 !important;
        border: none;
        transition: all 0.3s ease;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255,255,255,0.1);
        color: #ffffff !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%) !important;
        color: white !important;
        box-shadow: 0 10px 20px -5px rgba(0,210,255,0.3);
    }

    /* Tab label text */
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span {
        color: inherit !important;
    }

    /* ── PROGRESS BAR ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5) !important;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,210,255,0.5);
    }

    /* Progress label */
    .stProgress + div small,
    [data-testid="stProgressBarMessage"] {
        color: #94a3b8 !important;
    }

    /* ── BUTTONS ── */
    .stButton > button {
        background: linear-gradient(135deg, #00d2ff, #3a7bd5) !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 10px 25px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 5px 15px rgba(0,210,255,0.4) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(0,210,255,0.6) !important;
    }

    /* ── ALERTS ── */
    [data-testid="stAlert"],
    .stAlert {
        background: rgba(0,0,0,0.35) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }

    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {
        color: #e2e8f0 !important;
    }

    /* ── EXPANDER ── */
    [data-testid="stExpander"] summary,
    .streamlit-expanderHeader {
        color: #e2e8f0 !important;
        background: rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
    }

    [data-testid="stExpander"] p,
    .streamlit-expanderContent p {
        color: #e2e8f0 !important;
    }

    /* ── CUSTOM COMPONENTS ── */
    /* Step container */
    .step-container {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin: 20px 0 30px;
        padding: 15px;
        background: rgba(255,255,255,0.03);
        border-radius: 60px;
        border: 1px solid rgba(255,255,255,0.1);
    }

    .step-item { display: flex; align-items: center; gap: 10px; padding: 5px 15px; border-radius: 30px; transition: all 0.3s ease; }
    .step-item.active { background: rgba(0,210,255,0.1); border: 1px solid rgba(0,210,255,0.25); }

    .step-number { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; }
    .step-number.active   { background: linear-gradient(135deg, #00d2ff, #3a7bd5); color: white; box-shadow: 0 0 15px #00d2ff; }
    .step-number.completed { background: #10b981; color: white; }
    .step-number.pending  { background: rgba(255,255,255,0.1); color: #94a3b8; border: 1px solid rgba(255,255,255,0.2); }

    .step-text        { font-size: 0.9rem; font-weight: 500; color: #94a3b8; }
    .step-text.active { color: #00d2ff; }

    /* Group card */
    .group-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }
    .group-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, #00d2ff, #3a7bd5, transparent);
        transition: left 0.5s ease;
    }
    .group-card:hover::before { left: 100%; }
    .group-card:hover { border-color: rgba(0,210,255,0.5); box-shadow: 0 10px 30px -10px rgba(0,210,255,0.25); transform: translateY(-2px); }

    .group-header { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .group-icon { width: 50px; height: 50px; background: rgba(0,210,255,0.1); border-radius: 15px; display: flex; align-items: center; justify-content: center; color: #00d2ff; font-size: 1.8rem; border: 1px solid rgba(0,210,255,0.25); }
    .group-title       { font-size: 1.2rem; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; }
    .group-description { font-size: 0.85rem; color: #94a3b8; }

    /* Document paper */
    .document-paper {
        background: #1e293b;
        padding: 60px 80px;
        border-radius: 20px;
        box-shadow: 0 30px 60px -20px rgba(0,0,0,0.5);
        font-family: 'Space Grotesk', sans-serif;
        line-height: 1.8;
        color: #e2e8f0;
        max-width: 900px;
        margin: 30px auto;
        border: 1px solid rgba(255,255,255,0.1);
        position: relative;
    }
    .document-paper::before {
        content: '';
        position: absolute;
        top: 10px; left: 10px; right: 10px; bottom: 10px;
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 15px;
        pointer-events: none;
    }
    .document-paper h1 {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem; font-weight: 800;
        background: linear-gradient(135deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px; text-align: center; letter-spacing: -1px;
    }
    .document-paper h2 {
        font-family: 'Outfit', sans-serif;
        font-size: 1.8rem; font-weight: 700; color: #ffffff;
        margin-top: 40px; margin-bottom: 20px;
        border-bottom: 2px solid rgba(0,210,255,0.25);
        padding-bottom: 10px;
    }

    /* Draft cards */
    .draft-card {
        background: rgba(255,255,255,0.03);
        padding: 20px; border-radius: 16px; margin-bottom: 15px;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
    .draft-card:hover { transform: translateY(-2px); border-color: rgba(0,210,255,0.5); box-shadow: 0 15px 30px -10px rgba(0,210,255,0.25); }
    .draft-card strong { color: white !important; }

    /* Status badges */
    .status-badge { display: inline-block; padding: 6px 15px; border-radius: 30px; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.5px; }
    .badge-draft     { background: rgba(251,191,36,0.12); color: #fbbf24 !important; border: 1px solid rgba(251,191,36,0.25); }
    .badge-published { background: rgba(16,185,129,0.12); color: #10b981 !important; border: 1px solid rgba(16,185,129,0.25); }

    /* Welcome header */
    .welcome-header { text-align: center; padding: 30px 0 20px; margin-bottom: 20px; }
    .welcome-header h1 {
        font-size: 3rem; font-weight: 800;
        background: linear-gradient(135deg, #ffffff, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px; letter-spacing: -1px;
    }
    .welcome-header p { color: #94a3b8 !important; font-size: 1.1rem; font-weight: 400; }
    .emoji-row { display: flex; justify-content: center; gap: 20px; margin: 20px 0; font-size: 2rem; }

    /* Footer */
    .footer { text-align: center; color: #94a3b8 !important; padding: 30px 0 10px; font-size: 0.8rem; position: relative; }
    .footer::before {
        content: '';
        position: absolute; top: 0; left: 25%; width: 50%; height: 1px;
        background: linear-gradient(90deg, transparent, #00d2ff, #3a7bd5, #00d2ff, transparent);
    }
    .footer p { color: #94a3b8 !important; }
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

def render_step_form(base_groups, doc_groups, doc_name, current_step):
    all_groups = []
    if base_groups:
        for group in base_groups:
            group_copy = group.copy()
            group_copy['icon'] = "📋"
            group_copy['description'] = "Basic document information"
            all_groups.append(group_copy)
    if doc_groups:
        for group in doc_groups:
            group_copy = group.copy()
            group_copy['icon'] = "📄"
            group_copy['description'] = f"{doc_name} specific details"
            all_groups.append(group_copy)
    
    total_steps = len(all_groups)
    current_step = min(current_step, total_steps - 1) if total_steps > 0 else 0
    
    if total_steps > 0:
        progress = (current_step + 1) / total_steps
        st.progress(progress, text=f"Step {current_step + 1} of {total_steps}")
        
        step_names = ["Document Info"] + [f"Section {i+2}" for i in range(total_steps-1)]
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        cols = st.columns(total_steps)
        for i, col in enumerate(cols):
            with col:
                if i < total_steps:
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
        
        if current_step < len(all_groups):
            group = all_groups[current_step]
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
                    value = render_field(label, field, f"step_{current_step}_{key}")
                    user_inputs[key] = value
                    if field.get("required") and not value:
                        validation_errors.append(f"{field['label']} is required.")
            return user_inputs, validation_errors, total_steps
    return {}, [], total_steps

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <div style='font-size: 3rem; margin-bottom: 10px;'>⚡</div>
            <h1 style='color: white !important; font-size: 1.8rem; margin: 0;'>DocForge Hub</h1>
            <p style='color: #94a3b8 !important; font-size: 0.8rem;'>AI-Powered Document Generation</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("### 📍 Document")
    departments = ["HR", "IT Operations", "Legal", "Marketing", "Finance & Accounting", 
                   "Engineering", "Quality Assurance", "Security & Compliance", 
                   "Customer Success", "Product Management"]
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

    st.markdown("### 🏢 Company Profile")
    st.caption("Mandatory: Profile details are embedded into the document.")
    
    company_name = st.text_input("Company Name *", key="sidebar_company_name")
    industry = st.text_input("Industry *", key="sidebar_industry")
    employee_count = st.number_input("Employee Count", min_value=1, key="sidebar_employee_count", value=100)
    region = st.text_input("Operating Region *", key="sidebar_region")
    compliance = st.text_input("Compliance Framework", key="sidebar_compliance")
    jurisdiction = st.text_input("Jurisdiction *", key="sidebar_jurisdiction")
    
    required_fields = [company_name, industry, region, jurisdiction]
    completion = sum(1 for f in required_fields if f) / len(required_fields) if any(required_fields) else 0
    st.progress(completion, text=f"Profile {int(completion*100)}% complete")

# ---------------- MAIN CONTENT ----------------
st.markdown("""
    <div class='welcome-header'>
        <div class='emoji-row'>
            <span>⚡</span> <span>📄</span> <span>🤖</span> <span>⚡</span>
        </div>
        <h1>⚡ Document Forge</h1>
        <p>Intelligent document generation platform powered by AI</p>
    </div>
""", unsafe_allow_html=True)

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
                
                user_inputs, validation_errors, total_steps = render_step_form(
                    base_groups, doc_groups, doc_config["document_name"], st.session_state.current_step
                )
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.session_state.current_step > 0:
                        if st.button("◀ Previous", use_container_width=True):
                            st.session_state.current_step -= 1
                            st.rerun()
                
                with col3:
                    if st.session_state.current_step < total_steps - 1:
                        if st.button("Next ▶", use_container_width=True, type="primary"):
                            if validation_errors:
                                for err in validation_errors:
                                    st.error(f"❌ {err}")
                            else:
                                for key, value in user_inputs.items():
                                    st.session_state.form_data[f"{st.session_state.current_step}_{key}"] = value
                                st.session_state.current_step += 1
                                st.rerun()
                    else:
                        if st.button("🚀 Generate Draft", use_container_width=True, type="primary"):
                            if not all([company_name, industry, region, jurisdiction]):
                                st.error("❌ Please complete all mandatory Company Profile fields in the sidebar.")
                            elif validation_errors:
                                for err in validation_errors:
                                    st.error(f"❌ {err}")
                            else:
                                all_inputs = {}
                                for step in range(total_steps):
                                    for field in (base_groups + doc_groups)[step]["fields"]:
                                        key = f"step_{step}_{field['key']}"
                                        if key in st.session_state:
                                            all_inputs[field['key']] = st.session_state[key]
                                
                                for key, value in all_inputs.items():
                                    if hasattr(value, "isoformat"): 
                                        all_inputs[key] = value.isoformat()
                                
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
                                            "document_inputs": all_inputs
                                        })
                                        if gen_resp.status_code == 200:
                                            st.success("✅ Draft Generated Successfully!")
                                            st.balloons()
                                            st.session_state.selected_draft_id = gen_resp.json()["draft_id"]
                                            st.session_state.current_step = 0
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
        st.info("👈 Select a document template from sidebar")

with tab_lib:
    st.markdown("### 📚 Document Library")
    
    search = st.text_input("🔍 Search", placeholder="Type to search...", key="lib_search")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents/drafts")
        if response.status_code == 200:
            drafts = response.json()
            if drafts:
                filtered = [d for d in drafts if search.lower() in d['document_name'].lower()] if search else drafts
                
                if filtered:
                    for i in range(0, len(filtered), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(filtered):
                                draft = filtered[i + j]
                                with cols[j]:
                                    st.markdown(f"""
                                        <div class="draft-card">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                <div>
                                                    <strong style="color: white;">{draft['document_name'][:25]}{'...' if len(draft['document_name']) > 25 else ''}</strong>
                                                    <div style="font-size: 0.8rem; color: #94a3b8;">v{draft.get('version', '1.0')}</div>
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
    except:
        st.error("❌ Failed to load drafts")

# ---------------- DOCUMENT PREVIEW ----------------
if st.session_state.selected_draft_id:
    st.markdown("<hr style='margin: 30px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    try:
        resp = requests.get(f"{API_BASE_URL}/documents/draft/{st.session_state.selected_draft_id}")
        if resp.status_code == 200:
            draft_detail = resp.json()
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"<span style='color: white; font-weight: 600;'>{draft_detail['document_name']}  v{draft_detail.get('version', '1.0')}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/pdf" target="_blank"><button style="width:100%; background: linear-gradient(135deg, #00d2ff, #3a7bd5); color: white; border: none; border-radius: 30px; padding: 10px; font-weight: 600;">📥 PDF</button></a>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<a href="{API_BASE_URL}/documents/export/{st.session_state.selected_draft_id}/docx" target="_blank"><button style="width:100%; background: linear-gradient(135deg, #00d2ff, #3a7bd5); color: white; border: none; border-radius: 30px; padding: 10px; font-weight: 600;">📥 DOCX</button></a>', unsafe_allow_html=True)
            with col4:
                if st.button("✖️", use_container_width=True):
                    st.session_state.selected_draft_id = None
                    st.rerun()
            
            st.markdown('<div class="document-paper">', unsafe_allow_html=True)
            st.markdown(f"<h1>{draft_detail['document_name']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color: #94a3b8;'>Company: {company_name}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            
            for section in draft_detail["sections"]:
                st.markdown(f"<h2>{section['section_name']}</h2>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: #e2e8f0;'>{section['content']}</p>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.error("❌ Failed to load document preview")

# ---------------- FOOTER ----------------
st.markdown("""
    <div class="footer">
        <p>⚡ DocForge Hub - AI-Powered Intelligent Document Generation Platform</p>
        <p style='font-size: 0.7rem; margin-top: 5px;'>© 2024 All rights reserved</p>
    </div>
""", unsafe_allow_html=True)