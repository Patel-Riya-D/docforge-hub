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
# HELPER: GET PREVIOUS USER MESSAGES FROM HISTORY
#
# IMPORTANT: documents.py appends the CURRENT user question to history
# BEFORE invoking the graph. So history[-1] is always the current
# question. To get context we need history[-2] and earlier.
# ────────────────────────────────────────────────────────────────────
def _get_prior_user_messages(history: list, n: int = 2) -> list:
    """
    Returns the last `n` user messages BEFORE the current one.
    Skips the last user message (which is the current question).
    """
    user_msgs = [h["message"] for h in history if h["role"] == "user"]
    # drop the last one (current question already in history)
    prior = user_msgs[:-1] if len(user_msgs) > 1 else []
    return prior[-n:]


def _get_prior_conversation(history: list, n: int = 4) -> str:
    """
    Returns last `n` history entries (excluding current user message)
    as a formatted string for LLM context.
    """
    # exclude the last entry which is the current user question
    prior = history[:-1] if history else []
    recent = prior[-n:]
    return "\n".join(
        f"{h['role'].capitalize()}: {h['message']}" for h in recent
    )


# ────────────────────────────────────────────────────────────────────
# NODE: INTENT  (LLM-based + verb fast-path)
#
# Classifies into: "generation" | "query" | "meta" | "unclear"
#
# NEW: "meta" intent for conversational questions about the chat itself
# e.g. "what was my previous query", "what did I ask before"
# These are answered directly from history — no RAG needed.
# ────────────────────────────────────────────────────────────────────
INTENT_SYSTEM = """
You are an intent classifier for a document-management assistant.

Classify the user's message into exactly one of these intents:
  - generation  : The user wants to CREATE, GENERATE, DRAFT, MAKE, PRODUCE,
                  BUILD, or WRITE a document, report, SOP, template, policy,
                  letter, or any other artifact.
  - summarize   : The user wants a SUMMARY, OVERVIEW, or BRIEF of an existing
                  document. Includes: "summarize", "give me a summary of",
                  "what is the summary of", "overview of", "brief of".
  - query       : The user wants to RETRIEVE information, get an explanation,
                  find a procedure, or understand something from existing docs.
  - meta        : The user is asking about the conversation itself — their
                  previous questions, what was discussed, chat history.
  - unclear     : Cannot be classified into any of the above even with
                  careful consideration. Use this ONLY as a last resort.

Prioritisation rules (apply in order):
  1. Creation verb + document noun → always "generation".
  2. Summary/overview/brief of a document → always "summarize".
  3. Question about conversation history or previous messages → "meta".
  4. Question about information, explanation, or procedures → "query".
  5. Truly ambiguous short fragments with no context → "unclear".

Reply with ONLY the single word: generation | summarize | query | meta | unclear
No punctuation, no explanation, no extra words.
""".strip()


def intent_node(state: StateCaseState):
    question = state["question"]

    try:
        intent = _llm(INTENT_SYSTEM, question).lower()
        if intent not in ("generation", "summarize", "query", "meta", "unclear"):
            intent = "query"
    except Exception as e:
        print(f"⚠️  intent_node LLM error: {e} → defaulting to 'query'")
        intent = "query"

    print(f"[intent] '{question}' → {intent}")
    state["intent"] = intent
    return state

# ────────────────────────────────────────────────────────────────────
# NODE: META
# Handles conversational questions about the chat history directly.
# No RAG, no ticket. Answers from state["history"] only.
# ────────────────────────────────────────────────────────────────────
from word2number import w2n
import re

def meta_node(state: StateCaseState):
    history  = state.get("history", [])
    question = state["question"].lower()

    prior_user = _get_prior_user_messages(history, n=5)

    if not prior_user:
        state["answer"] = "I don't have any previous questions recorded in this session."
        return state

    # Check if user wants multiple queries
    num_match = re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b', question)

    if num_match:
        try:
            count = w2n.word_to_num(num_match.group())
        except:
            count = 2  # fallback

        recent = prior_user[-count:]
        listed = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(recent))
        state["answer"] = f"Here are your last {count} questions:\n{listed}"

    elif any(kw in question for kw in ["previous", "last", "before", "my query", "what did i ask"]):
        state["answer"] = f"Your previous question was: \"{prior_user[-1]}\""

    else:
        listed = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(prior_user))
        state["answer"] = f"Here are your recent questions:\n{listed}"

    state["confidence"]       = 100
    state["sources"]          = []
    state["should_escalate"]  = False
    state["is_out_of_domain"] = False
    return state

#summarize node
def summarize_node(state: StateCaseState):
    from backend.rag.summarizer import summarize_document

    question = state["question"]

    # ✅ Pure LLM extraction — no hardcoded patterns
    try:
        doc_name = _llm(
            "Extract ONLY the document name from the user's message. "
            "Return just the document name, nothing else. "
            "If no document name is found, return 'unknown'.",
            question
        ).strip()

        if not doc_name or doc_name.lower() == "unknown":
            doc_name = None

    except Exception as e:
        print(f"⚠️  doc name extraction failed: {e}")
        doc_name = None

    if not doc_name:
        state["answer"]          = "Please specify the document name. Example: 'summarize: Remote Work Policy'"
        state["confidence"]      = 0
        state["sources"]         = []
        state["should_escalate"] = False
        return state

    try:
        filters = {
            "doc_type": state.get("doc_type"),
            "industry": state.get("industry"),
            "version":  state.get("version"),
        }

        result  = summarize_document(doc_name, filters)
        summary = result.get("summary", "No summary generated.")

        state["answer"]           = summary
        state["confidence"]       = 100
        state["sources"]          = []
        state["should_escalate"]  = False
        state["is_out_of_domain"] = False

    except Exception as e:
        print(f"⚠️  summarize_node error: {e}")
        state["answer"]     = f"Failed to generate summary: {str(e)}"
        state["confidence"] = 0
        state["sources"]    = []

    return state
# ────────────────────────────────────────────────────────────────────
# NODE: CLARITY
#
# Key fix: history includes the CURRENT question as the last entry
# (added by documents.py before graph invocation). So we must use
# _get_prior_conversation() which strips the current message,
# giving the LLM only the actual prior context to resolve follow-ups.
#
# "vague" = subject unidentifiable even with history context
# "clear" = subject found in question or prior conversation
# ────────────────────────────────────────────────────────────────────
CLARITY_SYSTEM = """
You are a query clarity checker for a document-management assistant.

You will receive:
  - PRIOR CONVERSATION: recent exchanges BEFORE the current question
  - CURRENT QUESTION: what the user just asked

Use the prior conversation to resolve what the current question refers to.
A short or vague-looking message may be a clear follow-up in context.

Your ONLY job: decide whether — using both prior conversation AND
current question — there is an identifiable subject to search for.

You are NOT deciding:
  - Whether the answer exists in the documents
  - Whether the question is in scope or out of scope
  - Whether the data is real-time or historical

DEFAULT to "clear". Return "vague" only when no subject is identifiable
even after reading the prior conversation.

VAGUE — subject is unidentifiable:
  - A document container (report, SOP, policy, document, handbook) is
    named but NO topic appears in question OR prior conversation.
  - Bare single word or fragment with zero context from history.
  - Requires a qualifier (role, level, department) absent from both
    the question and the prior conversation.

CLEAR — subject exists in question or prior conversation:
  - Prior conversation provides the topic the current message refers to.
    e.g. prior: "explain policy" → current: "remote work" →
    combined: "remote work policy" → CLEAR.
  - A specific topic, concept, process, system, or regulation appears
    anywhere in the question or prior conversation.
  - Questions about actions, approvals, steps, requirements, outcomes
    tied to any process → always clear.
  - Current state, pending items, active issues, compliance status → clear.
  - Any named person, technology, acronym, or term → clear.

Internal reasoning (do NOT output):
  Step 1: What topic was discussed in the prior conversation?
  Step 2: Does the current question follow on from that topic?
  Step 3: Combined subject = prior topic + current question.
          Can a retrieval system search for it? Yes → clear. No → vague.

Reply with ONLY one word: vague | clear
""".strip()


def clarity_node(state: StateCaseState):
    question    = state["question"]
    tokens      = question.split()
    intent      = state.get("intent", "query")
    has_filters = bool(
        state.get("doc_type") or state.get("industry") or state.get("version")
    )

    # ✅ Summarize intent never needs clarification — always has doc name
    if intent == "summarize":
        state["needs_clarification"] = False
        state["clarification_question"] = ""
        return state

    needs_clarification    = False
    clarification_question = ""

    # intent == "unclear": use history to decide if it's a follow-up
    if intent == "unclear":
        history = state.get("history", [])
        prior_conv = _get_prior_conversation(history)

        if prior_conv:
            # There IS prior context — treat as a follow-up query, not unclear
            # Re-classify with context
            try:
                clarity_input  = f"Prior conversation:\n{prior_conv}\n\nCurrent message: {question}"
                clarity_result = _llm(CLARITY_SYSTEM, clarity_input).lower()
                print(f"[clarity/unclear-resolve] '{question}' → {clarity_result}")
                if clarity_result == "clear":
                    # Treat as a query follow-up — don't ask for clarification
                    state["needs_clarification"]    = False
                    state["clarification_question"] = ""
                    state["intent"] = "query"   # promote to query so retrieve_node runs
                    return state
            except Exception as e:
                print(f"⚠️  clarity resolve error: {e}")

        # No prior context or still vague after check
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
        history    = state.get("history", [])
        prior_conv = _get_prior_conversation(history)

        try:
            clarity_input = (
                f"Prior conversation:\n{prior_conv}\n\nCurrent question: {question}"
                if prior_conv else question
            )
            clarity_verdict = _llm(CLARITY_SYSTEM, clarity_input).lower()
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
# Short follow-up queries are enriched with the previous user question
# so RAG gets enough context to search correctly.
# ────────────────────────────────────────────────────────────────────
def retrieve_node(state: StateCaseState):
    history   = state.get("history", [])
    current_q = state["question"]

    # For short follow-ups, prepend the previous user question
    if len(current_q.split()) <= 5:
        prior_user = _get_prior_user_messages(history, n=1)
        if prior_user:
            question = f"{prior_user[-1]} {current_q}"
            print(f"[retrieve] enriched query: '{question}'")
        else:
            question = current_q
    else:
        question = current_q

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
# ────────────────────────────────────────────────────────────────────
DOMAIN_CHECK_SYSTEM = """
You are a domain classifier for a document-management assistant.

The assistant holds internal company documents: SOPs, HR policies,
security policies, handbooks, offer letter templates, compliance
checklists, technical guides, deployment procedures, and audit records.

Your job: decide if the user's question is about company-internal
knowledge OR about general world knowledge.

IN-DOMAIN — company-internal knowledge:
  - How the company operates, its rules, procedures, or internal records.
  - Company processes, HR policies, security policies, compliance
    requirements, incident handling, access controls, audit findings.
  - Current state of something the company manages: pending issues,
    active incidents, open tickets, compliance gaps.

OUT-OF-DOMAIN — general world knowledge:
  - General definition or explanation of a technology, methodology,
    or concept that exists independently of this company.
    Rule: if Wikipedia would have a better answer → out-of-domain.
  - A specific named individual's identity or personal background.

Reasoning (internal, do NOT output):
  Step 1: What is the core subject?
  Step 2: Company internal or general world knowledge?
  Step 3: If general concept any company could ask about → out-of-domain.
          If about how THIS company operates → in-domain.

Reply with ONLY one word: in-domain | out-of-domain
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

    # 1. Clearly out-of-domain
    if similarity > 1.1:
        state["is_out_of_domain"] = True
        state["should_escalate"]  = False
        state["answer"] = (
            "This question is outside the scope of our knowledge base. "
            "Please ask something related to our documents."
        )
        state["sources"] = []
        return state

    # 2. Borderline → LLM domain check
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

    # 3. RAG explicitly no answer
    no_answer_phrases = ["could not find", "not available", "no information"]
    if any(phrase in answer for phrase in no_answer_phrases):
        state["should_escalate"] = True
        return state

    # 4. Weak similarity
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
#
#   intent → [meta]    → END                      (conversational Q)
#          → clarity → clarify → END              (needs clarification)
#                    → retrieve → decision → answer   → END
#                                          → escalate → END
# ────────────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(StateCaseState)

    graph.add_node("intent",    intent_node)
    graph.add_node("meta",      meta_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("clarity",   clarity_node)
    graph.add_node("clarify",   clarify_node)
    graph.add_node("retrieve",  retrieve_node)
    graph.add_node("decision",  decision_node)
    graph.add_node("answer",    answer_node)
    graph.add_node("escalate",  escalate_node)

    graph.set_entry_point("intent")

    # ✅ Single conditional edge — delete the duplicate above this
    graph.add_conditional_edges(
        "intent",
        lambda state: (
            "meta"      if state.get("intent") == "meta"      else
            "summarize" if state.get("intent") == "summarize" else
            "clarity"
        ),
    )

    graph.add_edge("meta",      END)
    graph.add_edge("summarize", END)
    graph.add_edge("retrieve",  "decision")

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