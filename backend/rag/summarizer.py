from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.utils.rag_cache import (
    generate_summary_cache_key,
    get_rag_cache,
    set_rag_cache
)
from backend.utils.logger import get_logger

logger = get_logger("COMPARE")

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

    try:
        # ---------------- CACHE ----------------
        cache_key = generate_summary_cache_key(query, filters)

        cached = get_rag_cache(cache_key)
        if cached:
            logger.info("✅ CACHE HIT (SUMMARY)")
            return cached

        # ---------------- RETRIEVER ----------------
        try:
            chunks = retriever.search(query, k=8, filters=filters)
        except Exception as e:
            logger.error(f"Retriever error: {e}")
            return {
                "summary": "Failed to retrieve document content.",
                "chunks": []
            }

        # ---------------- EMPTY CHECK ----------------
        if not chunks:
            return {
                "summary": "❌ No relevant document found in knowledge base.",
                "chunks": []
            }

        # ---------------- CONTEXT ----------------
        try:
            context = "\n".join([c["text"] for c in chunks])
        except Exception as e:
            logger.error(f"Context build error: {e}")
            context = ""

        # ---------------- PROMPT ----------------
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
        # ---------------- LLM ----------------
        try:
            response = llm.invoke([
                SystemMessage(content="You summarize enterprise documents."),
                HumanMessage(content=prompt)
            ])

            summary = response.content.strip() if response else "No summary generated."

        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {
                "summary": "Summary generation failed due to LLM error.",
                "chunks": chunks
            }

        result = {
            "summary": summary,
            "chunks": chunks
        }

        # ---------------- CACHE SAVE ----------------
        try:
            set_rag_cache(cache_key, result)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

        return result

    except Exception as e:
        logger.error(f"Unexpected error in summarize_document: {e}")

        return {
            "summary": "Unexpected error occurred during summarization.",
            "chunks": []
        }