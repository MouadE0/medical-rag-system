from typing import List
import openai
from openai import OpenAI
import numpy as np
from tqdm import tqdm

from ..config import settings


class EmbeddingGenerator:
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self.dimensions = settings.openai_embedding_dimensions
        
    def generate_embedding(self, text: str) -> List[float]:

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.dimensions
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:

        embeddings = []
        
        print(f"Generating embeddings for {len(texts)} texts...")
        
        max_chars = 30000
        truncated_texts = []
        for text in texts:
            if len(text) > max_chars:
                truncated_texts.append(text[:max_chars] + "...[truncated]")
            else:
                truncated_texts.append(text)
        
        for i in tqdm(range(0, len(truncated_texts), batch_size)):
            batch = truncated_texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float"
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"Error in batch {i//batch_size}: {e}")
                embeddings.extend([[0.0] * self.dimensions] * len(batch))
        
        return embeddings
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)