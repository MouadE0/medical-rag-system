from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path

from ..domain.entities import DocumentChunk
from ..config import settings


class VectorStore:
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection_name = "cocoa_codes"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "CIM-10 CoCoA codes and rules"}
            )
        
        print(f"Vector store initialized: {self.collection.count()} documents")
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):

        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings")
        
        print(f"Adding {len(chunks)} chunks to vector store...")
        
        ids = []
        documents = []
        metadatas = []
        embeddings_clean = []
        
        seen_ids = set()
        skipped_zero = 0
        skipped_duplicate = 0
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if all(e == 0.0 for e in embedding):
                skipped_zero += 1
                continue
            
            chunk_id = chunk.chunk_id
            original_id = chunk_id
            counter = 1
            while chunk_id in seen_ids:
                chunk_id = f"{original_id}_{counter}"
                counter += 1
                skipped_duplicate += 1
            
            seen_ids.add(chunk_id)
            ids.append(chunk_id)
            documents.append(chunk.content)
            embeddings_clean.append(embedding)
            
            clean_metadata = {}
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    
                    if value and isinstance(value[0], str):
                        clean_metadata[key] = ','.join(str(v) for v in value[:10])
                elif value is None:
                    clean_metadata[key] = ""
            
            clean_metadata['page_number'] = chunk.page_number
            
            metadatas.append(clean_metadata)
        
        if skipped_zero > 0:
            print(f" Skipped {skipped_zero} chunks with zero embeddings")
        if skipped_duplicate > 0:
            print(f" Renamed {skipped_duplicate} duplicate chunk IDs")
        
        batch_size = 1000
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            
            self.collection.add(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                embeddings=embeddings_clean[i:batch_end],
                metadatas=metadatas[i:batch_end]
            )
            print(f" Progress: {batch_end}/{len(ids)} chunks added...")
        
        print(f" Added {len(ids)} chunks. Total in store: {self.collection.count()}")
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 10,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'similarity': 1 - results['distances'][0][i]
            })
        
        return formatted_results
    
    def get_by_code(self, code: str) -> Optional[Dict]:

        results = self.collection.get(
            where={"primary_code": code},
            include=["documents", "metadatas"]
        )
        
        if results['ids']:
            return {
                'id': results['ids'][0],
                'document': results['documents'][0],
                'metadata': results['metadatas'][0]
            }
        
        return None
    
    def count(self) -> int:
        return self.collection.count()
    
    def clear(self):
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "CIM-10 CoCoA codes and rules"}
        )
        print("Vector store cleared")