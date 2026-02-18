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
            "avg_section_words": "200-300",
            "rules": """
STRICT POLICY DOCUMENT RULES:

MUST DO:
- Write in formal, legal, authoritative tone
- Every section uses H3 numbered headings (e.g., 3.1, 3.2)
- Use declarative mandatory language: MUST, SHALL, IS REQUIRED, IS PROHIBITED
- Include Definitions section with bolded terms
- Include Scope section with explicit inclusions AND exclusions
- Include Roles & Responsibilities as a table
- Include Compliance & Enforcement section
- Include Exceptions process
- End every policy with Revision History table
- Reference compliance frameworks (GDPR, SOC 2, EEOC, etc.) where relevant

MUST NOT:
- Use conversational language ("you might want to...", "it's a good idea to...")
- Use step-by-step numbered operational instructions (that is SOP format)
- Use first-person ("I", "we think")
- Write vague requirements ("as appropriate", "when needed")
- Add narrative storytelling or cultural context
- Use bullet points as the primary content format
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
            "avg_section_words": "200-300",
            "rules": """
STRICT SOP DOCUMENT RULES:

MUST DO:
- Write every action as a numbered step with a clear verb
  Format: "Step N: [ACTION VERB] + [WHAT] + [HOW/WHERE]"
  Example: "Step 3: Submit the completed form to HR via BambooHR by 5 PM Friday"
- Each step must have ONE action only (no compound steps)
- Add verification checkpoint after every 3-5 steps
  Format: "✓ Verify: [what to check to confirm step completed correctly]"
- Include Prerequisites section BEFORE the procedure
- Include Roles & Responsibilities table (who does what)
- Include Troubleshooting section at the end
- Include Rollback/Escalation path if process fails
- Use tables for decision matrices
- Use checkboxes [ ] for checklists

MUST NOT:
- Use passive voice ("the form should be submitted" → "Submit the form")
- Write paragraphs of narrative text inside procedure steps
- Combine multiple actions in one step
- Use legal enforcement language (that belongs in Policy)
- Skip verification steps for critical actions
- Write steps without specifying who is responsible
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

MUST DO:
- Start with an Executive Summary (max 300 words)
- Every claim must be supported by data, metrics, or evidence
- Use tables to present comparative data
- Use this structure for each finding:
  Finding → Evidence → Analysis → Implication
- Include specific metrics with baseline and target
- Recommendations must be actionable with owner, timeline, and expected outcome
- Use charts/graphs descriptions where visual data is relevant
- Conclude with Next Steps and Decision Required

MUST NOT:
- Write policy or procedure language
- Use enforcement language (SHALL, MUST, IS PROHIBITED)
- Add opinions without data backing
- Write step-by-step operational instructions
- Add cultural or narrative content
- Leave recommendations vague ("improve the process")
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
  Format: "⚠️ SEVERITY: [P0/P1/P2/P3] | SLA: [X minutes to resolve]"
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

MUST DO:
- Every variable field uses [UPPERCASE_PLACEHOLDER] format
  Example: [COMPANY_NAME], [EFFECTIVE_DATE], [EMPLOYEE_NAME]
- Mark required fields: [REQUIRED: FIELD_NAME]
- Mark optional fields: [OPTIONAL: FIELD_NAME]
- Include instructions in italics above each section:
  _Instructions: Describe [X] in 2-3 sentences. Include [Y]._
- Provide a filled-in example for each major section
- Use tables for structured data fields
- Include a "How to Use This Template" box at the top

MUST NOT:
- Write completed content (leave placeholders)
- Add long narrative paragraphs
- Use enforcement language
- Add company-specific details (keep it generic/reusable)
- Generate TOC (templates are not long-form documents)
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

MUST DO:
- Use "we" and "our" to create belonging and inclusivity
- Write at an 8th-10th grade reading level (accessible to all employees)
- Explain the WHY behind every policy, not just the WHAT
  Format: "We have this policy because... | What this means for you is..."
- Use plain language equivalents for legal terms
  Example: "leave of absence" → "time away from work"
- Each section must include a "Quick Summary" box:
  Format: "In short: [1-2 sentence plain language summary]"
- Use employee-friendly examples:
  Format: "For example, if you need to [scenario], here is what to do: [steps]"
- End sections with "Questions? Contact: [HR contact]"
- Use inclusive gender-neutral language throughout
- Link/reference detailed policies for complex topics
  Format: "For full details, see our [Policy Name] Policy."

MUST NOT:
- Repeat detailed enforcement language from Policy documents
  (say "violations may result in disciplinary action" ONCE total, not per section)
- Use heavy regulatory citations in body text
  (put compliance references in footnotes only)
- Use intimidating legal language that creates fear
- Repeat SOC 2, GDPR, or other compliance terms more than once per section
- Center-align body text
- Use ALL CAPS for emphasis (use bold instead)
- Duplicate content across sections
- Use H2 heading more than once per section
- Add section heading INSIDE the section content again
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

MUST DO:
- Use field groups with clear labels
- Mark every field as: (Required) or (Optional)
- Specify input type for each field:
  Types: [Text] [Dropdown] [Checkbox] [Date] [Signature] [Textarea]
- Include a form header with:
  Form ID, Version, Purpose, Submission Instructions
- Use tables for multi-column field layouts
- Include signature and date block at the end
- Include a Privacy Notice for forms collecting personal data

MUST NOT:
- Write long explanatory paragraphs
- Add narrative content
- Generate TOC
- Use enforcement language
- Add more than 2 sentences of instruction per field
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

MUST DO:
- Start with a Situation Analysis (where we are)
- Define clear OKRs or SMART objectives
- Include competitive/market context
- Every initiative must have: Owner, Timeline, Budget, Success Metric
- Use tables for roadmaps and initiative tracking
- Include a Risk & Mitigation section
- End with Governance (how progress will be reviewed)

MUST NOT:
- Write operational step-by-step instructions (SOP territory)
- Use legal enforcement language
- Add detailed policy content
- Write more than 3 sentences without a supporting data point
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

MUST DO:
- Lead with the business problem, not the solution
- Quantify all benefits with specific metrics
- Include a clear ROI or value statement
- Use a Pricing/Investment table with line items
- Include a Timeline with milestones
- End with a specific Call to Action and decision deadline
- Include an Alternatives Considered section

MUST NOT:
- Use internal jargon without explanation
- Make promises that cannot be guaranteed
- Skip the risk section
- Leave pricing vague
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