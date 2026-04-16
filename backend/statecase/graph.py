"""
graph.py

Defines the LangGraph workflow for the StateCase Assistant.

This module orchestrates the full conversational pipeline using a
state machine approach, enabling intelligent routing of user queries
through multiple processing stages.

Core Responsibilities:
- Intent classification (generation, query, summarize, meta)
- Query clarity validation
- Context-aware retrieval (RAG)
- Document summarization
- Out-of-domain detection
- Decision making (answer vs escalation)
- Ticket creation for unresolved queries

Architecture:
- Uses LangGraph (StateGraph) to define nodes and transitions
- Each node updates a shared state (StateCaseState)
- Conditional edges control dynamic flow

Key Features:
- Context-aware conversation handling
- Pronoun resolution using chat history
- Query rewriting for better retrieval
- Confidence + similarity-based escalation logic
- Seamless integration with ticketing system

Flow:
    intent → (meta | summarize | clarity)
    clarity → (clarify | retrieve)
    retrieve → decision → (answer | escalate)

Notes:
- Designed for production-level conversational AI systems
- Fully extensible (new nodes can be added easily)
"""
from langgraph.graph import StateGraph, END
from backend.statecase.models import StateCaseState
from backend.rag.query_search_engine import answer_question as rag_query
from backend.statecase.ticketing import create_ticket
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from word2number import w2n
import re

def greeting_node(state):
    question = state["question"].lower().strip()

    greetings = ["hi", "hello", "hey", "good morning", "good evening"]

    if any(g in question for g in greetings):
        state["is_greeting"] = True
        state["answer"] = "👋 Hi! I'm your AI assistant. You can ask me about policies, documents, or anything related to your company."
    else:
        state["is_greeting"] = False

    return state

# ────────────────────────────────────────────────────────────────────
# HELPER: LLM CALL
# ────────────────────────────────────────────────────────────────────
def _llm(system: str, user: str) -> str:
    """
    Execute an LLM call with system and user prompts.

    Args:
        system (str): System-level instruction prompt
        user (str): User input or query

    Returns:
        str: LLM-generated response

    Notes:
        - Uses configured LLM provider
        - Returns stripped text output
    """
    llm = get_llm()
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    return llm.invoke(messages).content.strip()


# ────────────────────────────────────────────────────────────────────
# HELPER: BUILD CONVERSATION CONTEXT STRING
# ────────────────────────────────────────────────────────────────────
def _get_prior_user_messages(history: list, n: int = 3) -> list:
    """
    Returns the last `n` user messages BEFORE the current one.
    Skips history[-1] which is always the current question
    (documents.py appends it before graph invocation).
    """
    user_msgs = [h["message"] for h in history if h["role"] == "user"]
    prior = user_msgs[:-1] if len(user_msgs) > 1 else []
    return prior[-n:]


def _get_prior_conversation(history: list, n: int = 6) -> str:
    """
    FIX (Issue 1): Returns last `n` history entries INCLUDING the
    current user message (history[-1]) so clarity and summarize nodes
    have full context when deciding.

    Previously this used history[:-1] which excluded the current
    question, making follow-ups look context-free.
    """
    # Include all history; the caller can control n to limit window
    recent = history[-n:] if history else []
    return "\n".join(
        f"{h['role'].capitalize()}: {h['message']}" for h in recent
    )


def _get_prior_conversation_excluding_current(history: list, n: int = 6) -> str:
    """
    Returns conversation history EXCLUDING the current user message.
    Used only in meta_node where we want to show prior exchanges.
    """
    prior = history[:-1] if history else []
    recent = prior[-n:]
    return "\n".join(
        f"{h['role'].capitalize()}: {h['message']}" for h in recent
    )


# ────────────────────────────────────────────────────────────────────
# NODE: INTENT
# Classifies into: "generation" | "summarize" | "query" | "meta" | "unclear"
# ────────────────────────────────────────────────────────────────────
INTENT_SYSTEM = """
You are an intent classifier for a document-management assistant.

You will receive the FULL conversation (prior + current message).
Use ALL of it to determine the intent of the LAST user message.

Classify into exactly one of:
  - generation  : The user wants to CREATE, GENERATE, DRAFT, MAKE, PRODUCE,
                  BUILD, or WRITE a document, report, SOP, template, policy,
                  letter, or any other artifact.
  - summarize   : The user wants a SUMMARY, OVERVIEW, or BRIEF of an existing
                  document. Includes: "summarize", "give me a summary of",
                  "what is the summary of", "overview of", "brief of",
                  "summary of this", "summarize that", or any pronoun
                  ("this", "that", "it") referring to a doc discussed earlier.
  - query       : The user wants to RETRIEVE information, get an explanation,
                  find a procedure, or understand something from existing docs.
  - meta        : The user is asking about the conversation itself — their
                  previous questions, what was discussed, chat history.
  - unclear     : Cannot be classified even with full context. Last resort only.

Prioritisation rules (apply in order):
  1. Creation verb + document noun → always "generation".
  2. Summary/overview/brief, OR pronoun ("this","that","it") after
     a document was discussed → always "summarize".
  3. Question about conversation history → "meta".
  4. Question about information or procedures → "query".
  5. Truly ambiguous with no context → "unclear".

Reply with ONLY the single word: generation | summarize | query | meta | unclear
""".strip()



def intent_node(state: StateCaseState):
    """
    Classify the user's intent based on full conversation context.

    Args:
        state (StateCaseState): Current graph state

    Returns:
        StateCaseState: Updated state with 'intent'

    Possible Intents:
        - generation : Create new document/content
        - summarize  : Summarize existing document
        - query      : Retrieve information
        - meta       : Ask about previous conversation
        - unclear    : Ambiguous query

    Features:
        - Uses full conversation history (not just current query)
        - Handles pronouns like "this", "that"
        - Defaults to 'query' on failure

    Importance:
        - Entry point of the graph
        - Determines entire flow direction
    """
    question = state["question"].lower().strip()
    history  = state.get("history", [])

    # ✅ STEP 1: GREETING DETECTION (ADD THIS BLOCK)
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]

    if any(g in question for g in greetings):
        state["intent"] = "greeting"
        state["answer"] = (
            "👋 Hi! I'm your AI assistant. "
            "You can ask me about policies, SOPs, documents, or company processes."
        )
        return state

    # ✅ STEP 2: EXISTING LOGIC (NO CHANGE BELOW)
    full_conv = _get_prior_conversation(history, n=8)

    intent_input = (
        f"Conversation so far:\n{full_conv}\n\nClassify the intent of the LAST user message."
        if full_conv else question
    )

    try:
        intent = _llm(INTENT_SYSTEM, intent_input).lower()
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
# ────────────────────────────────────────────────────────────────────
def meta_node(state: StateCaseState):
    """
    Handle meta-level queries about conversation history.

    Args:
        state (StateCaseState)

    Returns:
        StateCaseState

    Capabilities:
        - Returns previous user questions
        - Supports queries like:
            • "What did I ask before?"
            • "Show last 3 questions"

    Notes:
        - Does not use RAG
        - Always returns high confidence
    """
    history  = state.get("history", [])
    question = state["question"].lower()

    prior_user = _get_prior_user_messages(history, n=5)

    if not prior_user:
        state["answer"] = "I don't have any previous questions recorded in this session."
        return state

    num_match = re.search(
        r'\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b', question
    )

    if num_match:
        try:
            count = w2n.word_to_num(num_match.group())
        except Exception:
            count = 2

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


# ────────────────────────────────────────────────────────────────────
# NODE: SUMMARIZE
#
# FIX (Issue 1): Now resolves pronouns ("this policy", "that document",
# "it") by inspecting the prior conversation when doc_name extraction
# returns a vague result. Also uses conversation_context from state
# if available (sent by ui.py).
# ────────────────────────────────────────────────────────────────────
DOC_NAME_EXTRACT_SYSTEM = """
You are a document name extractor.

You will receive a conversation (prior exchanges + current message).
Extract the name of the document the user wants summarized.

Rules:
- If the current message contains a clear document name, return it exactly.
- If the current message uses a pronoun ("this", "that", "it") or vague
  reference ("this policy", "that document"), look at the PRIOR conversation
  to find the most recently mentioned document name and return THAT.
- Return ONLY the document name, nothing else.
- If you truly cannot determine the document name, return "unknown".
""".strip()


def summarize_node(state: StateCaseState):
    """
    Generate summary of a document using context-aware extraction.

    Args:
        state (StateCaseState)

    Returns:
        StateCaseState

    Features:
        - Extracts document name using LLM
        - Resolves pronouns (e.g., "this policy")
        - Falls back to previous conversation if needed
        - Uses RAG summarizer

    Output:
        - summary text
        - confidence = 100

    Edge Cases:
        - Asks user if document name cannot be determined
    """
    from backend.rag.summarizer import summarize_document

    question = state["question"]
    history  = state.get("history", [])

    # FIX (Issue 1): include full conversation so LLM can resolve pronouns
    full_conv = _get_prior_conversation(history, n=8)
    extraction_input = (
        f"Conversation:\n{full_conv}\n\nExtract the document name the user wants summarized."
        if full_conv else question
    )

    try:
        doc_name = _llm(DOC_NAME_EXTRACT_SYSTEM, extraction_input).strip()
        if not doc_name or doc_name.lower() == "unknown":
            doc_name = None
    except Exception as e:
        print(f"⚠️  doc name extraction failed: {e}")
        doc_name = None

    # FIX (Issue 1): fallback — scan prior user messages for last doc reference
    if not doc_name:
        prior_user = _get_prior_user_messages(history, n=5)
        for msg in reversed(prior_user):
            # Heuristic: if a prior message looks like a doc name (> 2 words, no ?)
            if len(msg.split()) >= 2 and "?" not in msg:
                doc_name = msg.strip()
                print(f"[summarize] fallback doc_name from history: '{doc_name}'")
                break

    if not doc_name:
        state["answer"]          = (
            "Please specify the document name. Example: 'summarize: Remote Work Policy'"
        )
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
# ────────────────────────────────────────────────────────────────────
CLARITY_SYSTEM = """
You are a query clarity checker for a document-management assistant.

You will receive the FULL conversation including the current user message.
Use ALL of it to decide if there is an identifiable subject to search for.

DEFAULT to "clear". Return "vague" ONLY as a last resort.

ALWAYS "clear":
  - Any question containing a role, level, or job title.
  - Any question about salary, compensation, pay, benefits, or ranges.
  - Any question about working hours, schedule, availability, or timing.
  - Any question that contains two or more specific nouns or concepts.
  - Any question longer than 4 words with a clear subject.
  - A single topic word matching a known HR/policy concept
    (e.g. "remote work", "leave", "onboarding", "reimbursement").
  - A follow-up message where prior conversation provides the subject.
    e.g. prior: "explain policy" + "remote work" → subject is clear.
  - Any pronoun ("this", "that", "it") when a document was mentioned
    in prior conversation.

VAGUE — ONLY for:
  - A bare container word (policy, SOP, report) with NO topic ANYWHERE
    in the conversation (current or prior).
  - A single meaningless fragment with zero conversation context.

Reply with ONLY one word: vague | clear
""".strip()


def clarity_node(state: StateCaseState):
    """
    Determine whether the user query is clear or requires clarification.

    Args:
        state (StateCaseState)

    Returns:
        StateCaseState

    Behavior:
        - Uses LLM to classify query as:
            • "clear"
            • "vague"
        - Considers full conversation context

    Scenarios:
        - If vague → asks clarification question
        - If clear → proceeds to retrieval

    Special Handling:
        - Enhances query using previous messages
        - Skips for summarize intent

    Importance:
        - Prevents bad retrieval queries
        - Improves accuracy significantly
    """
    question    = state["question"]
    tokens      = question.split()
    intent      = state.get("intent", "query")
    has_filters = bool(
        state.get("doc_type") or state.get("industry") or state.get("version")
    )
    history = state.get("history", [])

    # Summarize intent never needs clarification
    if intent == "summarize":
        state["needs_clarification"]    = False
        state["clarification_question"] = ""
        return state

    needs_clarification    = False
    clarification_question = ""

    if intent == "unclear":
        # FIX (Issue 1): use FULL conversation including current message
        full_conv = _get_prior_conversation(history, n=8)

        if full_conv:
            try:
                clarity_input  = (
                    f"Full conversation:\n{full_conv}\n\n"
                    f"Is the subject of the LAST user message identifiable?"
                )
                clarity_result = _llm(CLARITY_SYSTEM, clarity_input).lower()
                print(f"[clarity/unclear-resolve] '{question}' → {clarity_result}")

                if clarity_result == "clear":
                    state["needs_clarification"]    = False
                    state["clarification_question"] = ""
                    state["intent"]                 = "query"

                    # Enrich with prior question for retrieve_node
                    prior_user = _get_prior_user_messages(history, n=1)
                    if prior_user:
                        state["enriched_question"] = f"{prior_user[-1]} {question}"
                        print(f"[clarity/unclear-resolve] enriched: '{state['enriched_question']}'")

                    return state
            except Exception as e:
                print(f"⚠️  clarity resolve error: {e}")

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
        # FIX (Issue 1): use FULL conversation (not history[:-1])
        # so the current message + prior exchanges are both visible
        full_conv = _get_prior_conversation(history, n=8)

        try:
            clarity_input = (
                f"Full conversation:\n{full_conv}\n\n"
                f"Is the subject of the LAST user message identifiable?"
                if full_conv else question
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
# NODE: CLARIFY
# ────────────────────────────────────────────────────────────────────
def clarify_node(state: StateCaseState):
    state["answer"] = state["clarification_question"]
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: RETRIEVE
#
# FIX (Issue 1): Query enrichment now uses FULL prior conversation
# context (not just the last user question). This means follow-up
# queries like "summary of this policy" correctly resolve to
# "Remote Work Policy summary" when that doc was discussed before.
# ────────────────────────────────────────────────────────────────────
QUERY_REWRITE_SYSTEM = """
You are a query rewriter for a document-management search engine.

You will receive a conversation history and the current user question.
Rewrite the current question into a SELF-CONTAINED search query that
resolves all pronouns and references using the conversation context.

Rules:
- Replace "this policy", "that document", "it", "that" etc. with the
  actual document/topic name from prior conversation.
- Keep the rewritten query concise (under 15 words).
- If the query is already self-contained, return it unchanged.
- Return ONLY the rewritten query, no explanation.
""".strip()


def retrieve_node(state: StateCaseState):
    """
    Perform document retrieval using RAG pipeline.

    Args:
        state (StateCaseState)

    Returns:
        StateCaseState

    Features:
        - Query rewriting using conversation context
        - Resolves pronouns ("this policy" → actual name)
        - Uses filters:
            • doc_type
            • industry
            • version

    Outputs:
        - answer
        - retrieved_chunks
        - confidence score
        - similarity score
        - sources

    Importance:
        - Core knowledge retrieval engine
    """
    history   = state.get("history", [])
    current_q = state["question"]

    # FIX (Issue 1): use enriched_question from clarity_node if set
    if state.get("enriched_question"):
        question = state["enriched_question"]
        print(f"[retrieve] using enriched query from clarity: '{question}'")
        state["enriched_question"] = None

    else:
        # FIX (Issue 1): for ALL queries (not just short ones), rewrite
        # using full conversation context to resolve pronouns/references
        full_conv = _get_prior_conversation(history, n=8)

        if full_conv and len(current_q.split()) <= 8:
            # Short queries are most likely to have unresolved references
            try:
                rewrite_input = (
                    f"Conversation:\n{full_conv}\n\n"
                    f"Rewrite this query to be self-contained: {current_q}"
                )
                rewritten = _llm(QUERY_REWRITE_SYSTEM, rewrite_input).strip()
                if rewritten and rewritten.lower() != current_q.lower():
                    print(f"[retrieve] rewritten query: '{rewritten}'")
                    question = rewritten
                else:
                    question = current_q
            except Exception as e:
                print(f"⚠️  query rewrite failed: {e}")
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
    """
    Decide whether to answer the query or escalate to ticketing.

    Args:
        state (StateCaseState)

    Returns:
        StateCaseState

    Decision Factors:
        - similarity_score (vector match quality)
        - confidence score
        - answer quality
        - domain classification

    Outcomes:
        - answer → return response
        - escalate → create ticket
        - out-of-domain → reject query

    Rules:
        - Low confidence → escalate
        - No answer → escalate
        - Out-of-domain → reject
        - Weak similarity → escalate

    Importance:
        - Business-critical logic
        - Controls escalation system
    """
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

    if similarity > 1.1:
        state["is_out_of_domain"] = True
        state["should_escalate"]  = False
        state["answer"] = (
            "Your question appears to be outside the scope of our internal knowledge base. "
            "Our documents cover company policies, SOPs, HR guidelines, and internal procedures. "
            "For general topics, please refer to external resources."
        )
        state["sources"] = []
        return state

    if 0.7 <= similarity <= 1.1:
        if _check_domain(question):
            state["is_out_of_domain"] = True
            state["should_escalate"]  = False
            state["answer"] = (
                "Your question appears to be outside the scope of our internal knowledge base. "
                "Our documents cover company policies, SOPs, HR guidelines, and internal procedures. "
                "For general topics, please refer to external resources."
            )
            state["sources"] = []
            return state

    no_answer_phrases = ["could not find", "not available", "no information"]
    if any(phrase in answer for phrase in no_answer_phrases):
        state["should_escalate"] = True
        return state

    if similarity > 0.9:
        state["should_escalate"] = True
        return state

    if confidence < 60:
        state["should_escalate"] = True
        return state

    state["should_escalate"] = False
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: ANSWER
# ────────────────────────────────────────────────────────────────────
def answer_node(state: StateCaseState):
    """
    Format final answer with sources.

    Args:
        state (StateCaseState)

    Returns:
        StateCaseState

    Features:
        - Deduplicates sources
        - Appends sources to answer
        - Formats response for UI

    Output:
        - Answer + citations
    """
    sources = state.get("sources", [])
    answer  = state.get("answer", "")

    if sources:
        seen = []
        for s in sources:
            if isinstance(s, str):
                label = s
            elif isinstance(s, dict):
                label = s.get("title") or s.get("source") or s.get("name") or str(s)
            else:
                label = str(s)

            if label and label not in seen:
                seen.append(label)

        if seen:
            citation_lines = "\n".join(f"  • {label}" for label in seen)
            state["answer"] = (
                f"{answer}\n\n"
                f"---\n"
                f"📚 **Sources:**\n{citation_lines}"
            )

    state["sources"] = sources
    return state


# ────────────────────────────────────────────────────────────────────
# NODE: ESCALATE
# ────────────────────────────────────────────────────────────────────
def escalate_node(state: StateCaseState):
    """
    Escalate query by creating a support ticket.

    Args:
        state (StateCaseState)

    Returns:
        StateCaseState

    Behavior:
        - Calls ticket creation system
        - Handles:
            • existing ticket
            • new ticket
            • failure case

    Outputs:
        - User-friendly message
        - Ticket ID

    Notes:
        - Triggered when:
            • low confidence
            • no answer
            • unclear result
    """
    if state.get("is_out_of_domain", False):
        state["answer"] = (
            "Your question appears to be outside the scope of our internal knowledge base. "
            "Our documents cover company policies, SOPs, HR guidelines, and internal procedures. "
            "For general topics, please refer to external resources."
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

    if status == "exists":
        state["answer"] = (
            f"I couldn't find a reliable answer in our documents.\n\n"
            f"🔁 A support ticket for this query **already exists in Notion** "
            f"(ID: `{ticket_id}`). Our team is already working on it — "
            f"no duplicate ticket was created."
        )
    elif status == "created":
        state["answer"] = (
            f"I couldn't find a reliable answer in our documents.\n\n"
            f"🎫 A new support ticket has been **created in Notion** "
            f"(ID: `{ticket_id}`). Our team will review and follow up with you."
        )
    else:
        state["answer"] = (
            "I couldn't find a reliable answer in our documents, "
            "and ticket creation failed. Please contact support directly."
        )

    return state


# ────────────────────────────────────────────────────────────────────
# GRAPH ASSEMBLY
# ────────────────────────────────────────────────────────────────────
def build_graph():
    """
    Construct and compile the LangGraph workflow.

    Returns:
        Compiled graph object

    Nodes:
        - intent
        - meta
        - summarize
        - clarity
        - clarify
        - retrieve
        - decision
        - answer
        - escalate

    Flow:
        intent
            ├── meta → END
            ├── summarize → END
            └── clarity
                    ├── clarify → END
                    └── retrieve → decision
                                ├── answer → END
                                └── escalate → END

    Features:
        - Conditional routing
        - Stateful processing
        - Modular node design

    Importance:
        - Core orchestrator of assistant
        - Defines entire system behavior
    """
    graph = StateGraph(StateCaseState)

    graph.add_node("greeting", greeting_node)
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

    graph.add_conditional_edges(
        "intent",
        lambda state: (
            "answer"    if state.get("intent") == "greeting" else
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
        lambda state: (
            "escalate" if state.get("should_escalate")  else
            "escalate" if state.get("is_out_of_domain") else
            "answer"
        ),
    )

    graph.add_edge("clarify",  END)
    graph.add_edge("answer",   END)
    graph.add_edge("escalate", END)

    return graph.compile()