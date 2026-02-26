from fastapi import FastAPI
from backend.api.routes import documents
from backend.approval import routes as approval_routes
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="DocForge Hub API",
    description="Backend API for document generation and publishing",
    version="1.0.0"
)

app.include_router(documents.router)
app.include_router(approval_routes.router)


@app.get("/")
def health_check():
    return {"status": "ok"}


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")