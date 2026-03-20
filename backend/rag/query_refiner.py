"""
Query Refiner Module

This module enhances user queries using an LLM.

Responsibilities:
- Rewrite user query to be more specific and retrieval-friendly
- Improve semantic search performance
- Remove ambiguity in user input

Used by:
- RAG pipeline before retrieval
"""

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
You are a query refinement assistant for enterprise document search.

Rewrite the user question to make it clearer, more specific, 
and optimized for semantic search over company documents.

Rules:
- Keep the original meaning EXACTLY the same
- Expand vague or short queries into complete questions
- Add relevant context words if missing (e.g., policy, process, guidelines)
- DO NOT introduce new information
- DO NOT change intent

User Question:
{question}

Refined Question:
"""

    response = llm.invoke([
        SystemMessage(content="You improve search queries."),
        HumanMessage(content=prompt)
    ])

    return response.content.strip()