from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class CodeSuggestionRequest(BaseModel):

    query: str = Field(..., description="Medical symptom or diagnosis description", min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10, description="Number of suggestions")
    use_reranking: bool = Field(default=True, description="Use LLM re-ranking")


class CodeSuggestionResponse(BaseModel):

    code: str
    label: str
    relevance_score: float
    explanation: str
    cocoa_rules: Optional[str] = None
    exclusions: List[str] = []
    inclusions: List[str] = []
    coding_instructions: List[str] = []
    chapter: Optional[str] = None
    priority: Optional[str] = None


class QueryResponse(BaseModel):

    query: str
    suggestions: List[CodeSuggestionResponse]
    processing_time_ms: float
    retrieval_metadata: Dict


class CodeLookupRequest(BaseModel):

    code: str = Field(..., description="CIM-10 code", pattern=r'^[A-Z]\d{2}\.?\d?$')


class CodeLookupResponse(BaseModel):

    found: bool
    code: str
    document: Optional[str] = None
    metadata: Optional[Dict] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):

    status: str
    vector_store_count: int
    version: str = "1.0.0"