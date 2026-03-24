"""Document Processing Agent – extracts structured data from legacy documents.

Uses LangGraph to build a multi-step pipeline:
  1. Parse raw text from PDF / DOCX / CSV
  2. Classify document type (invoice, PO, inventory report)
  3. Extract structured fields via LLM
  4. Validate & store results
  5. Generate embedding for semantic search
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import END, StateGraph

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DocState(TypedDict):
    task_id: str
    filename: str
    raw_text: str
    doc_type: str
    extracted_fields: dict[str, Any]
    embedding: list[float]
    validation_errors: list[str]
    steps_completed: list[str]
    error: str


# ── LLM instances ───────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)
embeddings = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)


# ── Node functions ──────────────────────────────────────────
def classify_document(state: DocState) -> DocState:
    """Classify the document type using LLM."""
    messages = [
        SystemMessage(content=(
            "You are a document classifier for an ERP system. "
            "Classify the following document into exactly one of: "
            "invoice, purchase_order, inventory_report, shipping_manifest, credit_memo, unknown. "
            "Respond with ONLY the classification label."
        )),
        HumanMessage(content=f"Filename: {state['filename']}\n\nContent:\n{state['raw_text'][:3000]}"),
    ]
    response = llm.invoke(messages)
    doc_type = response.content.strip().lower().replace(" ", "_")
    return {
        **state,
        "doc_type": doc_type,
        "steps_completed": [*state["steps_completed"], "classify"],
    }


EXTRACTION_SCHEMAS = {
    "invoice": {
        "invoice_number": "string",
        "date": "YYYY-MM-DD",
        "vendor_name": "string",
        "line_items": [{"description": "string", "quantity": "number", "unit_price": "number", "total": "number"}],
        "subtotal": "number",
        "tax": "number",
        "total": "number",
        "payment_terms": "string",
    },
    "purchase_order": {
        "po_number": "string",
        "date": "YYYY-MM-DD",
        "vendor_name": "string",
        "ship_to": "string",
        "line_items": [{"sku": "string", "description": "string", "quantity": "number", "unit_price": "number"}],
        "total": "number",
    },
    "inventory_report": {
        "report_date": "YYYY-MM-DD",
        "warehouse": "string",
        "items": [{"sku": "string", "name": "string", "quantity_on_hand": "number", "location": "string"}],
    },
}


def extract_fields(state: DocState) -> DocState:
    """Extract structured fields from the document using LLM."""
    schema = EXTRACTION_SCHEMAS.get(state["doc_type"], {"raw_content": "string"})
    messages = [
        SystemMessage(content=(
            "You are a data extraction agent for an ERP system. "
            "Extract structured data from the document below. "
            f"Return valid JSON matching this schema:\n{json.dumps(schema, indent=2)}\n"
            "If a field is not found, use null. Return ONLY the JSON object."
        )),
        HumanMessage(content=state["raw_text"][:6000]),
    ]
    response = llm.invoke(messages)
    try:
        extracted = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        extracted = {"raw_response": response.content}

    return {
        **state,
        "extracted_fields": extracted,
        "steps_completed": [*state["steps_completed"], "extract"],
    }


def validate_extraction(state: DocState) -> DocState:
    """Validate extracted fields for obvious errors."""
    errors: list[str] = []
    fields = state["extracted_fields"]

    if state["doc_type"] == "invoice":
        if not fields.get("invoice_number"):
            errors.append("Missing invoice_number")
        if fields.get("total") is not None and fields.get("subtotal") is not None:
            if isinstance(fields["total"], (int, float)) and isinstance(fields["subtotal"], (int, float)):
                if fields["total"] < fields["subtotal"]:
                    errors.append("Total is less than subtotal")

    if state["doc_type"] == "purchase_order":
        if not fields.get("po_number"):
            errors.append("Missing po_number")

    return {
        **state,
        "validation_errors": errors,
        "steps_completed": [*state["steps_completed"], "validate"],
    }


def generate_embedding(state: DocState) -> DocState:
    """Generate vector embedding of the document for semantic search."""
    text_for_embedding = f"{state['doc_type']}: {state['filename']}\n{state['raw_text'][:2000]}"
    embedding = embeddings.embed_query(text_for_embedding)
    return {
        **state,
        "embedding": embedding,
        "steps_completed": [*state["steps_completed"], "embed"],
    }


def handle_error(state: DocState) -> DocState:
    """Handle errors gracefully."""
    return {**state, "error": "Processing failed – see validation_errors"}


# ── Routing ─────────────────────────────────────────────────
def should_continue(state: DocState) -> str:
    if state.get("validation_errors"):
        return "handle_error"
    return "generate_embedding"


# ── Build the graph ─────────────────────────────────────────
def build_document_processor_graph() -> StateGraph:
    graph = StateGraph(DocState)

    graph.add_node("classify", classify_document)
    graph.add_node("extract", extract_fields)
    graph.add_node("validate", validate_extraction)
    graph.add_node("generate_embedding", generate_embedding)
    graph.add_node("handle_error", handle_error)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "extract")
    graph.add_edge("extract", "validate")
    graph.add_conditional_edges("validate", should_continue, {
        "generate_embedding": "generate_embedding",
        "handle_error": "handle_error",
    })
    graph.add_edge("generate_embedding", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


document_processor = build_document_processor_graph()
