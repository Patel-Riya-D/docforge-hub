from typing import TypedDict, List, Optional


class StateCaseState(TypedDict):
    # User input
    question: str

    # Context
    industry: Optional[str]
    doc_type: Optional[str]
    version: Optional[str]

    # Memory
    history: List[dict]

    # Retrieval
    retrieved_chunks: List[dict]

    sources: List[str]
    is_out_of_domain: bool  

    # Output
    answer: Optional[str]
    confidence: Optional[float]

    # Decision
    needs_clarification: bool
    should_escalate: bool

    # Ticket
    ticket_created: bool

    needs_clarification: bool
    clarification_question: Optional[str]

    intent: str
    doc_set: Optional[List[str]]
    similarity_score: Optional[float]