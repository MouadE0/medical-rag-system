from typing import List, Dict
import time

from ..infrastructure.vector_store import VectorStore
from ..infrastructure.embeddings import EmbeddingGenerator
from ..infrastructure.llm_client import LLMClient
from .retriever import HybridRetriever
from .query_processor import QueryProcessor
from ..domain.entities import CodeSuggestion, QueryResult
from ..config import settings


class RAGPipeline:
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        llm_client: LLMClient
    ):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.llm_client = llm_client
        
        self.retriever = HybridRetriever(vector_store, embedding_generator)
        self.query_processor = QueryProcessor()
    
    def suggest_codes(
        self,
        query: str,
        top_k: int = 5,
        use_reranking: bool = True
    ) -> QueryResult:

        start_time = time.time()
        

        processed_query = self.query_processor.process(query)
        search_query = processed_query['search_query']
        
        candidates = self.retriever.retrieve_hybrid(
            search_query,
            top_k=settings.top_k_retrieval,
            semantic_weight=settings.semantic_weight,
            keyword_weight=settings.keyword_weight
        )
        
        if use_reranking and len(candidates) > 0:
            candidates = self.llm_client.rerank_candidates(
                query,
                candidates,
                top_k=settings.top_k_rerank
            )
        else:
            candidates = candidates[:top_k]
        
        suggestions = self._generate_suggestions(query, candidates)
        
        processing_time = (time.time() - start_time) * 1000  # ms
        

        result = QueryResult(
            query=query,
            suggestions=suggestions,
            processing_time_ms=processing_time,
            retrieval_metadata={
                'candidates_retrieved': len(candidates),
                'reranking_used': use_reranking,
                'mentioned_codes': processed_query['mentioned_codes']
            }
        )
        
        return result
    
    def _generate_suggestions(self, query: str, candidates: List[Dict]) -> List[CodeSuggestion]:

        if not candidates:
            return []
        
        system_prompt = """
            Tu es un expert en codage médical CIM-10 utilisant le référentiel CoCoA.

            Pour chaque code CIM-10 suggéré, tu dois:
            1. Expliquer POURQUOI ce code correspond à la requête
            2. Citer les règles CoCoA pertinentes (exclusions, inclusions)
            3. Mentionner les précautions de codage

            Retourne un JSON avec cette structure exacte:
            {
            "suggestions": [
                    {
                    "code": "A41.0",
                    "label": "Sepsis à staphylocoques dorés",
                    "relevance_score": 0.95,
                    "explanation": "Ce code correspond car...",
                    "cocoa_rules": "À l'exclusion de: sepsis néonatal (P36.-)",
                    "exclusions": ["P36.-", "O85"],
                    "inclusions": ["septicémie à staphylocoque doré"],
                    "coding_instructions": ["Utiliser code supplémentaire R57.2 pour choc septique"],
                    "chapter": "I",
                    "priority": "4"
                    }
                ]
            }
        """


        context = "\n\n".join([
            f"--- Code {i+1} ---\n{c['document']}"
            for i, c in enumerate(candidates[:5])
        ])
        
        user_message = f"""Requête du médecin: "{query}"

            Codes candidats du référentiel CoCoA:
            {context}

            Suggère les codes les plus pertinents avec explications détaillées.
        """

        llm_response = self.llm_client.generate_json_response(
            system_prompt,
            user_message,
            temperature=0.2
        )
        
        suggestions = []
        
        if "error" in llm_response:
            for i, candidate in enumerate(candidates[:5]):
                metadata = candidate.get('metadata', {})
                code = metadata.get('primary_code', 'UNKNOWN')
                label = metadata.get('label', 'Code CIM-10')
                
                suggestions.append(CodeSuggestion(
                    code=code,
                    label=label,
                    relevance_score=candidate.get('rerank_score', candidate.get('hybrid_score', 0.5)),
                    explanation=f"Ce code a été trouvé dans le référentiel CoCoA avec un score de similarité élevé.",
                    cocoa_rules=None,
                    source_chunks=[candidate['id']]
                ))
        else:
            for item in llm_response.get('suggestions', [])[:5]:
                suggestions.append(CodeSuggestion(
                    code=item.get('code', 'Unknown'),
                    label=item.get('label', ''),
                    relevance_score=item.get('relevance_score', 0.5),
                    explanation=item.get('explanation', ''),
                    cocoa_rules=item.get('cocoa_rules'),
                    exclusions=item.get('exclusions', []),
                    inclusions=item.get('inclusions', []),
                    coding_instructions=item.get('coding_instructions', []),
                    chapter=item.get('chapter'),
                    priority=item.get('priority'),
                    source_chunks=[c['id'] for c in candidates[:5]]
                ))
        
        return suggestions
    
    def lookup_code(self, code: str) -> Dict:

        result = self.vector_store.get_by_code(code)
        
        if result:
            return {
                'found': True,
                'code': code,
                'document': result['document'],
                'metadata': result['metadata']
            }
        else:
            return {
                'found': False,
                'code': code,
                'message': f"Code {code} non trouvé dans le référentiel"
            }