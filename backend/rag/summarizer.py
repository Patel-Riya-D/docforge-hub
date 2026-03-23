from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.utils.rag_cache import (
    generate_summary_cache_key,
    get_rag_cache,
    set_rag_cache
)

retriever = Retriever()
llm = get_llm()


def summarize_document(query, filters=None):
    """
    Generate a concise summary of a document or topic using RAG.

    This function:
    1. Retrieves relevant chunks based on query.
    2. Uses LLM to summarize content into key points.
    3. Returns summary along with sources.

    Args:
        query (str): Document name or topic to summarize.
        filters (dict, optional): Metadata filters.

    """
    cache_key = generate_summary_cache_key(query, filters)

    cached = get_rag_cache(cache_key)
    if cached:
        print("✅ CACHE HIT (SUMMARY)")
        return cached

    #  Retrieve relevant chunks
    chunks = retriever.search(query, k=8, filters=filters)

    # 🔥 ADD THIS CHECK
    if not chunks:
        return {
            "summary": "❌ No relevant document found in knowledge base.",
            "chunks": []
        }

    context = "\n".join([c["text"] for c in chunks])

    prompt = f"""
You are an enterprise document summarization assistant.

Summarize the following company document content.

Rules:
- ONLY summarize using the provided context
- DO NOT add external information
- DO NOT infer missing details
- DO NOT hallucinate
- Keep it concise and structured
- Use bullet points
- Focus on key policies, processes, and important details

Content:
{context}

Summary:
"""

    response = llm.invoke([
        SystemMessage(content="You summarize enterprise documents."),
        HumanMessage(content=prompt)
    ])

    result =  {
        "summary": response.content,
        "chunks": chunks
    }

    set_rag_cache(cache_key, result)

    return result 