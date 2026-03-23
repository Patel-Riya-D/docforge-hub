from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.utils.rag_cache import (
    generate_compare_cache_key,
    get_rag_cache,
    set_rag_cache
)
from backend.utils.logger import get_logger

logger = get_logger("COMPARE")

retriever = Retriever()
llm = get_llm()

def filter_chunks_by_topic(chunks, topic):
    if not topic:
        return chunks

    topic = topic.lower()

    filtered = [
        c for c in chunks
        if topic in c["text"].lower()
        or topic in c["section"].lower()
    ]

    return filtered if filtered else chunks  # fallback if nothing found

from backend.utils.logger import get_logger

logger = get_logger("COMPARE")


def compare_documents(doc_a, doc_b, topic=""):
    """
    Compare two documents based on retrieved content.

    This function:
    1. Retrieves relevant chunks for both documents.
    2. Uses LLM to compare similarities and differences.
    3. Returns structured comparison output with sources.

    Args:
        doc_a (str): First document name or query.
        doc_b (str): Second document name or query.
        topic (str, optional): Specific comparison focus (e.g., "attendance").
    """

    try:
        # ---------------- CACHE ----------------
        cache_key = generate_compare_cache_key(doc_a, doc_b, topic)

        cached = get_rag_cache(cache_key)
        if cached:
            logger.info("✅ CACHE HIT (COMPARE)")
            return cached

        # ---------------- RETRIEVAL ----------------
        query_a = f"{doc_a} {topic}" if topic else doc_a
        query_b = f"{doc_b} {topic}" if topic else doc_b

        try:
            chunks_a = retriever.search(query_a, k=6)
            chunks_b = retriever.search(query_b, k=6)
        except Exception as e:
            logger.error(f"Retriever error: {e}")
            return {
                "answer": "Failed to retrieve document content.",
                "chunks_a": [],
                "chunks_b": []
            }

        # ---------------- FILTER ----------------
        try:
            chunks_a = filter_chunks_by_topic(chunks_a, topic)
            chunks_b = filter_chunks_by_topic(chunks_b, topic)
        except Exception as e:
            logger.warning(f"Filtering error: {e}")

        # ---------------- CONTEXT ----------------
        try:
            context_a = "\n".join(
                [f"{c['doc_title']} → {c['section']}: {c['text']}" for c in chunks_a]
            )

            context_b = "\n".join(
                [f"{c['doc_title']} → {c['section']}: {c['text']}" for c in chunks_b]
            )
        except Exception as e:
            logger.error(f"Context building error: {e}")
            context_a, context_b = "", ""

        # ---------------- PROMPT ----------------
        prompt = f"""
You are a senior enterprise document analyst.
Your task is to compare two documents using ONLY the provided context.

Document A: {doc_a}
Document B: {doc_b}

Topic: {topic if topic else "General comparison"}

Context A:
{context_a}
Context B:
{context_b}

-------------------------------------------

STRICT RULES:
- Use ONLY the given context
- Do NOT hallucinate or invent facts
- If BOTH documents lack information for a dimension → SKIP that dimension
- If ONE document lacks explicit mention:
  → Infer its focus based on available content
  → Do NOT write "Not specified"
  → Instead explain how its focus differs
- Prefer semantic comparison over literal matching
- Focus on business purpose, structure, and functional differences

--------------------------------------

Output Format:

1. Key Similarities
- Focus on meaningful overlaps (avoid generic statements)
2. Critical Differences
- ONLY include dimensions supported by context
- Use format:
- [Dimension]:
  A → ...
  B → ...
3. Executive Summary (2-3 lines)
Highlight the core difference in purpose and usage.

"""


        # ---------------- LLM CALL ----------------
        try:
            response = llm.invoke([
                SystemMessage(content="You compare enterprise documents."),
                HumanMessage(content=prompt)
            ])

            answer = response.content.strip() if response else "No response generated."

        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {
                "answer": "Comparison could not be generated due to LLM error.",
                "chunks_a": chunks_a,
                "chunks_b": chunks_b
            }

        # ---------------- RESULT ----------------
        result = {
            "answer": answer,
            "chunks_a": chunks_a,
            "chunks_b": chunks_b
        }

        # ---------------- CACHE SAVE ----------------
        try:
            set_rag_cache(cache_key, result)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

        return result

    except Exception as e:
        logger.error(f"Unexpected error in compare_documents: {e}")

        return {
            "answer": "Unexpected error occurred during comparison.",
            "chunks_a": [],
            "chunks_b": []
        }