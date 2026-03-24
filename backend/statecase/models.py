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

    # Output
    answer: Optional[str]
    confidence: Optional[float]

    # Decision
    needs_clarification: bool
    should_escalate: bool

    # Ticket
    ticket_created: bool