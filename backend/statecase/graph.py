from langgraph.graph import StateGraph, END
from backend.statecase.models import StateCaseState
from backend.rag.query_search_engine import answer_question as rag_query


def clarity_node(state: StateCaseState):
    question = state["question"]

    # 🔥 simple rule (we improve later)
    if len(question.split()) < 3 or "create" in question.lower():
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

    print("GRAPH NODE SOURCES:", state["sources"])

    return state


# ---------------- NODE 2: DECISION ----------------
def decision_node(state):
    confidence = state.get("confidence", 0)
    chunks = state.get("retrieved_chunks", [])
    sources = state.get("sources", [])

    # 🔥 semantic relevance check
    has_relevance = len(chunks) > 0

    # 🔥 strong retrieval signal
    strong_match = any(c.get("score", 0) > 0.6 for c in chunks)

    if (confidence < 40 or not sources) and has_relevance and strong_match:
        state["should_escalate"] = True
    else:
        state["should_escalate"] = False

    return state

# ---------------- NODE 3: ANSWER ----------------

def answer_node(state):
    state["sources"] = state.get("sources", [])
    return state

# ---------------- NODE 4: ESCALATE ----------------
def escalate_node(state):
    state["answer"] = "⚠️ I couldn't find a reliable answer."
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
