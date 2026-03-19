"""
question_label_enhancer.py

This module enhances raw form field labels into clear, professional,
and actionable enterprise-style questions using LLM.

It is used to improve user experience in DocForge Hub by:
- Converting basic labels into meaningful questions
- Maintaining original intent while improving clarity
- Ensuring consistency across document input forms

Example:
    Input:  "employee name"
    Output: "What is the employee's full name?"

This module helps make form interactions more intuitive and professional.
"""

from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

llm = get_llm()

def enhance_label(label: str, document_name: str) -> str:
    """
    Enhance a raw field label into a professional enterprise question.

    This function uses an LLM to rewrite simple or unclear field labels
    into well-structured, concise, and actionable questions suitable
    for enterprise document forms.

    Args:
        label (str): Original field label (e.g., "employee name").
        document_name (str): Name of the document for contextual clarity.

    Returns:
        str: Improved question string.

    Behavior:
        - Preserves original meaning
        - Improves clarity and specificity
        - Keeps output concise
        - Returns only the final question (no explanation)

    Example:
        Input:
            label = "start date"
            document_name = "Employment Contract"

        Output:
            "What is the employee's start date?"
    """

    prompt = f"""
Rewrite the following document field label into a clear,
professional enterprise question.

Rules:
- Keep original meaning.
- Do not change scope.
- Make it specific and actionable.
- Keep it concise.
- Return only the improved question.

Document: {document_name}
Field: {label}
"""

    response = llm.invoke([
        SystemMessage(content="You improve enterprise form questions."),
        HumanMessage(content=prompt)
    ])

    return response.content.strip()