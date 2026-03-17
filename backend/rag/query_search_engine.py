from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.rag.query_refiner import refine_query


retriever = Retriever()
llm = get_llm()

def calculate_confidence(chunks):

    if not chunks:
        return "LOW"

    scores = [c.get("score", 1.5) for c in chunks]

    avg_score = sum(scores) / len(scores)

    print("scores:", scores)
    print("avg_score:", avg_score)

    if avg_score < 0.5:
        return "HIGH"
    elif avg_score < 1.0:
        return "MEDIUM"
    else:
        return "LOW"
    
# =============== search tool + refine ===============

def answer_question(question, filters=None):
    """
    Perform Retrieval-Augmented Generation (RAG) to answer a user query.

    This function:
    1. Refines the user query using an LLM for better retrieval.
    2. Retrieves relevant document chunks using vector search.
    3. Generates a grounded answer using retrieved context.
    4. Returns answer along with sources and retrieved chunks.

    Args:
        question (str): User input question.
        filters (dict, optional): Metadata filters such as:
            {
                "doc_type": str or None,
                "industry": str or None
            }
    """

    # 🔥 Step 1: Refine query
    refined_question = refine_query(question)

    # 🔍 Step 2: Search using refined query
    chunks = retriever.search(refined_question, k=5, filters=filters)

    context = ""
    sources = []

    for c in chunks:
        context += f"\n{c['text']}\n"
        sources.append(f"{c['doc_title']} → {c['section']}")

    # 🧠 Step 3: Generate answer
    prompt = f"""
Answer the question using the context below.

Context:
{context}

Question:
{refined_question}

Answer ONLY based on the provided context.
Be concise and directly answer the question.
Do not add extra information.

If the answer is not present in the context, say:
"I could not find the answer in the available documents."
"""

    response = llm.invoke([
        SystemMessage(content="You answer questions using company documents."),
        HumanMessage(content=prompt)
    ])

    confidence = calculate_confidence(chunks)

    # 📦 Step 4: Return result
    return {
        "answer": response.content,
        "sources": list(set(sources)),
        "chunks": chunks,
        "refined_query": refined_question,
        "confidence": confidence
    }

