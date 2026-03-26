"""
documents.py

This module defines all document-related API endpoints for the DocForge Hub system.

It includes:
- Document preview and generation
- Draft lifecycle management (create, list, delete, approve, regenerate)
- Export functionality (DOCX)
- Company profile management
- Section editing and improvement using LLM
- Clarification question generation
- Notion publishing integration
- RAG-based querying, comparison, summarization, and evaluation

Built using FastAPI with SQLAlchemy ORM and integrated with LLM + RAG pipelines.
"""
from fastapi import APIRouter, HTTPException
from backend.api.schemas import DocumentPreviewRequest
from backend.api.schemas import SaveSectionEditRequest
from backend.models.company_profile import CompanyProfile
from backend.db_models import CompanyProfile
from backend.api.schemas import CompanyProfileCreate
from backend.generation.question_engine import generate_clarification_questions
from backend.registry.db_loader import load_document_from_db
from backend.generation.generator import generate_draft
from backend.api.schemas import DocumentGenerateRequest
from backend.api.schemas import QuestionRequest
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.dependencies import get_db
from backend.db_models import Draft, DraftSection
from backend.db_models import Document
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse
from backend.export.exporter import generate_docx
from backend.export.docx_formatter import build_docx
import io
from sqlalchemy import func
import json
from pydantic import BaseModel
from backend.generation.llm_provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.integrations.notion_publisher import publish_document_to_notion
from backend.rag.query_search_engine import answer_question
from backend.rag.compare_engine import compare_documents
from backend.rag.summarizer import summarize_document
from backend.rag.evaluate import run_evaluation
from backend.utils.logger import get_logger
from backend.utils.redis_session import update_session_history
from backend.utils.rate_limitter import check_rate_limit
from backend.statecase.graph import build_graph
from backend.statecase.models import StateCaseState
from backend.statecase.memory import memory_store
from backend.utils.redis_session import update_session_history
from backend.utils.redis_session import get_user_session, save_user_session
import uuid
from fastapi import BackgroundTasks
from backend.statecase.ticketing import create_ticket

logger = get_logger("API")

router = APIRouter(prefix="/documents", tags=["Documents"])

# build graph once (global)
statecase_graph = build_graph()


@router.post("/preview")
def preview_document(payload: DocumentPreviewRequest, db: Session = Depends(get_db)):
    """
    Preview a document template from the registry.

    This endpoint retrieves a document structure based on department
    and document filename without generating content.

    Args:
        payload (DocumentPreviewRequest): Contains department and document filename.
        db (Session): Database session dependency.

    Returns:
        dict: Document structure from registry.

    Raises:
        HTTPException:
            404 if document not found.
            500 for unexpected errors.
    """
    logger.info(f"/preview called: {payload.department}/{payload.document_filename}")

    try:
        doc = load_document_from_db(
            db=db,
            department=payload.department,
            document_filename=payload.document_filename
        )

        logger.info("Preview document loaded successfully")
        return doc

    except ValueError as e:
        logger.warning(f"Preview not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
def generate_document(payload: DocumentGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a document draft using LLM and store it in the database.

    Workflow:
    1. Load registry document template
    2. Validate required inputs
    3. Generate draft using LLM
    4. Store draft metadata and sections in DB

    Args:
        payload (DocumentGenerateRequest): Includes inputs, company profile, and metadata.
        db (Session): Database session.

    Returns:
        dict: Draft ID and status.

    Raises:
        HTTPException: 500 if generation fails.
    """
    logger.info(f"/generate called: {payload.document_filename}")
    try:
        registry_doc = load_document_from_db(
            db=db,
            department=payload.department,
            document_filename=payload.document_filename
        )

        # 🔎 Validate that all inputs are filled before generating
        for key, value in payload.document_inputs.items():
            if value in ["", None]:
                return {
                    "status": "questions_required",
                    "message": f"Missing value for {key}"
                }
        
        logger.info("Starting draft generation")
        
        draft_result = generate_draft(
            registry_doc=registry_doc,
            department=payload.department,
            document_filename=payload.document_filename,
            company_profile=payload.company_profile,
            document_inputs=payload.document_inputs,
            user_notes=getattr(payload, "user_notes", None)
        )

        latest_version = db.query(func.max(Draft.version)).filter(
            Draft.document_name == registry_doc["document_name"],
            Draft.department == payload.department
        ).scalar()

        next_version = int(latest_version or 0) + 1

        draft = Draft(
            document_name=registry_doc["document_name"],
            department=payload.department,
            document_type=registry_doc.get("internal_type"),
            industry=payload.company_profile.get("industry"),
            tags=["docforge"],
            created_by=payload.company_profile.get("company_name"),
            status=draft_result["status"],
            version=next_version,
            regeneration_count=draft_result["generation_metadata"].get("retry_count", 0)
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        logger.info(f"Draft saved successfully: draft_id={draft.id}")

        import json

        print("SECTIONS STRUCTURE:", draft_result["sections"])

        for idx, section in enumerate(draft_result.get("sections", []), start=1):

            print("SECTION ITEM TYPE:", type(section))

            # Convert string section to dict if needed
            if isinstance(section, str):
                try:
                    section = json.loads(section)
                except Exception:
                    continue

            if not isinstance(section, dict):
                continue

            blocks = section.get("blocks", [])

            # Ensure blocks is a list
            if isinstance(blocks, str):
                try:
                    blocks = json.loads(blocks)
                except Exception:
                    blocks = []

            if not isinstance(blocks, list):
                blocks = []
            
            section_name = str(
                section.get("name") or section.get("section_name") or "Section"
            ).strip()

            db_section = DraftSection(
                draft_id=draft.id,
                section_name=section.get("name") or section.get("section_name", "Section"),
                section_order=idx,
                content=blocks
            )

            db.add(db_section)

        db.commit()

        return {
            "draft_id": draft.id,
            "status": "draft_saved",
            "message": "Draft generated and stored successfully"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error generating draft: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drafts")
def list_drafts(db: Session = Depends(get_db)):
    """
    Retrieve all document drafts.

    Args:
        db (Session): Database session.

    Returns:
        list[dict]: List of drafts with id, name, status, and version.
    """
    drafts = db.query(Draft).all()

    return [
        {
            "id": d.id,
            "document_name": d.document_name,
            "status": d.status,
            "version": d.version
        }
        for d in drafts
    ]

@router.delete("/draft/{draft_id}")
def delete_draft(draft_id: int, db: Session = Depends(get_db)):
    """
    Delete a draft by ID.

    Args:
        draft_id (int): Draft identifier.
        db (Session): Database session.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: 404 if draft not found.
    """
    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
     raise HTTPException(status_code=404, detail="Draft not found")


    db.delete(draft)
    db.commit()

    return {"message": "Draft deleted successfully"}

@router.get("/list")
def list_documents(department: str, db: Session = Depends(get_db)):
    """
    List available document templates for a department.

    Args:
        department (str): Department name.
        db (Session): Database session.

    Returns:
        list[dict]: Document names and types.
    """
    docs = db.query(Document).filter(func.lower(Document.department) == department.lower()).all()

    return [
        {
            "document_name": d.document_name,
            "internal_type": d.internal_type
        }
        for d in docs
    ]

@router.get("/draft/{draft_id}")
def get_draft_detail(draft_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full draft details including sections.

    Args:
        draft_id (int): Draft identifier.
        db (Session): Database session.

    Returns:
        dict: Draft metadata and section content.

    Raises:
        HTTPException: 404 if draft not found.
    """

    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    sections = (
        db.query(DraftSection)
        .filter(DraftSection.draft_id == draft_id)
        .order_by(DraftSection.section_order.asc())
        .all()
    )

    return {
        "id": draft.id,
        "document_name": draft.document_name,
        "status": draft.status,
        "version": draft.version,
        "sections": [
            {
                "section_name": s.section_name,
                "blocks": s.content,
                "status": s.status,
                "regeneration_count": s.regeneration_count
            }
            for s in sections
        ]
    }

@router.get("/export/{draft_id}/{file_type}")
def export_draft(draft_id: int, file_type: str, db: Session = Depends(get_db)):
    """
    Export a draft into DOCX, PDF, or XLS format.

    Conditions:
    - All sections must be approved before export.

    Args:
        draft_id (int): Draft identifier.
        file_type (str): Export format (docx, pdf, xls).
        db (Session): Database session.

    Returns:
        StreamingResponse: File download response.

    Raises:
        HTTPException:
            404 if draft not found.
            400 if sections are not approved or invalid type.
    """

    draft_obj = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft_obj:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    not_approved = db.query(DraftSection).filter(
        DraftSection.draft_id == draft_id,
        DraftSection.status != "approved"
    ).count()

    if not_approved > 0:
        raise HTTPException(
            status_code=400,
            detail="All sections must be approved before export"
        )

    sections = (
        db.query(DraftSection)
        .filter(DraftSection.draft_id == draft_id)
        .order_by(DraftSection.section_order.asc())
        .all()
    )

    # Fetch original document metadata
    doc_meta = db.query(Document).filter(
        func.lower(Document.document_name) == draft_obj.document_name.lower(),
        func.lower(Document.department) == draft_obj.department.lower()
    ).first()

    internal_type = doc_meta.internal_type if doc_meta else ""
    risk_level = doc_meta.risk_level if doc_meta else "MEDIUM"

    sections_data = []

    for s in sections:

        blocks = s.content

        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = [{"type": "paragraph", "content": blocks}]

        elif isinstance(blocks, dict):
            blocks = [blocks]

        elif not isinstance(blocks, list):
            blocks = []

        sections_data.append({
            "name": s.section_name,
            "blocks": blocks,
            "mandatory": True
        })

        draft_dict = {
            "source_document": {
                "document_name": draft_obj.document_name,
                "department": draft_obj.department,
                "internal_type": internal_type,
                "risk_level": risk_level
            },
            "version": f"v{draft_obj.version}",
            "status": draft_obj.status,
            "generation_metadata": {
                "generated_at": draft_obj.created_at.isoformat() if draft_obj.created_at else ""
            },
            "sections": sections_data
        }
    filename = draft_obj.document_name.replace(" ", "_")

    if file_type == "docx":
        print("SECTIONS SENT TO DOCX:", draft_dict["sections"])
        try:
            docx_bytes = build_docx(draft_dict)

        except Exception as e:
            print("DOCX ERROR:", str(e))
            raise HTTPException(
                status_code=500,
                detail=f"DOCX generation failed: {str(e)}"
            )

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}.docx"'}
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid export type")

@router.post("/company-profile")
def create_company_profile(profile: CompanyProfileCreate, db: Session = Depends(get_db)):
    """
    Create a company profile.

    Args:
        profile (CompanyProfileCreate): Company details.
        db (Session): Database session.

    Returns:
        CompanyProfile: Stored company profile object.
    """
    db_profile = CompanyProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.post("/approve-section")
def approve_section(draft_id: int, section_name: str, db: Session = Depends(get_db)):
    """
    Approve a specific section of a draft.

    Args:
        draft_id (int): Draft ID.
        section_name (str): Section name.
        db (Session): Database session.

    Returns:
        dict: Approval status.

    Raises:
        HTTPException: 404 if section not found.
    """
    section = db.query(DraftSection).filter(
        DraftSection.draft_id == draft_id,
        DraftSection.section_name == section_name
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if section.status == "approved":
        return {"message": "Section already approved"}

    section.status = "approved"
    section.approved_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Section approved successfully",
        "section_name": section.section_name,
        "status": section.status
    }

@router.post("/regenerate-section")
def regenerate_section(draft_id: int, section_name: str, improvement_note: str, db: Session = Depends(get_db)):
    """
    Regenerate a section using LLM with user-provided feedback.

    Args:
        draft_id (int): Draft ID.
        section_name (str): Section name.
        improvement_note (str): User feedback for improvement.
        db (Session): Database session.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: 404 if draft/section not found, 500 on failure.
    """
    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    section = db.query(DraftSection).filter(
        DraftSection.draft_id == draft_id,
        DraftSection.section_name == section_name
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        from backend.generation.generator import regenerate_section_llm
        import json

        # Normalize existing content
        blocks = section.content

        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = []

        if not isinstance(blocks, list):
            blocks = []

        # Call LLM regeneration
        new_blocks = regenerate_section_llm(
            draft={
                "source_document": {
                    "internal_type": draft.document_name,
                    "risk_level": "MEDIUM",
                    "department": draft.department
                }
            },
            section={
                "name": section.section_name,
                "blocks": blocks
            },
            issues=[f"User correction: {improvement_note}"]
        )

        # Ensure result is always list
        if isinstance(new_blocks, dict):
            new_blocks = [new_blocks]

        if not isinstance(new_blocks, list):
            new_blocks = [
                {
                    "type": "paragraph",
                    "content": str(new_blocks)
                }
            ]

        section.content = new_blocks
        section.status = "draft"
        section.regeneration_count += 1
        draft.status = "NEEDS_REVIEW"

        db.commit()

        return {"message": "Section regenerated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-section-edit")
def save_section_edit(payload: SaveSectionEditRequest, db: Session = Depends(get_db)):
    """
    Save and improve edited section content using LLM.

    Workflow:
    1. Optionally improve grammar using LLM
    2. Replace paragraph content
    3. Update draft status

    Args:
        payload (SaveSectionEditRequest): Edit payload.
        db (Session): Database session.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: 404 if draft/section not found, 500 on failure.
    """
    draft = db.query(Draft).filter(Draft.id == payload.draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    section = db.query(DraftSection).filter(
        DraftSection.draft_id == payload.draft_id,
        DraftSection.section_name == payload.section_name
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        # -------------------------------
        # 🔹 Step 1: Improve grammar using LLM
        # -------------------------------

                # Detect document type
        doc_meta = db.query(Document).filter(
            func.lower(Document.document_name) == draft.document_name.lower(),
            func.lower(Document.department) == draft.department.lower()
        ).first()

        document_type = doc_meta.internal_type if doc_meta else ""

        # Skip LLM editing for FORM documents
        if document_type.upper() == "FORM":
            improved_text = payload.updated_text
        else:
            llm = get_llm()

            prompt = f"""
        Improve the grammar, clarity, and professionalism of the following text.

        Rules:
        - Do NOT change meaning.
        - Do NOT add new information.
        - Do NOT remove important content.
        - Return only the improved version.
        - Keep enterprise tone.

        Text:
        {payload.updated_text}
        """

            response = llm.invoke([
                SystemMessage(content="You are a professional enterprise document editor."),
                HumanMessage(content=prompt)
            ])

            improved_text = response.content.strip()


        # -------------------------------
        # 🔹 Step 2: Replace paragraph block
        # -------------------------------

        blocks = section.content or []

        if not isinstance(blocks, list):
            blocks = []

        new_blocks = []
        paragraph_found = False

        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "paragraph":
                paragraph_found = True
                new_blocks.append({
                    "type": "paragraph",
                    "content": improved_text
                })
            else:
                new_blocks.append(block)

        if not paragraph_found:
            new_blocks.append({
                "type": "paragraph",
                "content": improved_text
            })

        # -------------------------------
        # 🔹 Step 3: Save
        # -------------------------------

        section.content = new_blocks
        section.status = "draft"
        draft.status = "NEEDS_REVIEW"

        db.commit()
        db.refresh(section)

        return {"message": "Section updated and improved successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-questions")
def generate_questions(payload: QuestionRequest, db: Session = Depends(get_db)):
    """
    Generate clarification questions for missing inputs.

    Args:
        payload (QuestionRequest): Includes document and inputs.
        db (Session): Database session.

    Returns:
        dict: List of generated questions.
    """
    registry_doc = load_document_from_db(
        db=db,
        department=payload.department,
        document_filename=payload.document_filename
    )

    if not registry_doc:
        return {"questions": []}

    questions = generate_clarification_questions(
        registry_doc=registry_doc,
        company_profile=payload.company_profile,
        document_inputs=payload.document_inputs
    )

    return {"questions": questions}

@router.post("/publish-notion/{draft_id}")
def publish_to_notion(draft_id: int, db: Session = Depends(get_db)):
    """
    Publish a finalized draft to Notion.

    Args:
        draft_id (int): Draft ID.
        db (Session): Database session.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: 404 if draft or sections not found.
    """

    draft = db.query(Draft).filter(Draft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    sections = (
        db.query(DraftSection)
        .filter(DraftSection.draft_id == draft_id)
        .order_by(DraftSection.section_order.asc())
        .all()
    )

    if not sections:
        raise HTTPException(status_code=404, detail="Draft sections not found")

    sections_data = []

    for s in sections:

        blocks = s.content

        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks)
            except:
                blocks = []

        if not isinstance(blocks, list):
            blocks = []

        sections_data.append({
            "name": s.section_name,
            "blocks": blocks
        })

    doc_meta = db.query(Document).filter(
        func.lower(Document.document_name) == draft.document_name.lower(),
        func.lower(Document.department) == draft.department.lower()
    ).first()

    document_type = (doc_meta.internal_type.title() if doc_meta and doc_meta.internal_type else "Policy")
    company = db.query(CompanyProfile).first()
    company_name = company.company_name if company else "DocForge"
    industry = company.industry if company else "SaaS"

    logger.info(f"Publishing document: {draft.document_name}")
    logger.info(f"Doc type: {document_type}, Industry: {industry}")
    logger.info(f"Company: {company_name}")

    logger.info(f"DOCUMENT TYPE SENT TO NOTION: {document_type}")

    publish_document_to_notion(
        draft=draft,
        document_name=draft.document_name,
        sections=sections_data,
        version=int(draft.version),
        document_type=document_type,
        industry=industry,
        tags=[draft.department],
        created_by=company_name,
        created_at=str(draft.created_at)
    )
    db.commit()
    db.refresh(draft)

    return {"message": "Published to Notion successfully"}

@router.post("/rag-query")
def rag_query(data: dict):
    """
    Perform Retrieval-Augmented Generation (RAG) query.

    Features:
    - Rate limiting
    - Metadata filtering
    - Session tracking

    Args:
        data (dict): Includes question, session_id, filters.

    Returns:
        dict: RAG answer with context.

    Raises:
        HTTPException:
            400 if question missing
            429 if rate limit exceeded
    """
    question = data.get("question")
    session_id = data.get("session_id", "default_user")
    user_id = session_id   # better use same id

    logger.info(f"/rag-query called: {question}")

    if not question:
        logger.warning("RAG query missing question")
        raise HTTPException(status_code=400, detail="Question is required")

    # ✅ STEP 1: Rate limit FIRST
    if not check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for {user_id}")
        raise HTTPException(status_code=429, detail="Too many requests")

    filters = {
        "doc_type": data.get("doc_type"),
        "industry": data.get("industry"),
        "version": data.get("version")
    }

    # ✅ STEP 2: Run RAG
    result = answer_question(question, filters)

    # ✅ STEP 3: Store session
    update_session_history(session_id, question)

    logger.info("RAG query processed successfully")

    return result

@router.post("/rag-compare")
def rag_compare(data: dict):
    """
    Compare two documents using RAG.

    Args:
        data (dict): Includes doc_a, doc_b, and optional topic.

    Returns:
        dict: Comparison result.

    Raises:
        HTTPException: 400 if inputs missing.
    """

    doc_a = data.get("doc_a")
    doc_b = data.get("doc_b")
    topic = data.get("topic", "")
    version = data.get("version")

    logger.info(f"/rag-compare called: {doc_a} vs {doc_b} | Topic: {topic}")

    if not doc_a or not doc_b:
        raise HTTPException(status_code=400, detail="doc_a and doc_b required")

    # 🔥 STEP 1: Get available document names from retriever
    from backend.rag.notion_reader import get_all_document_titles

    available_docs = get_all_document_titles()

    # 🔥 STEP 2: Strict validation
    if doc_a not in available_docs:
        return {
            "answer": f"❌ Document A '{doc_a}' not found in knowledge base.\n\nAvailable documents:\n- " + "\n- ".join(available_docs),
            "sources": []
        }

    if doc_b not in available_docs:
        return {
            "answer": f"❌ Document B '{doc_b}' not found in knowledge base.\n\nAvailable documents:\n- " + "\n- ".join(available_docs),
            "sources": []
        }

    # 🔥 STEP 3: Only if valid → run comparison
    return compare_documents(doc_a, doc_b, topic,version)

@router.post("/rag-summarize")
def rag_summarize(data: dict):
    """
    Summarize documents using RAG.

    Args:
        data (dict): Includes query and filters.

    Returns:
        dict: Summary output.

    Raises:
        HTTPException: 400 if query missing.
    """

    query = data.get("query")
    logger.info(f"/rag-summarize called: {query}")

    filters = {
        "doc_type": data.get("doc_type"),
        "industry": data.get("industry"),
        "version": data.get("version")
    }

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    return summarize_document(query, filters)

@router.post("/rag-evaluate")
def rag_evaluate():
    """
    Run evaluation on RAG system using predefined metrics.

    Metrics:
    - Faithfulness
    - Answer relevancy

    Returns:
        dict: Evaluation results and averages.
    """

    logger.info("/rag-evaluate started")

    df = run_evaluation()

    if df is None or df.empty:
        raise HTTPException(
            status_code=500,
            detail="Evaluation failed: No data returned"
        )

    logger.info("Evaluation completed")

    return {
        "message": "Evaluation completed",
        "data": df.to_dict(orient="records"),
        "avg_faithfulness": float(df["faithfulness"].mean()),
        "avg_relevancy": float(df["answer_relevancy"].mean()),
        "avg_context_precision": float(df["context_precision"].mean()),
        "avg_context_recall": float(df["context_recall"].mean())
    }


@router.post("/statecase-chat")
def statecase_chat(data: dict, background_tasks: BackgroundTasks):
    """
    Stateful assistant endpoint using LangGraph.
    """
    trace_id = str(uuid.uuid4())
    print("TRACE ID:", trace_id)

    question = data.get("question")
    session_id = data.get("session_id", "default")

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    # Get memory from Redis
    session_data = get_user_session(session_id)

    history = session_data.get("history") or []
    context = session_data.get("context") or {}
    doc_set = context.get("doc_set", [])

    # Use stored context if not provided
    industry = data.get("industry") or context.get("industry")
    doc_type = data.get("doc_type") or context.get("doc_type")
    version = data.get("version") or context.get("version")

    # Initialize state
    state: StateCaseState = {
        "question": question,
        "industry": industry,
        "doc_type": doc_type,
        "version": version,
        "history": history,
        "retrieved_chunks": [],
        "answer": None,
        "confidence": 0,
        "needs_clarification": False,
        "is_out_of_domain": False,  
        "should_escalate": False,
        "ticket_created": False,
        "clarification_question": None,
        "trace_id": trace_id,
        "session_id": session_id,
        "doc_set": doc_set,
    }

    # Run LangGraph
    result = statecase_graph.invoke(state)

    # 🔥 Async ticket creation
    if result.get("should_escalate") and not result.get("is_out_of_domain", False):
        from backend.statecase.ticketing import create_ticket

        background_tasks.add_task(
            create_ticket,
            question=question,
            context=state.get("retrieved_chunks"),
            filters={
                "doc_type": doc_type,
                "industry": industry,
                "version": version
            },
            confidence=result.get("confidence"),
            history=history,
            sources=result.get("sources"),
            user_id=session_id
        )

    # Store doc set (sources used in this query)
    if result.get("sources"):
        context["doc_set"] = result.get("sources")

    # 🔥 Track last used document/source
    if result.get("sources"):
        context["last_doc"] = result["sources"][0]

    # Update context (only overwrite if new values provided)
    if data.get("industry"):
        context["industry"] = data.get("industry")

    if data.get("doc_type"):
        context["doc_type"] = data.get("doc_type")

    if data.get("version"):
        context["version"] = data.get("version")

    # Save updated history
    history.append({
        "role": "user",
        "message": question
    })

    history.append({
        "role": "assistant",
        "message": result.get("answer")
    })

    history = history[-10:]

    # Save session
    save_user_session(session_id, {
        "history": history,
        "context": context
    })

    print("GRAPH RESULT:", result)

    # 🔥 Override answer for async case
    if result.get("should_escalate"):
        answer = "⚠️ I couldn't find a reliable answer. A ticket is being created."
    else:
        answer = result.get("answer")

    return {
        "answer": answer,
        "confidence": result.get("confidence"),
        "sources": result.get("sources", []),
        "escalated": result.get("should_escalate", False),
        "needs_clarification": result.get("needs_clarification", False),
        "trace_id": trace_id
    }


@router.post("/update-ticket")
def update_ticket(data: dict):
    ticket_id = data.get("ticket_id")
    status = data.get("status")

    if not ticket_id or not status:
        raise HTTPException(status_code=400, detail="ticket_id and status required")

    from backend.statecase.ticketing import update_ticket_status

    success = update_ticket_status(ticket_id, status)

    return {
        "success": success,
        "message": f"Updated to {status}" if success else "Failed"
    }