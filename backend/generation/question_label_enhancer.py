# backend/generation/question_label_enhancer.py

from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

llm = get_llm()

def enhance_label(label: str, document_name: str) -> str:

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