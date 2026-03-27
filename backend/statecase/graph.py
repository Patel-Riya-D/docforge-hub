from langgraph.graph import StateGraph, END
from backend.statecase.models import StateCaseState
from backend.rag.query_search_engine import answer_question as rag_query
from backend.statecase.ticketing import create_ticket
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage


# ────────────────────────────────────────────────────────────────────
# HELPER: LLM CALL
# ────────────────────────────────────────────────────────────────────
def _llm(system: str, user: str) -> str:
    llm = get_llm()
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    return llm.invoke(messages).content.strip()


# ────────────────────────────────────────────────────────────────────
# NODE: INTENT  (LLM-based, no hardcoded keywords)
# Classifies into: "generation" | "query" | "unclear"
# ────────────────────────────────────────────────────────────────────
INTENT_SYSTEM = """
You are an intent classifier for a document-management assistant.

Classify the user's message into exactly one of these intents:
  - generation : The user wants to CREATE, GENERATE, DRAFT, MAKE, PRODUCE,
                 BUILD, or WRITE a document, report, SOP, template, policy,
                 letter, or any other artifact. This includes bare imperative
                 commands like "create document", "generate SOP", "make report",
                 "draft policy" — even with no extra detail provided.
  - query      : The user wants to RETRIEVE information, get an explanation,
                 find a procedure, or understand something from existing docs.
  - unclear    : Cannot be classified as generation or query even after
                 careful consideration.

Prioritisation rules (apply in order):
  1. If the message starts with or contains a creation verb (create, generate,
     make, draft, write, build, produce, prepare) followed by any document
     noun (document, doc, report, SOP, policy, letter, template, guide,
     handbook, form, plan, checklist) → ALWAYS return "generation",
     regardless of how short or vague the message is.
  2. If the message is clearly asking for information or explanation → "query".
  3. If genuinely ambiguous after rules 1 and 2 → "unclear".

Reply with ONLY the single word: generation | query | unclear
No punctuation, no explanation, no extra words.
""".strip()


def intent_node(state: StateCaseState):
    question = state["question"]
    try:
        intent = _llm(INTENT_SYSTEM, question).lower()
        if intent not in ("generation", "query", "unclear"):
            intent = "query"
    except Exception as e:
        print(f"⚠️  intent_node LLM error: {e} → defaulting to 'query'")
        intent = "query"

    print(f"[intent] '{question}' → {intent}")
    state["intent"] = intent
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: CLARITY
#
# Decides if the question has an identifiable subject to search for.
# Rule-based prompt — no hardcoded query examples.
#
# "vague" = subject is unidentifiable (no topic to search)
# "clear" = subject exists → flow to retrieval
#
# Real-time / live-data questions (pending issues, active incidents)
# are CLEAR — they have a subject. Whether the doc can answer them
# is decided later in decision_node → escalate → ticket.
# ────────────────────────────────────────────────────────────────────
CLARITY_SYSTEM = """
You are a query clarity checker for a document-management assistant.

Your ONLY job: decide whether this question has an identifiable subject
that a retrieval system could attempt to search for.

You are NOT responsible for deciding:
  - Whether the answer exists in the documents
  - Whether the question is in scope or out of scope
  - Whether the data is real-time or historical
  Those are handled by other parts of the system. Ignore them completely.

DEFAULT to "clear". Return "vague" only when the subject is genuinely
unidentifiable — no retrieval system could know what to look for.

VAGUE — the subject is unidentifiable:
  - A document type is named (report, SOP, policy, document, handbook)
    but NO topic is attached. The user points at a container, not content.
  - The question is a bare word, phrase, or fragment with no topic.
  - The question asks about something that REQUIRES a missing qualifier
    (role, level, department) to have any single meaningful answer,
    AND that qualifier is completely absent from the question.

CLEAR — a subject exists and can be searched:
  - A specific topic, concept, process, system, regulation, team,
    or named thing appears anywhere in the question.
  - A question word (what, which, how, why, when, who, where) is
    followed by a recognisable subject — even a broad one.
  - The question asks about current state, pending items, active
    issues, compliance status, or real-time data. These questions
    have a clear subject — current/pending/active just describes
    the state being asked about, not vagueness.
  - The question names a person, technology, acronym, or term —
    even one that is unknown or off-topic.

Internal reasoning steps (do NOT output these):
  Step 1: Remove question words and helper verbs.
  Step 2: What noun or concept remains as the core subject?
  Step 3: Could a search engine use that subject to find content?
          If yes → clear. If subject is empty or only "document" → vague.

Reply with ONLY one word: vague | clear
No punctuation, no explanation, no reasoning in your output.
""".strip()


def clarity_node(state: StateCaseState):
    question    = state["question"]
    tokens      = question.split()
    intent      = state.get("intent", "query")
    has_filters = bool(
        state.get("doc_type") or state.get("industry") or state.get("version")
    )

    needs_clarification    = False
    clarification_question = ""

    if intent == "unclear":
        needs_clarification    = True
        clarification_question = (
            "I'm not sure what you're looking for. Could you clarify whether "
            "you'd like me to find information from our documents, or create/"
            "generate something? Any extra context (industry, document type, "
            "topic) would help too."
        )

    elif intent == "generation" and len(tokens) <= 6 and not has_filters:
        needs_clarification    = True
        clarification_question = (
            "I'd be happy to help generate that. Could you provide a bit more detail?\n"
            "  • Which industry or department is this for?\n"
            "  • What specific topic or process should it cover?\n"
            "  • Any particular format or template to follow?"
        )

    elif intent == "query":
        try:
            clarity_verdict = _llm(CLARITY_SYSTEM, question).lower()
            print(f"[clarity] '{question}' → {clarity_verdict}")
        except Exception as e:
            print(f"⚠️  clarity_node LLM error: {e} → assuming clear")
            clarity_verdict = "clear"

        if clarity_verdict == "vague":
            needs_clarification    = True
            clarification_question = (
                "Could you provide a bit more context so I can find the right information?\n"
                "For example:\n"
                "  • Which department, role, or document type are you referring to?\n"
                "  • Is there a specific process, policy, or topic you have in mind?"
            )

    state["needs_clarification"]    = needs_clarification
    state["clarification_question"] = clarification_question
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: CLARIFY — returns clarification question and exits
# ────────────────────────────────────────────────────────────────────
def clarify_node(state: StateCaseState):
    state["answer"] = state["clarification_question"]
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: RETRIEVE
# ────────────────────────────────────────────────────────────────────
def retrieve_node(state: StateCaseState):
    history      = state.get("history", [])
    history_text = "\n".join(
        f"{h['role']}: {h['message']}" for h in history[-2:]
    )
    question = (
        f"{history_text}\nUser: {state['question']}"
        if history_text else state["question"]
    )

    filters = {
        "doc_type": state.get("doc_type"),
        "industry": state.get("industry"),
        "version":  state.get("version"),
    }

    result = rag_query(question, filters)

    state["retrieved_chunks"] = result.get("chunks", [])
    state["answer"]           = result.get("answer")
    state["confidence"]       = result.get("confidence_score", 0)
    state["sources"]          = result.get("sources", [])
    state["similarity_score"] = result.get("similarity_score", None)

    return state


# ────────────────────────────────────────────────────────────────────
# LLM DOMAIN CHECK
#
# Called in decision_node for borderline similarity (0.7–1.1).
# Determines if a question is about company-internal knowledge
# OR about general world knowledge (tech concepts, named individuals).
#
# CRITICAL DESIGN RULE:
#   Real-time / live-data questions (pending issues, active incidents,
#   current compliance status) are ALWAYS in-domain. The company
#   DOES have policies and procedures about these topics — the static
#   docs just may not have the current state. That is an answerability
#   problem, not a domain problem → handled by escalate_node (ticket).
#
#   Only flag out-of-domain when the question is about something the
#   company's documents would NEVER cover regardless of their content.
# ────────────────────────────────────────────────────────────────────
DOMAIN_CHECK_SYSTEM = """
You are a domain classifier for a document-management assistant.

The assistant holds internal company documents: SOPs, HR policies,
security policies, handbooks, offer letter templates, compliance
checklists, technical guides, deployment procedures, and audit records.

Your job: decide if the user's question is about company-internal
knowledge OR about general world knowledge.

IN-DOMAIN — the question is about company-internal knowledge:
  - It asks about how the company operates, what its rules are,
    what its procedures say, or what its internal records contain.
  - It asks about company processes, HR policies, security policies,
    compliance requirements, incident handling, access controls,
    audit findings, or operational status within the company.
  - It asks about the current state of something the company manages:
    pending issues, active incidents, open tickets, compliance gaps.
    These ARE in-domain — the company has documents about these topics
    even if the static docs don't have today's live data.
  - The answer would come from an internal company document,
    even if that document doesn't currently have the specific answer.

OUT-OF-DOMAIN — the question is about general world knowledge:
  - It asks for a general definition or explanation of a technology,
    methodology, or concept that exists independently of this company.
    The company documents would only mention it, not define it.
    Rule: if Wikipedia would have a better answer than the company's
    internal docs, it is out-of-domain.
  - It asks about a specific named individual as a person
    (their identity, personal background, or who they are)
    rather than their role in a company process.

Reasoning process (internal, do not output):
  Step 1: What is the core subject of the question?
  Step 2: Is this subject something the company's internal documents
          would address (policies, procedures, operations)?
          OR is it something that exists in the wider world
          independently of this company?
  Step 3: If the subject is a general concept any company could ask
          about (tech term, methodology, person's identity) → out-of-domain.
          If the subject is about how THIS company operates → in-domain.

Reply with ONLY one word: in-domain | out-of-domain
No punctuation, no explanation, no reasoning in your output.
""".strip()


def _check_domain(question: str) -> bool:
    """Returns True if the question is OUT-of-domain."""
    try:
        verdict = _llm(DOMAIN_CHECK_SYSTEM, question).lower().strip()
        print(f"[domain-check] '{question}' → {verdict}")
        return "out" in verdict
    except Exception as e:
        print(f"⚠️  domain_check LLM error: {e} → assuming in-domain")
        return False


# ────────────────────────────────────────────────────────────────────
# NODE: DECISION
#
# Priority-ordered routing:
#   1. similarity > 1.1          → clearly out-of-domain, no LLM needed
#   2. similarity in [0.7, 1.1]  → LLM domain check
#      └─ out-of-domain          → "out of scope" message, no ticket
#      └─ in-domain + weak sim   → escalate → ticket
#   3. RAG said "no answer"      → escalate → ticket
#   4. similarity > 0.9          → weak match → escalate → ticket
#   5. confidence < 60           → low confidence → escalate → ticket
#   6. good answer               → return directly
# ────────────────────────────────────────────────────────────────────
def decision_node(state: StateCaseState):
    state["is_out_of_domain"] = False
    state["should_escalate"]  = False

    confidence = state.get("confidence", 0)
    answer     = (state.get("answer") or "").lower()
    similarity = state.get("similarity_score")
    question   = state["question"]

    if similarity is None:
        print("⚠️  similarity_score missing → escalating as weak match")
        state["should_escalate"] = True
        return state

    print(f"[decision] similarity={similarity:.4f}  confidence={confidence}%")

    # 1. Clearly out-of-domain (high distance, skip LLM)
    if similarity > 1.1:
        state["is_out_of_domain"] = True
        state["should_escalate"]  = False
        state["answer"] = (
            "This question is outside the scope of our knowledge base. "
            "Please ask something related to our documents."
        )
        state["sources"] = []
        return state

    # 2. Borderline similarity → LLM domain check
    #    If in-domain: fall through to steps 3-5 (escalate with ticket)
    #    If out-of-domain: clean message, no ticket
    if 0.7 <= similarity <= 1.1:
        if _check_domain(question):
            state["is_out_of_domain"] = True
            state["should_escalate"]  = False
            state["answer"] = (
                "This question is outside the scope of our knowledge base. "
                "Please ask something related to our documents."
            )
            state["sources"] = []
            return state
        # in-domain but borderline → continue to escalation checks below

    # 3. RAG explicitly returned no answer
    no_answer_phrases = ["could not find", "not available", "no information"]
    if any(phrase in answer for phrase in no_answer_phrases):
        state["should_escalate"] = True
        return state

    # 4. Weak similarity (in-domain but poor doc match)
    if similarity > 0.9:
        state["should_escalate"] = True
        return state

    # 5. Low confidence
    if confidence < 60:
        state["should_escalate"] = True
        return state

    # 6. Good answer
    state["should_escalate"] = False
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: ANSWER
# ────────────────────────────────────────────────────────────────────
def answer_node(state: StateCaseState):
    state["sources"] = state.get("sources", [])
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: ESCALATE
# Only called for in-domain questions that couldn't be answered.
# ────────────────────────────────────────────────────────────────────
def escalate_node(state: StateCaseState):
    if state.get("is_out_of_domain", False):
        state["answer"] = (
            "This question is outside the scope of our knowledge base. "
            "Please ask something related to our documents."
        )
        return state

    status, ticket_id = create_ticket(
        question=state["question"],
        context=state.get("retrieved_chunks", []),
        filters={
            "doc_type": state.get("doc_type"),
            "industry": state.get("industry"),
            "version":  state.get("version"),
        },
        confidence=state.get("confidence", 0),
        history=state.get("history", []),
        sources=state.get("sources", []),
    )

    if status == "created":
        state["answer"] = (
            f"I couldn't find a reliable answer in our documents. "
            f"A support ticket has been created (ID: {ticket_id}) and our team will follow up."
        )
    elif status == "exists":
        state["answer"] = (
            "A support ticket for this query already exists — our team is already on it. "
            "No duplicate ticket was created."
        )
    else:
        state["answer"] = (
            "I couldn't find a reliable answer and ticket creation failed. "
            "Please contact support directly."
        )

    return state


# ────────────────────────────────────────────────────────────────────
# GRAPH ASSEMBLY
# ────────────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(StateCaseState)

    graph.add_node("intent",   intent_node)
    graph.add_node("clarity",  clarity_node)
    graph.add_node("clarify",  clarify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("decision", decision_node)
    graph.add_node("answer",   answer_node)
    graph.add_node("escalate", escalate_node)

    graph.set_entry_point("intent")

    graph.add_edge("intent",   "clarity")
    graph.add_edge("retrieve", "decision")

    graph.add_conditional_edges(
        "clarity",
        lambda state: "clarify" if state["needs_clarification"] else "retrieve",
    )
    graph.add_conditional_edges(
        "decision",
        lambda state: "escalate" if state["should_escalate"] else "answer",
    )

    graph.add_edge("clarify",  END)
    graph.add_edge("answer",   END)
    graph.add_edge("escalate", END)

    return graph.compile()