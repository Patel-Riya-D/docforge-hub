# risk_behavior.py

def get_risk_behavior(risk_level: str) -> str:
    """
    Returns additional generation rules based on document risk level.
    Risk levels: LOW, MEDIUM, HIGH, CRITICAL
    """

    behaviors = {

        "LOW": """
RISK LEVEL: LOW
- Standard professional language
- No special legal disclaimers required
- No mandatory legal review statements
- Standard formatting acceptable
        """,

        "MEDIUM": """
RISK LEVEL: MEDIUM
- Include a note that policies may be updated
- Reference relevant regulatory context where applicable
- Include version control and review date
- Recommend manager review before implementation
        """,

        "HIGH": """
RISK LEVEL: HIGH — APPLY THESE CONTROLS:

1. LEGAL DISCLAIMER: Include at section start:
   "This section constitutes a binding policy requirement.
    All employees are subject to this policy from their start date."

2. COMPLIANCE REFERENCE: Reference ONE relevant framework per section
   (SOC 2, GDPR, EEOC, FLSA — whichever is most relevant)
   Do NOT repeat the same framework more than once in the document.

3. ENFORCEMENT LANGUAGE: Every HIGH-risk section must state:
   "Violations of this policy may result in disciplinary action
    up to and including termination of employment."
   BUT: Include this statement ONCE per document, not per section.

4. REVIEW REQUIREMENT: End section with:
   "This policy is reviewed annually by [Legal/HR/Compliance team]."

5. PRECISION: No vague language.
   Replace: "appropriate measures" → specific measures
   Replace: "as needed" → specific trigger conditions
   Replace: "management discretion" → named role with authority
        """,

        "CRITICAL": """
RISK LEVEL: CRITICAL — MAXIMUM CONTROLS:

1. MANDATORY LEGAL REVIEW NOTICE:
   Every CRITICAL section must begin with:
    "IMPORTANT: This section contains legally binding requirements.
    Review by qualified legal counsel is mandatory before distribution."

2. ZERO AMBIGUITY RULE:
   Every requirement must be:
   - Measurable (specific numbers, dates, thresholds)
   - Attributable (named role responsible)
   - Verifiable (how compliance is confirmed)
   - Enforceable (consequence if violated)

3. COMPLIANCE CITATIONS:
   Cite specific regulatory sections where applicable:
   Format: "[Requirement] per [Law/Standard], [Section]"
   Example: "Retained for 7 years per SOX Section 802"

4. APPROVAL CHAIN:
   Include: "Approved by: [CISO/Legal/CEO/Board] — [Date]"

5. INCIDENT REPORTING:
   Every CRITICAL section must include:
   "Report violations immediately to [role] and [backup role].
    Do not attempt to resolve without proper authorization."
        """
    }

    return behaviors.get(risk_level.upper(), behaviors["MEDIUM"])