from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

retriever = Retriever()
llm = get_llm()


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
    chunks_a = retriever.search(doc_a + " " + topic, k=4)
    chunks_b = retriever.search(doc_b + " " + topic, k=4)

    context_a = "\n".join(
        [f"{c['doc_title']} → {c['section']}: {c['text']}" for c in chunks_a]
    )

    context_b = "\n".join(
        [f"{c['doc_title']} → {c['section']}: {c['text']}" for c in chunks_b]
    )

    prompt = f"""
You are a senior enterprise policy analyst.

Your task is to compare two documents using ONLY the provided context.

Document A: {doc_a}
Document B: {doc_b}

Topic: {topic if topic else "General comparison"}

Context A:
{context_a}

Context B:
{context_b}

STRICT RULES:
- Use ONLY the given context
- Do NOT assume or hallucinate
- If information for a dimension is missing in BOTH documents, DO NOT include that dimension
- If information is present in one document but missing in the other, write "Not specified" for the missing side
- Be precise, analytical, and professional

OUTPUT FORMAT:

Document A: {doc_a}
Document B: {doc_b}

--------------------------------------

1. Key Similarities (Concise Insights)
- Focus on meaningful overlaps (not generic statements)

2. Critical Differences (Structured)
- ONLY include dimensions that are explicitly supported by the context
- DO NOT force all dimensions
- Use format:

- [Dimension]: 
  A → ... 
  B → ...

3. Executive Summary (2-3 lines)
Provide a high-level comparison highlighting the core difference in purpose.
"""

    response = llm.invoke([
        SystemMessage(content="You compare enterprise documents."),
        HumanMessage(content=prompt)
    ])

    sources = list(set(
        [f"{c['doc_title']} → {c['section']}" for c in chunks_a] +
        [f"{c['doc_title']} → {c['section']}" for c in chunks_b]
    ))

    return {
        "answer": response.content,
        "sources": sources,
        "chunks_a": chunks_a,
        "chunks_b": chunks_b
    }