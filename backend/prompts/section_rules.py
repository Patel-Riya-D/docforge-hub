# section_rules.py

def get_section_rules(document_type: str, section_name: str) -> str:
    """
    Returns strict, section-specific generation rules.
    Combines document-type rules with section-name-specific rules.
    """

    rules = []

    # DOCUMENT TYPE BASE RULES

    doc_type_rules = {

        "POLICY": [
            "Use formal, legal, authoritative language.",
            "Use declarative mandatory language: MUST, SHALL, IS REQUIRED, IS PROHIBITED.",
            "Write in third-person institutional voice.",
            "Avoid operational step-by-step instructions.",
            "Include compliance alignment references where relevant.",
            "No conversational or narrative text.",
        ],

        "SOP": [
            "Write every action as a numbered step.",
            "Each step: one action only.",
            "Use active imperative voice: 'Submit the form' not 'The form should be submitted'.",
            "Add verification checkpoint every 3-5 steps.",
            "Include who is responsible for each step.",
            "No policy enforcement language.",
        ],

        "REPORT": [
            "Write in analytical, objective tone.",
            "Support every claim with data or evidence.",
            "Use Finding → Evidence → Analysis → Implication structure.",
            "Recommendations must have owner, timeline, expected outcome.",
            "No policy or enforcement language.",
        ],

        "RUNBOOK": [
            "Write for someone under pressure. Short sentences only.",
            "Every step must have: ACTION, RUN (command), EXPECT (output), IF FAILS.",
            "No paragraphs longer than 3 lines.",
            "No policy or legal language.",
            "Include severity indicator at section start.",
        ],

        "TEMPLATE": [
            "Use [UPPERCASE_PLACEHOLDER] for all variable fields.",
            "Mark fields as [REQUIRED: X] or [OPTIONAL: X].",
            "Do not fill in content - leave all fields as placeholders.",
            "Include italicized instructions above each section.",
            "Provide one filled-in example per major section.",
        ],

        "OFFER_LETTER": [
            "Write in formal employment contract tone.",
            "Each section must contain 1–3 short sentences only.",
            "Maximum 60 words per section.",
            "Do NOT generate lists or bullet points.",
            "Do NOT generate explanations or background text.",
            "Do NOT repeat information from other sections.",
            "Focus strictly on employment terms.",
        ],

        "HANDBOOK": [
            "Use 'we' and 'our' throughout.",
            "Write at 8th-10th grade reading level.",
            "Explain WHY the policy exists before stating WHAT it requires.",
            "Include a Quick Summary box at end of section.",
            "Use plain-language equivalents for all legal terms.",
            "End with: 'Questions? Contact [HR/Department contact]'.",
            "Do NOT use H2 heading inside section body.",
            "Do NOT repeat the section title inside the content.",
            "Do NOT use enforcement language more than once per section.",
            "Do NOT repeat compliance terms (SOC 2, GDPR) multiple times.",
        ],

        "FORM": [
            "Use field groups with labels only.",
            "No paragraphs longer than 2 sentences.",
            "Mark every field as (Required) or (Optional).",
            "Specify input type: [Text] [Dropdown] [Checkbox] [Date] [Signature].",
            "No narrative or explanatory content.",
        ],

        "STRATEGY": [
            "Every initiative must have: Owner, Timeline, Budget, Success Metric.",
            "Support all assertions with data or market context.",
            "Use OKR or SMART format for objectives.",
            "No operational step-by-step instructions.",
        ],

        "PROPOSAL": [
            "Lead with business problem.",
            "Quantify all benefits with specific metrics.",
            "No vague promises or unverifiable claims.",
            "Pricing must be itemized in table format.",
        ],
    }

    base_rules = doc_type_rules.get(document_type.upper(), [])
    rules.extend(base_rules)

    # SECTION NAME SPECIFIC RULES

    section_lower = section_name.lower()

    # --- INDEX / TABLE OF CONTENTS ---
    toc_sections = ["table of contents", "index", "contents"]
    if any(s in section_lower for s in toc_sections):

        toc_required_types = ["POLICY", "SOP", "REPORT", "HANDBOOK", "STRATEGY", "PROPOSAL"]
        toc_not_required_types = ["RUNBOOK", "TEMPLATE", "FORM"]

        if document_type.upper() in toc_required_types:
            rules = [  # Override all other rules for TOC section
                "Generate a Table of Contents ONLY.",
                "Format: Section Number | Section Name | (Page reference placeholder)",
                "Use dot leaders or dashes between name and page: e.g., '1.1 Purpose .............. 3'",
                "Group by Part/Chapter if document has parts.",
                "Include all H2 and H3 headings.",
                "Do NOT write any other content in this section.",
                "Do NOT add narrative text.",
            ]
        elif document_type.upper() in toc_not_required_types:
            rules = [
                "This document type does NOT require a Table of Contents.",
                "Skip TOC generation entirely.",
                "Return empty string for this section.",
            ]
        return "\n".join(f"• {r}" for r in rules)

    # --- WELCOME / INTRODUCTION ---
    if any(s in section_lower for s in ["welcome", "introduction", "about this"]):
        rules.extend([
            "Write in warm, personal tone.",
            "If HANDBOOK: Write from CEO/HR Director perspective.",
            "Keep to 250-350 words maximum.",
            "Avoid referencing specific policy details.",
            "End with an inspiring or welcoming statement.",
        ])
    
    if "company overview" in section_lower:
        rules.extend([
            "Start with a structured company profile.",
            "Include: Company Name, Industry, Founded Year, Headquarters.",
            "Include: Founders and leadership team.",
            "Include: Employee count and departments.",
            "Follow with a paragraph describing company background.",
            "Use the company_background input if provided.",
            "Do NOT invent company history.",
        ])

    # --- SCOPE ---
    if "scope" in section_lower:
        rules.extend([
            "Explicitly state WHO this applies to.",
            "Explicitly state WHO this does NOT apply to.",
            "Explicitly state WHAT situations/activities are covered.",
            "Explicitly state WHAT is EXCLUDED.",
            "Use two subsections: 'Applies To' and 'Does Not Apply To'.",
            "Do not write general narrative - be specific.",
        ])

    # --- DEFINITIONS ---
    if any(s in section_lower for s in ["definition", "glossary", "terminology"]):
        rules.extend([
            "Format as: **Term**: [Precise definition] for each entry.",
            "Bold each defined term.",
            "Define all acronyms used in the document.",
            "Sort alphabetically.",
            "Do NOT add narrative or examples in this section.",
            "Minimum 5 definitions, maximum 20.",
        ])

    # --- ROLES AND RESPONSIBILITIES ---
    if any(s in section_lower for s in ["responsibilit", "roles", "raci", "ownership"]):
        rules.extend([
            "Format as a table: Role | Responsibilities | Escalates To",
            "Every responsibility starts with an action verb.",
            "Do not use vague language ('oversees', 'manages') - be specific.",
            "Include ALL roles mentioned in the document.",
        ])

    # --- PROCEDURE / STEPS ---
    if any(s in section_lower for s in ["procedure", "process", "steps", "workflow"]):
        rules.extend([
            "Numbered steps are MANDATORY.",
            "Each step: one action, one outcome.",
            "Include decision points as: IF [condition] → THEN [action].",
            "Include timing requirements for each step.",
        ])

    # --- COMPLIANCE / ENFORCEMENT ---
    if any(s in section_lower for s in ["compliance", "enforcement", "violation", "consequence"]):
        if document_type.upper() == "HANDBOOK":
            rules.extend([
                "State consequences in one paragraph only.",
                "Do NOT repeat enforcement language from other sections.",
                "Use plain language: 'may result in disciplinary action' not legalese.",
                "Do NOT list specific termination conditions here.",
            ])
        else:
            rules.extend([
                "State monitoring mechanisms clearly.",
                "Specify consequence severity levels.",
                "Include reporting/violation procedure.",
                "Reference disciplinary policy if applicable.",
            ])

    # --- EXCEPTIONS ---
    if "exception" in section_lower:
        rules.extend([
            "State who can grant exceptions (by role, not name).",
            "State the request process with timeline.",
            "State documentation requirements.",
            "State maximum exception duration.",
        ])

    # --- REVISION HISTORY ---
    if any(s in section_lower for s in ["revision", "changelog", "version history"]):
        rules = [  # Override - this section is always the same
            "Generate a Revision History TABLE ONLY.",
            "Columns: Version | Date | Summary of Changes | Author | Approved By",
            "Include placeholder row for version 1.0.",
            "Do NOT add any narrative text.",
        ]
        return "\n".join(f"• {r}" for r in rules)

    # --- ACKNOWLEDGMENT ---
    if any(s in section_lower for s in ["acknowledgment", "acceptance", "sign", "agreement"]):
        rules = [
            "Format as a formal acknowledgment statement.",
            "Include: Employee Name (print), Signature, Date, Employee ID.",
            "Include: Statement of receipt and understanding.",
            "If HANDBOOK: Include at-will employment acknowledgment.",
            "Do NOT add narrative text.",
            "Keep to 100-150 words maximum.",
        ]
        return "\n".join(f"• {r}" for r in rules)

    # --- TROUBLESHOOTING ---
    if any(s in section_lower for s in ["troubleshoot", "common issue", "faq", "problem"]):
        rules.extend([
            "Format as: Issue | Likely Cause | Solution | Escalate If",
            "Use table format for clarity.",
            "Include minimum 5 common scenarios.",
            "Each solution must be actionable, not vague.",
        ])

    # --- ESCALATION ---
    if "escalation" in section_lower:
        rules.extend([
            "Format as escalation matrix table.",
            "Columns: Level | Contact Role | Contact Method | When to Escalate | SLA",
            "Include L1 through L3/L4 minimum.",
            "Every contact is by role, not personal name.",
        ])

    # --- SECURITY SPECIFIC ---
    if any(s in section_lower for s in ["security", "data protection", "confidential", "privacy"]):
        rules.extend([
            "Reference relevant compliance framework (SOC 2, GDPR, etc.) ONCE only.",
            "Include specific technical controls or requirements.",
            "Avoid vague language ('appropriate security measures').",
            "Include incident reporting requirement.",
        ])

    # --- COMPENSATION / BENEFITS ---
    if any(s in section_lower for s in ["compensation", "salary", "pay", "benefit", "leave", "pto"]):
        rules.extend([
            "State amounts and thresholds specifically.",
            "Include eligibility criteria clearly.",
            "Reference specific systems (BambooHR, Workday) for requests.",
            "State timelines for processing.",
        ])

    # --- COVER PAGE ---
    if any(s in section_lower for s in ["cover", "title page", "front page"]):
        rules = [
            "Generate cover page elements ONLY:",
            "- Company Name (large, prominent)",
            "- Document Title",
            "- Document Type",
            "- Version Number",
            "- Effective Date",
            "- Department/Owner",
            "- Confidentiality Classification",
            "Do NOT add any other text or narrative.",
        ]
        return "\n".join(f"• {r}" for r in rules)

    return "\n".join(f"• {r}" for r in rules)


def requires_toc(document_type: str) -> bool:
    """Helper to check if document type needs TOC."""
    toc_types = {"POLICY", "SOP", "REPORT", "HANDBOOK", "STRATEGY", "PROPOSAL"}
    return document_type.upper() in toc_types


def get_section_word_limit(document_type: str, section_name: str) -> tuple:
    """
    Returns (min_words, max_words) for the section.
    """

    # OFFER LETTER STRICT LIMIT
    if document_type.upper() == "OFFER_LETTER":
        return (20, 60)
    
    section_lower = section_name.lower()

    # Short sections
    short_sections = [
        "cover", "title", "table of contents", "index",
        "acknowledgment", "revision history", "signature",
        "welcome", "introduction"
    ]
    if any(s in section_lower for s in short_sections):
        return (50, 200)

    # Medium sections by doc type
    medium_map = {
        "FORM": (100, 250),
        "TEMPLATE": (150, 350),
        "RUNBOOK": (250, 450),
    }
    if document_type.upper() in medium_map:
        return medium_map[document_type.upper()]

    # Long sections by doc type
    long_map = {
        "REPORT": (80, 150),
        "STRATEGY": (80, 150),
        "PROPOSAL": (80, 150),
        "HANDBOOK": (200, 400)
    }

    if document_type.upper() in long_map:
        return long_map[document_type.upper()]

    # Default
    return (80, 180)
