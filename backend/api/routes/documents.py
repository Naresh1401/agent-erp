"""Document upload & semantic search routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.orchestrator import orchestrator
from backend.api.schemas import DocumentOut, DocumentUpload, SemanticSearchRequest
from backend.db.database import get_db
from backend.db.models import Document
from backend.services.llm_service import LLMService, get_llm_service
from backend.services.vector_store import VectorStoreService, get_vector_store

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    payload: DocumentUpload,
    db: AsyncSession = Depends(get_db),
):
    """Upload a document and process it with the Document Processor agent."""
    doc = Document(filename=payload.filename, raw_text=payload.raw_text, status="processing")
    db.add(doc)
    await db.flush()

    # Dispatch to document processor agent
    result = await orchestrator.dispatch(
        "document_processor",
        {"filename": payload.filename, "raw_text": payload.raw_text, "document_id": str(doc.id)},
        db,
    )

    # Update document with results
    agent_result = result.get("result", {})
    doc.structured_data = agent_result.get("extracted_fields", {})
    doc.status = "processed" if result["status"] == "completed" else "failed"
    await db.flush()

    return doc


@router.post("/search")
async def semantic_search(payload: SemanticSearchRequest):
    """Search documents using semantic similarity."""
    llm_svc = get_llm_service()
    vs = get_vector_store()

    query_embedding = await llm_svc.embed(payload.query)
    results = vs.search(query_embedding, limit=payload.limit)
    return {"query": payload.query, "results": results}
