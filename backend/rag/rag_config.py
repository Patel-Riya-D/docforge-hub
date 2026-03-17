from backend.generation.llm_provider import get_llm, get_embeddings

def get_rag_components():
    return {
        "llm": get_llm(),
        "embeddings": get_embeddings()
    }