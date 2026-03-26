from langgraph.graph import StateGraph, END
from backend.statecase.models import StateCaseState
from backend.rag.query_search_engine import answer_question as rag_query
from backend.statecase.ticketing import create_ticket


def clarity_node(state: StateCaseState):
    question = state["question"]

    # 🔥 simple rule (we improve later)
    if len(question.split()) < 4:
        state["needs_clarification"] = True
        state["clarification_question"] = "Can you provide more details? (e.g., industry, document type)"
    else:
        state["needs_clarification"] = False

    return state

def clarify_node(state: StateCaseState):
    state["answer"] = state["clarification_question"]
    return state

# ---------------- NODE 1: RETRIEVE ----------------
def retrieve_node(state: StateCaseState):
    history = state.get("history", [])

    #  include last 2 messages for context
    history_text = "\n".join([
        f"{h['role']}: {h['message']}"
        for h in history[-2:]
    ])

    question = f"{history_text}\nUser: {state['question']}"

    filters = {
        "doc_type": state.get("doc_type"),
        "industry": state.get("industry"),
        "version": state.get("version")
    }

    result = rag_query(question, filters)

    state["retrieved_chunks"] = result.get("chunks", [])
    state["answer"] = result.get("answer")
    state["confidence"] = result.get("confidence_score", 0)
    state["sources"] = result.get("sources", [])
    state["similarity_score"] = result.get("similarity_score", None)

    print("GRAPH NODE SOURCES:", state["sources"])
    print("SIM FROM RAG:", result.get("similarity_score"))

    return state

# ---------------- NODE 2: DECISION ----------------
def decision_node(state):
    state["is_out_of_domain"] = False

    confidence = state.get("confidence", 0)
    chunks = state.get("retrieved_chunks", [])
    answer = state.get("answer", "").lower()
    similarity = state.get("similarity_score")

    if similarity is None:
        print("⚠️ similarity missing → fallback")
        similarity = 999
    
    if "currently" in state["question"].lower() or "who" in state["question"].lower():
        state["should_escalate"] = True
        return state

    no_answer_detected = any(
        phrase in answer for phrase in [
            "could not find",
            "not available",
            "no information"
        ]
    )

    print("SIMILARITY:", similarity)

    # ✅ TRUE OUT-OF-DOMAIN (based on similarity)
    if similarity > 1.1:
        state["is_out_of_domain"] = True
        state["should_escalate"] = False
        state["answer"] = "This question is outside the scope of available documents."
        state["sources"] = []
        return state

    # ⚠️ NO ANSWER → ESCALATE
    if no_answer_detected:
        state["should_escalate"] = True
        return state

    # ⚠️ WEAK MATCH → ESCALATE
    if similarity > 0.9:
        state["should_escalate"] = True
        return state

    # ⚠️ VERY LOW CONFIDENCE → ESCALATE
    if confidence < 45:
        state["should_escalate"] = True
        return state

    # ✅ GOOD ANSWER
    state["should_escalate"] = False
    return state
# ---------------- NODE 3: ANSWER ----------------

def answer_node(state):
    state["sources"] = state.get("sources", [])
    return state

# ---------------- NODE 4: ESCALATE ----------------
def escalate_node(state):

    if state.get("is_out_of_domain", False):
        state["answer"] = "This question is outside the scope of available documents."
        return state

    status, ticket_id = create_ticket(
        question=state["question"],
        context=state.get("retrieved_chunks", []),
        filters={
            "doc_type": state.get("doc_type"),
            "industry": state.get("industry"),
            "version": state.get("version")
        },
        confidence=state.get("confidence", 0),
        history=state.get("history", []),
        sources=state.get("sources", []),
    )

    if status == "created":
        state["answer"] = "⚠️ I couldn't find a reliable answer. A support ticket has been created."
    elif status == "exists":
        state["answer"] = "⚠️ I couldn't find a reliable answer. A ticket already exists for this query."
    else:
        state["answer"] = "⚠️ I couldn't find a reliable answer. Ticket creation failed."

    return state

def intent_node(state):
    question = state["question"].lower()

    if "create" in question or "generate" in question:
        state["intent"] = "generation"
    else:
        state["intent"] = "query"

    return state

# ---------------- BUILD GRAPH ----------------
def build_graph():

    graph = StateGraph(StateCaseState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("decision", decision_node)
    graph.add_node("clarity", clarity_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("intent",intent_node)
    graph.add_node("answer", answer_node)
    graph.add_node("escalate", escalate_node)

    # Flow
    graph.set_entry_point("intent")

    graph.add_edge("intent","clarity")

    graph.add_edge("retrieve", "decision")

    graph.add_conditional_edges(
        "decision",
        lambda state: "escalate" if state["should_escalate"] else "answer"
    )
    graph.add_conditional_edges(
        "clarity",
        lambda state: "clarify" if state["needs_clarification"] else "retrieve"
    )
    graph.add_edge("clarify", END)
    graph.add_edge("answer", END)
    graph.add_edge("escalate", END)

    return graph.compile()
