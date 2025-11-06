from fastapi import APIRouter, HTTPException, Depends
from typing import Dict

from .schema import (
    CodeSuggestionRequest,
    QueryResponse,
    CodeLookupRequest,
    CodeLookupResponse,
    HealthResponse
)
from ..application.rag_pipeline import RAGPipeline
from ..infrastructure.vector_store import VectorStore
from ..infrastructure.embeddings import EmbeddingGenerator
from ..infrastructure.llm_client import LLMClient
from ..infrastructure.auth import get_current_user

vector_store = VectorStore()
embedding_generator = EmbeddingGenerator()
llm_client = LLMClient()

rag_pipeline = RAGPipeline(vector_store, embedding_generator, llm_client)

router = APIRouter()


@router.post("/suggest-codes", response_model=QueryResponse)
async def suggest_codes(
    request: CodeSuggestionRequest,
    current_user: dict = Depends(get_current_user)
):

    try:
        result = rag_pipeline.suggest_codes(
            query=request.query,
            top_k=request.top_k,
            use_reranking=request.use_reranking
        )
        
        return QueryResponse(
            query=result.query,
            suggestions=[
                {
                    'code': s.code,
                    'label': s.label,
                    'relevance_score': s.relevance_score,
                    'explanation': s.explanation,
                    'cocoa_rules': s.cocoa_rules,
                    'exclusions': s.exclusions,
                    'inclusions': s.inclusions,
                    'coding_instructions': s.coding_instructions,
                    'chapter': s.chapter,
                    'priority': s.priority
                }
                for s in result.suggestions
            ],
            processing_time_ms=result.processing_time_ms,
            retrieval_metadata=result.retrieval_metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lookup-code", response_model=CodeLookupResponse)
async def lookup_code(
    request: CodeLookupRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Look up a specific CIM-10 code.
    
    Example request:
    ```json
        {
        "code": "A41.0"
        }
    ```
    """
    try:
        result = rag_pipeline.lookup_code(request.code)
        return CodeLookupResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():

    return HealthResponse(
        status="healthy",
        vector_store_count=vector_store.count()
    )