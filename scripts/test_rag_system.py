import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.vector_store import VectorStore
from src.infrastructure.embeddings import EmbeddingGenerator
from src.infrastructure.llm_client import LLMClient
from src.application.rag_pipeline import RAGPipeline


TEST_CASES = [
    "Dyspnée à l'effort et à la parole",
    "Toux purulente",
    "Fièvre",
    "Pneumopathie à Haemophilus influenzae",
    "Insuffisance respiratoire aiguë hypoxémique",
    "Sepsis à staphylocoques",
]


def main():
    print("="*80)
    print("TESTING RAG SYSTEM")
    print("="*80)
    
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    llm_client = LLMClient()
    
    rag_pipeline = RAGPipeline(vector_store, embedding_gen, llm_client)
    
    print(f"\n Vector store loaded: {vector_store.count()} documents")
    
    for i, query in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(TEST_CASES)}: {query}")
        print(f"{'='*80}")
        
        result = rag_pipeline.suggest_codes(query, top_k=3)
        
        print(f"\n  Processing time: {result.processing_time_ms:.0f}ms")
        print(f"\n Suggestions:")
        
        for j, suggestion in enumerate(result.suggestions, 1):
            print(f"\n{j}. {suggestion.code} - {suggestion.label}")
            print(f"   Score: {suggestion.relevance_score:.2f}")
            print(f"   Explanation: {suggestion.explanation[:200]}...")
            if suggestion.exclusions:
                print(f"   Exclusions: {len(suggestion.exclusions)} items")
    
    print("\n" + "="*80)
    print(" ALL TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()