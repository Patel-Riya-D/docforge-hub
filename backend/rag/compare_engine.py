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
You are an enterprise document comparison assistant.

Compare the following two documents:

Document A: {doc_a}
Document B: {doc_b}

Topic: {topic if topic else "General comparison"}

Context A:
{context_a}

Context B:
{context_b}

Instructions:
- Compare similarities and differences
- Use only the provided context
- Be clear and structured
- If information is missing, say so
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