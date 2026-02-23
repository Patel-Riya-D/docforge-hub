# type_behavior.py

def get_type_behavior(document_type: str) -> dict:
    """
    Returns strict behavioral contract for each document type.
    Returns dict with: rules, format, toc_required, tone, forbidden
    """

    behaviors = {

        "POLICY": {
            "toc_required": True,
            "toc_min_sections": 5,
            "tone": "formal, legal, authoritative",
            "voice": "third-person institutional",
            "format": "structured headings with numbered sections",
            "avg_section_words": "120-180",
            "rules": """
STRICT POLICY DOCUMENT RULES:

POLICY DOCUMENT — BEHAVIORAL CONTRACT

OUTPUT MODE: FINAL ENTERPRISE POLICY

STRUCTURE CONTRACT:
- Content must represent finalized publishable policy text.
- No instructional sentences.
- No template guidance.
- No placeholders.
- No example entries.
- Do NOT repeat section title inside the content.
- Sections must be concise and self-contained.

LANGUAGE CONTRACT:
- Use formal legal tone.
- Use third-person institutional voice.
- Obligations must use Shall, Must, Is Required, or Is Prohibited.
- Do NOT use first-person ("I", "we").
- Do NOT use conversational language.
- Do NOT write step-by-step procedural instructions.
- Avoid vague phrases such as "as appropriate", "when necessary", "as needed".

REPETITION CONTROL:
- Enforcement language may appear only once in the entire document.
- Do NOT repeat binding statements in multiple sections.
- Company name may appear maximum twice per section.

LENGTH CONTRACT:
- Each section must be between 120 and 180 words.
- Exceeding the limit invalidates the section.

FAIL IF:
- Instructional or template-style language appears.
- Placeholders are present.
- Enforcement language appears in multiple sections.
- Word count exceeds defined limits.
            """,
            "forbidden_phrases": [
                "you might want to",
                "it is recommended that you",
                "feel free to",
                "as needed",
                "as appropriate",
                "it is suggested"
            ]
        },

        "SOP": {
            "toc_required": True,
            "toc_min_sections": 5,
            "tone": "procedural, precise, operational",
            "voice": "second-person imperative (you/your role)",
            "format": "numbered steps with verification checkpoints",
            "avg_section_words": "120-180",
            "rules": """
STRICT SOP DOCUMENT RULES:

SOP DOCUMENT — OPERATIONAL PROCEDURE CONTRACT

OUTPUT MODE: EXECUTABLE PROCEDURE

STRUCTURE CONTRACT:
- Every action must be written as a numbered step.
- Each step contains ONE action only.
- No narrative paragraphs.
- Include verification checkpoints.
- Include Roles & Responsibilities table.

LANGUAGE CONTRACT:
- Use imperative voice.
- Start steps with an action verb.
- No legal enforcement language.
- No policy disclaimers.

PROHIBITED:
- No placeholders.
- No conversational tone.
- No vague instructions.
- No combined multi-action steps.

FAIL IF:
- Paragraph-style narrative appears.
- Enforcement language appears.
- Multiple actions exist in one step.
            """,
            "forbidden_phrases": [
                "it is recommended",
                "should be done",
                "may be completed",
                "as appropriate"
            ]
        },

        "REPORT": {
            "toc_required": True,
            "toc_min_sections": 4,
            "tone": "analytical, objective, evidence-based",
            "voice": "third-person analytical",
            "format": "executive summary → findings → analysis → recommendations",
            "avg_section_words": "100-200",
            "rules": """
STRICT REPORT DOCUMENT RULES:

REPORT DOCUMENT — ANALYTICAL CONTRACT

OUTPUT MODE: FINAL ANALYTICAL REPORT

STRUCTURE CONTRACT:
- Begin with an Executive Summary (maximum 250 words).
- Use structured analytical headings.
- Each finding must follow this structure:
  Finding → Evidence → Analysis → Implication.
- Use tables for comparative or numeric data.
- Include a Recommendations section with Owner and Timeline.
- No placeholders. No examples. No template language.

LANGUAGE CONTRACT:
- Use third-person analytical tone.
- All claims must reference metrics, data points, or documented evidence.
- Use measurable indicators (percentages, dates, trends, deltas).
- Avoid opinionated language.

PROHIBITED:
- No enforcement language (SHALL, MUST).
- No procedural steps (SOP style).
- No conversational tone.
- No vague recommendations.
- No filler phrases (e.g., "in today's world", "generally speaking").

LENGTH CONTRACT:
- Each section must be between 100-200 words.
- Executive Summary must not exceed 250 words.

FAIL IF:
- Claims lack evidence.
- Recommendations lack owner or timeline.
- Enforcement language appears.
- Section exceeds word limits.
            """,
            "forbidden_phrases": [
                "it is believed that",
                "we think",
                "generally speaking",
                "it seems like"
            ]
        },

        "RUNBOOK": {
            "toc_required": False,
            "toc_min_sections": 0,
            "tone": "urgent, operational, action-focused",
            "voice": "second-person imperative - direct commands",
            "format": "incident flow: detect → assess → act → verify → escalate",
            "avg_section_words": "300-500",
            "rules": """
STRICT RUNBOOK DOCUMENT RULES:

MUST DO:
- Write for someone under pressure during an incident
- Every section starts with a severity/urgency indicator
  Format: " SEVERITY: [P0/P1/P2/P3] | SLA: [X minutes to resolve]"
- Use numbered action steps with bash commands where applicable
  Format:
  1. ACTION: [What to do]
     RUN: `command here`
     EXPECT: [What successful output looks like]
     IF FAILS: [What to do next]
- Include an Immediate Actions section (first 5 minutes)
- Include an Escalation Matrix table with contacts and when to escalate
- Include Rollback procedure for every resolution step
- Include Post-Resolution checklist
- Every diagnostic step must include the actual command

MUST NOT:
- Write long paragraphs of context or background
- Use formal legal language
- Add policy references
- Write anything that takes longer than 10 seconds to read
- Use vague instructions ("check the system")
            """,
            "forbidden_phrases": [
                "please ensure",
                "it is recommended",
                "you may want to",
                "consider reviewing"
            ]
        },

        "TEMPLATE": {
            "toc_required": False,
            "toc_min_sections": 0,
            "tone": "neutral, instructional, structured",
            "voice": "second-person instructional",
            "format": "labeled sections with [PLACEHOLDER] fields",
            "avg_section_words": "100-200",
            "rules": """
STRICT TEMPLATE DOCUMENT RULES:

TEMPLATE DOCUMENT — STRUCTURED PLACEHOLDER CONTRACT

OUTPUT MODE: REUSABLE BLANK TEMPLATE

STRUCTURE CONTRACT:
- Content must remain a blank reusable template.
- Use [UPPERCASE_PLACEHOLDER] format only.
- Mark required fields as [REQUIRED: FIELD_NAME].
- Mark optional fields as [OPTIONAL: FIELD_NAME].
- Do NOT include real data.
- Do NOT include narrative examples.
- Do NOT include explanatory paragraphs.

LANGUAGE CONTRACT:
- Use neutral instructional tone.
- Keep field explanations concise (maximum 2 sentences per field).

PROHIBITED:
- No enforcement language.
- No compliance citations.
- No filled sample data.
- No guidance paragraphs.

FAIL IF:
- Real data appears.
- Policy-style enforcement language appears.
- Example entries are generated.
            """,
            "forbidden_phrases": [
                "you must",
                "it is required that"
            ]
        },

        "HANDBOOK": {
            "toc_required": True,
            "toc_min_sections": 5,
            "tone": "professional, warm, inclusive, plain-language",
            "voice": "first-person plural (we, our company, our team)",
            "format": "conversational sections with clear H2/H3 structure",
            "avg_section_words": "400-600",
            "rules": """
STRICT HANDBOOK DOCUMENT RULES:

HANDBOOK DOCUMENT — EMPLOYEE GUIDE CONTRACT

OUTPUT MODE: FINAL EMPLOYEE HANDBOOK CONTENT

STRUCTURE CONTRACT:
- Use clear H2 and H3 structure.
- Include one "Quick Summary" paragraph per section (max 2 sentences).
- Explain both WHAT the policy is and WHY it exists.
- Avoid duplicating content across sections.
- Do NOT repeat detailed enforcement language.
- Do NOT include placeholders or template instructions.

LANGUAGE CONTRACT:
- Use first-person plural voice ("we", "our company").
- Write at 8th-10th grade readability level.
- Use clear and accessible language.
- Replace legal jargon with plain equivalents.
- Avoid intimidating tone.

REPETITION CONTROL:
- Compliance frameworks (SOC 2, GDPR, etc.) may be referenced only once per section.
- Disciplinary language may appear only once in entire handbook.
- Company name may appear maximum twice per section.

LENGTH CONTRACT:
- Each section must be between 250-400 words.
- Avoid long narrative paragraphs (max 5 sentences per paragraph).

PROHIBITED:
- No policy-style legal disclaimers.
- No heavy regulatory citations.
- No template-style placeholders.
- No duplicated explanations.
- No ALL CAPS emphasis.

FAIL IF:
- Enforcement language repeated.
- Section exceeds word limit.
- Legal tone dominates.
- Content duplicates previous section.
            """,
            "forbidden_phrases": [
                "failure to comply will result in immediate termination",
                "as mandated by law",
                "pursuant to",
                "heretofore",
                "aforementioned",
                "notwithstanding"
            ]
        },

        "FORM": {
            "toc_required": False,
            "toc_min_sections": 0,
            "tone": "neutral, concise, instructional",
            "voice": "second-person direct",
            "format": "labeled field groups with input types",
            "avg_section_words": "100-250",
            "rules": """
STRICT FORM DOCUMENT RULES:

FORM DOCUMENT — STRUCTURED DATA CAPTURE CONTRACT

OUTPUT MODE: FINAL FORM STRUCTURE

STRUCTURE CONTRACT:
- Use clearly labeled field groups.
- Every field must specify input type.
- Mark fields as (Required) or (Optional).
- Keep explanations short and precise.

PROHIBITED:
- No long explanatory paragraphs.
- No narrative storytelling.
- No policy-style enforcement.
- No template placeholders beyond defined fields.

FAIL IF:
- Paragraphs exceed 3 sentences.
- Instructional tone dominates.
- Enforcement language appears.
            """,
            "forbidden_phrases": [
                "it is required that you explain",
                "please provide a detailed explanation"
            ]
        },

        "STRATEGY": {
            "toc_required": True,
            "toc_min_sections": 5,
            "tone": "strategic, visionary, data-driven",
            "voice": "first-person plural executive (we, our organization)",
            "format": "situation → objective → initiatives → metrics → timeline",
            "avg_section_words": "100-200",
            "rules": """
STRICT STRATEGY DOCUMENT RULES:

STRATEGY DOCUMENT — EXECUTIVE PLANNING CONTRACT

OUTPUT MODE: FINAL STRATEGIC PLAN

STRUCTURE CONTRACT:
- Follow this order strictly:
  Situation Analysis → Strategic Objectives → Key Initiatives → Metrics → Risks → Governance.
- Each initiative must include:
  Owner | Timeline | Budget | Success Metric.
- Use tables for roadmap and initiative tracking.
- No placeholders. No instructional language.

LANGUAGE CONTRACT:
- Use first-person plural executive voice ("we will", "our objective").
- Use measurable objectives (OKRs or SMART goals).
- Every objective must include a quantifiable metric.
- Avoid generic vision statements.

PROHIBITED:
- No operational step-by-step instructions.
- No legal enforcement language.
- No vague goals ("improve performance").
- No filler strategy phrases ("best in class", "innovative solutions").

LENGTH CONTRACT:
- Sections must be between 100-200 words.
- Objectives must be concise and measurable.

FAIL IF:
- Objectives lack measurable metric.
- Initiative lacks owner or timeline.
- Generic visionary language dominates.
            """,
            "forbidden_phrases": [
                "we should try to",
                "it would be nice if",
                "maybe we could"
            ]
        },

        "PROPOSAL": {
            "toc_required": True,
            "toc_min_sections": 4,
            "tone": "persuasive, professional, solution-focused",
            "voice": "first-person collaborative (we, our team)",
            "format": "problem → solution → value → investment → next steps",
            "avg_section_words": "100-200",
            "rules": """
STRICT PROPOSAL DOCUMENT RULES:

PROPOSAL DOCUMENT — BUSINESS CASE CONTRACT

OUTPUT MODE: FINAL CLIENT-READY PROPOSAL

STRUCTURE CONTRACT:
- Follow this sequence:
  Problem Statement → Proposed Solution → Business Value → Investment → Timeline → Risks → Call to Action.
- Include quantified benefits.
- Include ROI or financial impact where possible.
- Include pricing table if applicable.
- No placeholders. No example instructions.

LANGUAGE CONTRACT:
- Use persuasive but professional tone.
- Focus on business outcomes, not features.
- Quantify benefits using percentages, cost savings, revenue impact.
- Avoid internal jargon.

PROHIBITED:
- No vague claims ("world-class", "best in class").
- No guarantees without measurable backing.
- No enforcement language.
- No filler marketing buzzwords.

LENGTH CONTRACT:
- Sections must be between 100-200 words.
- Keep arguments concise and evidence-based.

FAIL IF:
- Benefits are not quantified.
- Pricing is vague.
- Call to action is missing.
- Overly promotional tone appears.
            """,
            "forbidden_phrases": [
                "best-in-class",
                "world-class",
                "synergy",
                "leverage our core competencies"
            ]
        }
    }

    result = behaviors.get((document_type or "").upper())
    if not result:
        return {
        "toc_required": False,
        "toc_min_sections": 0,
        "tone": "professional",
        "voice": "third-person",
        "format": "structured headings",
        "avg_section_words": "300-500",
        "rules": "Maintain professional tone. Use structured headings.",
        "forbidden_phrases": []
        }

    return result


def get_type_behavior_string(document_type: str) -> str:
    """
    Returns the behavior rules as a formatted string for prompt injection.
    Backward compatible with existing code.
    """
    behavior = get_type_behavior(document_type)
    if isinstance(behavior, dict):
        return behavior.get("rules", "")
    return behavior


def should_generate_toc(document_type: str) -> bool:
    """
    Returns True if this document type requires a Table of Contents.
    """
    behavior = get_type_behavior(document_type)
    return behavior.get("toc_required", False)


def get_tone(document_type: str) -> str:
    """Returns the tone specification for this document type."""
    behavior = get_type_behavior(document_type)
    return behavior.get("tone", "professional")


def get_forbidden_phrases(document_type: str) -> list:
    """Returns list of phrases to avoid for this document type."""
    behavior = get_type_behavior(document_type)
    return behavior.get("forbidden_phrases", [])