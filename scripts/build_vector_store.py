"""
Build the vector store from CoCoA PDF.
To RUN ONCE to create the database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.pdf_processor import process_cocoa_pdf
from src.infrastructure.embeddings import EmbeddingGenerator
from src.infrastructure.vector_store import VectorStore
from src.config import settings


def main():
    print("="*80)
    print("BUILDING VECTOR STORE FROM COCOA PDF")
    print("="*80)
    
    # 1. Process PDF
    print("\n Step 1: Processing CoCoA PDF...")
    chunks = process_cocoa_pdf(settings.cocoa_pdf_path)
    print(f"Created {len(chunks)} chunks")
    
    # 2. Generate embeddings
    print("\n Step 2: Generating embeddings...")
    embedding_gen = EmbeddingGenerator()
    
    texts = [chunk.content for chunk in chunks]
    embeddings = embedding_gen.generate_embeddings_batch(texts, batch_size=100)
    print(f"Generated {len(embeddings)} embeddings")
    
    # 3. Add to embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding
    
    # 4. Store in vector database
    print("\n Step 3: Storing in ChromaDB...")
    vector_store = VectorStore()
    
    vector_store.clear()
    
    vector_store.add_chunks(chunks, embeddings)
    print(f"Vector store built with {vector_store.count()} documents")
    
    print("\n" + "="*80)
    print("VECTOR STORE BUILD COMPLETE!")
    print("="*80)
    print(f"\nLocation: {settings.chroma_persist_dir}")
    print(f"Total documents: {vector_store.count()}")
    print("\nYou can now run the API: python -m src.api.main")


if __name__ == "__main__":
    main()