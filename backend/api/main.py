from fastapi import FastAPI
from backend.api.routes import documents
from fastapi.staticfiles import StaticFiles
import threading
from contextlib import asynccontextmanager
from backend.rag.background_indexer import start_auto_indexing


@asynccontextmanager
async def lifespan(app: FastAPI):
    #  Startup logic
    thread = threading.Thread(target=start_auto_indexing, daemon=True)
    thread.start()

    yield

    #  Shutdown logic
    print("Shutting down...")


#  SINGLE APP ONLY
app = FastAPI(
    title="DocForge Hub API",
    description="Backend API for document generation and publishing",
    version="1.0.0",
    lifespan=lifespan
)

#  Add routes AFTER app creation
app.include_router(documents.router)


@app.get("/")
def health_check():
    return {"status": "ok"}


app.mount("/diagrams", StaticFiles(directory="uploads/diagrams"), name="diagrams")