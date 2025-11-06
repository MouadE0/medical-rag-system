from typing import List, Dict
from rank_bm25 import BM25Okapi
import re

from ..infrastructure.vector_store import VectorStore
from ..infrastructure.embeddings import EmbeddingGenerator
from ..config import settings


class HybridRetriever:
    
    def __init__(self, vector_store: VectorStore, embedding_generator: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        
        self.bm25 = None
        self.bm25_docs = None
        self.bm25_ids = None
        self.bm25_metadata = None
    
    def _build_bm25_index(self):
        print("Building BM25 index...")
        
        all_docs = self.vector_store.collection.get(include=["documents", "metadatas"])
        
        self.bm25_docs = all_docs['documents']
        self.bm25_ids = all_docs['ids']
        self.bm25_metadata = all_docs['metadatas']
        
        tokenized_docs = [self._tokenize(doc) for doc in self.bm25_docs]
        
        self.bm25 = BM25Okapi(tokenized_docs)
        
        print(f" BM25 index built with {len(self.bm25_docs)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        # Lowercase and split by non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def retrieve_semantic(self, query: str, top_k: int = 10) -> List[Dict]:
        query_embedding = self.embedding_generator.generate_embedding(query)
        results = self.vector_store.search(query_embedding, top_k=top_k)
        return results
    
    def retrieve_keyword(self, query: str, top_k: int = 10) -> List[Dict]:
        if self.bm25 is None:
            self._build_bm25_index()
        
        query_tokens = self._tokenize(query)
        
        scores = self.bm25.get_scores(query_tokens)
        
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'id': self.bm25_ids[idx],
                'document': self.bm25_docs[idx],
                'bm25_score': float(scores[idx]),
                'metadata': self.bm25_metadata[idx] if self.bm25_metadata else {}
            })
        
        return results
    
    def retrieve_hybrid(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict]:

        semantic_results = self.retrieve_semantic(query, top_k=top_k * 2)
        keyword_results = self.retrieve_keyword(query, top_k=top_k * 2)
        
        def normalize_scores(results, score_key):
            if not results:
                return results
            
            scores = [r.get(score_key, 0) for r in results]
            max_score = max(scores) if scores else 1.0
            min_score = min(scores) if scores else 0.0
            
            if max_score == min_score:
                for r in results:
                    r[f'{score_key}_norm'] = 1.0
            else:
                for r in results:
                    r[f'{score_key}_norm'] = (r.get(score_key, 0) - min_score) / (max_score - min_score)
            
            return results
        
        semantic_results = normalize_scores(semantic_results, 'similarity')
        keyword_results = normalize_scores(keyword_results, 'bm25_score')
        
        merged = {}
        
        for result in semantic_results:
            doc_id = result['id']
            merged[doc_id] = result
            merged[doc_id]['hybrid_score'] = semantic_weight * result.get('similarity_norm', 0)
        
        for result in keyword_results:
            doc_id = result['id']
            if doc_id in merged:
                merged[doc_id]['hybrid_score'] += keyword_weight * result.get('bm25_score_norm', 0)
            else:
                merged[doc_id] = result
                merged[doc_id]['hybrid_score'] = keyword_weight * result.get('bm25_score_norm', 0)
        
        sorted_results = sorted(merged.values(), key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        return sorted_results[:top_k]