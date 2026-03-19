"""
RAG Query Search Engine

This module implements the core Retrieval-Augmented Generation (RAG) pipeline.

Responsibilities:
- Accept user query and optional metadata filters
- Refine query using LLM for better retrieval
- Perform semantic search using FAISS retriever
- Generate grounded answer using retrieved context
- Attach citations (document title + section)
- Compute confidence score based on similarity
- Use Redis caching to optimize repeated queries

Key Features:
- Query refinement for improved retrieval accuracy
- Context-aware answer generation with anti-hallucination prompt
- Metadata filtering (doc_type, industry)
- Redis-based caching for performance optimization
- Confidence scoring (HIGH / MEDIUM / LOW)

Used by:
- FastAPI endpoint: /documents/rag-query
"""

from backend.rag.retriever import Retriever
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.rag.query_refiner import refine_query
from backend.utils.rag_cache import (
    generate_rag_cache_key,
    get_rag_cache,
    set_rag_cache
)
from backend.utils.logger import get_logger
import time

logger = get_logger("RAG")

retriever = Retriever()
llm = get_llm()

def calculate_confidence(chunks):
    """
    Determine confidence level of retrieved results based on similarity scores.

    Strategy:
    - Uses FAISS distance scores (lower = better match)
    - Selects best (minimum) score among retrieved chunks
    - Maps score to confidence levels:
        HIGH   → strong semantic match
        MEDIUM → partial match
        LOW    → weak or irrelevant match

    Args:
        chunks (list[dict]): Retrieved chunks with 'score' field

    Returns:
        str: One of ["HIGH", "MEDIUM", "LOW"]

    Notes:
    - Designed to give conservative confidence estimates
    - Used to control answer reliability in UI
    """

    if not chunks:
        return "LOW"

    scores = [c.get("score", 1.5) for c in chunks]

    best_score = min(scores)

    print("scores:", scores)
    print("best_score:", best_score)

    if best_score < 0.5:
        return "HIGH"
    elif best_score < 1.0:
        return "MEDIUM"
    else:
        return "LOW"
    
# =============== search tool + refine ===============

def answer_question(question, filters=None):
    """
    Execute end-to-end RAG pipeline for answering user queries.

    Workflow:
    1. Refines the user query using an LLM to improve semantic retrieval.
    2. Generates a Redis cache key based on refined query + filters.
    3. Checks Redis cache:
        - If HIT → returns cached response
        - If MISS → performs retrieval
    4. Retrieves top-k relevant chunks from FAISS vector store.
    5. Constructs context from retrieved chunks.
    6. Generates grounded answer using LLM with strict prompt.
    7. Computes confidence score based on similarity scores.
    8. Stores full response in Redis for future reuse.

    Args:
        question (str): User input query.
        filters (dict, optional): Metadata filters such as:
            {
                "doc_type": str or None,
                "industry": str or None
            }

    Returns:
        dict:
            {
                "answer": str,
                "sources": list[str],
                "chunks": list[dict],
                "refined_query": str,
                "confidence": str,
                "cache_hit": bool
            }

    Notes:
    - Ensures answers are grounded strictly in retrieved context.
    - Prevents hallucination via prompt constraints.
    - Low confidence responses may be overridden.
    """
    start_time = time.time()

    logger.info(f"New query received: {question}")

    # 🔥 Step 1: Refine query
    refined_question = refine_query(question)

    # 🔍 Step 2: Search using refined query
    # 🔑 Generate cache key
    cache_key = generate_rag_cache_key(refined_question, filters)

    # ⚡ Try cache
    # ⚡ Step 2: Try full RAG cache
    cached = get_rag_cache(cache_key)

    if cached:
        if isinstance(cached, dict):
            logger.info("Cache HIT")
            cached["cache_hit"] = True
            return cached
        else:
            logger.warning("Invalid cache format detected")
    else:
        logger.info("Cache MISS")
    
    # 🔍 Step 3: Retrieve
    chunks = retriever.search(refined_question, k=3, filters=filters)

    logger.info(f"Retrieved {len(chunks)} chunks")

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

Answer in exactly ONE short sentence.
Answer ONLY based on the provided context.
Be concise and directly answer the question.
Do not add extra information.

If the answer is not present in the context, say:
"I could not find the answer in the available documents."
"""

    try:
        response = llm.invoke([
            SystemMessage(content="You answer questions using company documents."),
            HumanMessage(content=prompt)
        ])
    except Exception as e:
        logger.error(f"LLM error: {str(e)}")
        raise

    # 🔥 Trim answer
    answer = response.content.strip().split("\n")[0]

    confidence = calculate_confidence(chunks)

    #confidence filter
    if confidence == "LOW":
        answer = "Not Available"

    logger.info(f"Answer generated: {answer}")
    logger.info(f"Confidence: {confidence}")

    # 📦 Step 4: Return result
    result = {
        "answer": answer,
        "sources": list(set(sources)),
        "chunks": chunks,
        "refined_query": refined_question,
        "confidence": confidence,
        "cache_hit": False
    }

    # 💾 Store full response in Redis
    set_rag_cache(cache_key, result)

    end_time = time.time()
    logger.info(f"Total response time: {round(end_time - start_time, 2)} sec")

    return result
