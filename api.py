import logging
import shutil
import tempfile
from pathlib import Path
from threading import Lock

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.retrieval import answer_question, source_name
from backend.vectorstore import DEFAULT_INDEX, add_documents


logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Ask your PDF")
index_lock = Lock()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Question(BaseModel):
    question: str


@app.get(
    "/health",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "The application is working correctly"}
                }
            }
        }
    },
)
def health():
    return {"message": "The application is working correctly"}


@app.post(
    "/upload",
    responses={
        200: {
            "description": "PDF indexed successfully",
            "content": {
                "application/json": {"example": {"filename": "document.pdf", "chunks": 12}}
            },
        },
        400: {
            "description": "The uploaded file is not a PDF",
            "content": {"application/json": {"example": {"detail": "Please upload a PDF file."}}},
        },
        500: {
            "description": "PDF processing failed",
            "content": {"application/json": {"example": {"detail": "Could not process the PDF."}}},
        },
    },
)
def upload(file: UploadFile = File(..., description="Select a PDF file, such as document.pdf.")):
    filename = Path((file.filename or "").replace("\\", "/")).name
    if Path(filename).suffix.lower() != ".pdf":
        logger.warning("Upload rejected: file is not a PDF")
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    try:
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / filename
            with pdf_path.open("wb") as output:
                shutil.copyfileobj(file.file, output)
            with index_lock:
                chunks = add_documents([pdf_path])
    except Exception:
        logger.exception("PDF processing failed")
        raise HTTPException(status_code=500, detail="Could not process the PDF.")

    logger.info("PDF indexed: %s chunks", chunks)
    return {"filename": filename, "chunks": chunks}


@app.post(
    "/ask",
    responses={
        200: {
            "description": "Answer and retrieved sources",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "The document describes the project goals. [1]",
                        "sources": [{"number": 1, "filename": "document.pdf"}],
                    }
                }
            },
        },
        400: {
            "description": "The question is empty",
            "content": {"application/json": {"example": {"detail": "Question cannot be empty."}}},
        },
        404: {
            "description": "No PDF has been indexed",
            "content": {"application/json": {"example": {"detail": "Upload a PDF first."}}},
        },
        500: {
            "description": "Question answering failed",
            "content": {"application/json": {"example": {"detail": "Could not answer the question."}}},
        },
    },
)
def ask(
    request: Question = Body(
        ...,
        openapi_examples={
            "document_question": {
                "summary": "Ask about the uploaded document",
                "value": {"question": "What is this document about?"},
            }
        },
    ),
):
    if not request.question.strip():
        logger.warning("Question rejected: empty question")
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        with index_lock:
            if not (DEFAULT_INDEX / "index.faiss").exists():
                raise HTTPException(status_code=404, detail="Upload a PDF first.")
            answer, sources = answer_question(request.question.strip())
    except HTTPException:
        raise
    except Exception:
        logger.exception("Question answering failed")
        raise HTTPException(status_code=500, detail="Could not answer the question.")
    logger.info("Question answered: %s sources", len(sources))
    return {
        "answer": answer,
        "sources": [
            {"number": number, "filename": source_name(source)}
            for number, source in enumerate(sources, 1)
        ],
    }
