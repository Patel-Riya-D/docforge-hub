from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.utils.rag_cache import (
    generate_summary_cache_key,
    get_rag_cache,
    set_rag_cache
)
from backend.utils.logger import get_logger

logger = get_logger("SUMMARY")

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

        # ---------------- HANDLE LATEST VERSION ----------------
        if filters and filters.get("version") == "latest":

            # Find max version from chunks
            versions = [int(c.get("version", 0)) for c in chunks if c.get("version")]

            if not versions:
                return {
                    "summary": "❌ No version information found.",
                    "chunks": []
                }

            latest_version = max(versions)

            chunks = [
                c for c in chunks if int(c.get("version", 0)) == latest_version
            ]
        # ---------------- STRICT VERSION CHECK ----------------
        if filters and filters.get("version") and filters["version"] not in ["All", "latest"]:

            requested_version = str(filters["version"])

            # Check if any chunk matches requested version
            valid_chunks = [
                c for c in chunks if str(c.get("version")) == requested_version
            ]

            if not valid_chunks:
                return {
                    "summary": f"❌ No document found for version {requested_version}.",
                    "chunks": []
                }

            # Use only valid version chunks
            chunks = valid_chunks
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