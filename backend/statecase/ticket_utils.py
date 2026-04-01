import json
from backend.generation.llm_provider import get_llm

llm = get_llm()


def classify_ticket_llm(question: str):
    """
    Classify a user query into ticket metadata using LLM.

    The function prompts an LLM to categorize the query into:
    - Category (Policy Missing, Data Request, General Query)
    - Owner (HR, Finance, IT, General Support)
    - Priority (High, Medium, Low)

    Args:
        question (str): User query

    Returns:
        dict:
            {
                "category": str,
                "owner": str,
                "priority": str
            }

    Behavior:
        - Uses LLM for intelligent classification
        - Extracts JSON safely from LLM response
        - Falls back to rule-based classification on failure
    """
    prompt = f"""
You are a support ticket classifier.

Classify the user query into:

1. Category: [Policy Missing, Data Request, General Query]
2. Owner: [HR Team, Finance Team, IT Team, General Support]
3. Priority: [High, Medium, Low]

Rules:
- HR → leave, employee, policy
- Finance → budget, cost
- IT → system, access, security
- Data Request → asks for current data
- High priority → urgent, critical issues

Return ONLY valid JSON (no explanation):

{{
  "category": "...",
  "owner": "...",
  "priority": "..."
}}

Query:
{question}
"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        # 🧠 SAFE JSON PARSE
        import re

        # extract JSON from response
        match = re.search(r'\{.*\}', content, re.DOTALL)

        if match:
            json_str = match.group()
            result = json.loads(json_str)
        else:
            raise ValueError("No JSON found in LLM response")

        return {
            "category": result.get("category", "General Query"),
            "owner": result.get("owner", "General Support"),
            "priority": result.get("priority", "Low")
        }

    except Exception as e:
        print("⚠️ LLM classification failed:", e)
        return classify_ticket_rules(question)


# 🔧 FALLBACK (KEEP YOUR OLD LOGIC)
def classify_ticket_rules(question: str):
    """
    Rule-based fallback for ticket classification.

    Args:
        question (str): User query

    Returns:
        dict:
            {
                "category": str,
                "owner": str,
                "priority": str
            }

    Logic:
        - Keyword-based classification
        - Ensures system reliability when LLM fails
    """
    q = question.lower()

    if any(word in q for word in ["policy", "leave", "process"]):
        category = "Policy Missing"
    elif any(word in q for word in ["who", "current", "data"]):
        category = "Data Request"
    else:
        category = "General Query"

    if any(word in q for word in ["leave", "employee", "hr"]):
        owner = "HR Team"
    elif any(word in q for word in ["budget", "finance"]):
        owner = "Finance Team"
    elif any(word in q for word in ["system", "access", "security"]):
        owner = "IT Team"
    else:
        owner = "General Support"

    if "urgent" in q or "critical" in q:
        priority = "High"
    elif category == "Data Request":
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "category": category,
        "owner": owner,
        "priority": priority
    }


# 🔥 MAIN FUNCTION (USE THIS)
def classify_ticket(question: str):
    """
    Main ticket classification entry point.

    Args:
        question (str): User query

    Returns:
        dict: Ticket metadata (category, owner, priority)

    Notes:
        - Uses LLM-based classification primarily
        - Automatically falls back to rule-based logic if needed
    """
    return classify_ticket_llm(question)