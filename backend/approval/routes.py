from fastapi import APIRouter
from .store import create_request, list_pending, approve

router = APIRouter(prefix="/approval", tags=["Approval"])


@router.post("/request")
def request_approval(payload: dict):
    return create_request(
        payload["department"],
        payload["document_filename"]
    )


@router.get("/pending")
def pending_approvals():
    return list_pending()


@router.post("/approve/{request_id}")
def approve_request(request_id: str):
    return approve(request_id)
