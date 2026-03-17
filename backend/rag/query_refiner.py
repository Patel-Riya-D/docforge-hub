from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

llm = get_llm()


def refine_query(question):
    """
    Improve and expand a user query for better retrieval.

    This function rewrites vague or short queries into
    more detailed and search-friendly queries using LLM.

    Args:
        question (str): Original user query.

    Returns:
        str: Refined query.
    """

    prompt = f"""
Rewrite the user question to make it clearer and more specific 
for searching company documents.

Rules:
- Keep meaning same
- Make it more complete
- Expand short queries
- Do NOT add new information

User Question:
{question}
"""

    response = llm.invoke([
        SystemMessage(content="You improve search queries."),
        HumanMessage(content=prompt)
    ])

    return response.content.strip()