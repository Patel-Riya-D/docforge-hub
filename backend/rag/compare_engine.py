from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

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

    # Retrieve chunks for both documents
    chunks_a = retriever.search(doc_a, k=6)
    chunks_b = retriever.search(doc_b, k=6)

    chunks_a = filter_chunks_by_topic(chunks_a, topic)
    chunks_b = filter_chunks_by_topic(chunks_b, topic)

    context_a = "\n".join(
        [f"{c['doc_title']} → {c['section']}: {c['text']}" for c in chunks_a]
    )

    context_b = "\n".join(
        [f"{c['doc_title']} → {c['section']}: {c['text']}" for c in chunks_b]
    )

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

OUTPUT FORMAT:
Document A: {doc_a}
Document B: {doc_b}
--------------------------------------

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


    response = llm.invoke([
        SystemMessage(content="You compare enterprise documents."),
        HumanMessage(content=prompt)
    ])

    return {
        "answer": response.content,
        "chunks_a": chunks_a,
        "chunks_b": chunks_b
    }