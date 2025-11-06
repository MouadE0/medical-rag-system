from typing import List, Dict, Optional
from openai import OpenAI
import json

from ..config import settings


class LLMClient:
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        print(f"LLMClient initialized with model: {self.model}")
    
    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f" Error generating response: {e}")
            return f"Error: {str(e)}"
    
    def generate_json_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2
    ) -> Dict:
        """
        Generate a JSON response from GPT-4.
        
        Args:
            system_prompt: System instructions
            user_message: User query
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON dict
        """
        try:
            print(f" Calling LLM with model: {self.model}")
            print(f"   Temperature: {temperature}")
            print(f"   User message length: {len(user_message)} chars")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            print(f" LLM response received: {len(content)} chars")
            
            parsed = json.loads(content)
            print(f" JSON parsed successfully")
            return parsed
            
        except json.JSONDecodeError as e:
            print(f" Error parsing JSON: {e}")
            print(f"   Raw content: {content[:500]}...")
            return {"error": "Invalid JSON response"}
        except Exception as e:
            print(f" Error generating JSON response: {e}")
            print(f"   Error type: {type(e).__name__}")
            return {"error": str(e)}
    
    def rerank_candidates(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:

        if not candidates:
            print(" No candidates to rerank")
            return []
        
        print(f" Re-ranking {len(candidates)} candidates...")
        
        system_prompt = """
            Tu es un expert en codage médical CIM-10 avec le référentiel CoCoA.

            Évalue la pertinence de chaque code CIM-10 par rapport à la requête médicale.

            Retourne un JSON avec cette structure:
            {
            "rankings": [
                {
                "code": "A41.0",
                "relevance_score": 0.95,
                "reasoning": "Correspond exactement à la description..."
                }
            ]
            }

            Critères d'évaluation:
            1. Correspondance sémantique avec la requête
            2. Respect des règles d'exclusion CoCoA
            3. Spécificité du code (privilégier codes précis)
            4. Contexte clinique approprié
        """

        candidates_text = "\n\n".join([
            f"Code: {c['metadata'].get('primary_code', 'UNKNOWN')}\n"
            f"Libellé: {c['metadata'].get('label', 'N/A')}\n"
            f"Extrait: {c['document'][:300]}..."
            for c in candidates[:15] 
        ])
        
        user_message = f"""Requête: "{query}"

            Codes candidats:
            {candidates_text}

            Classe ces codes par pertinence (top {top_k}).
        """

        result = self.generate_json_response(system_prompt, user_message)
        
        if "error" in result:
            print(" Re-ranking failed, using original order")
            return candidates[:top_k]
        
        rankings = result.get("rankings", [])
        print(f" Re-ranked {len(rankings)} candidates")
        
        score_map = {}
        for r in rankings:
            code = r.get("code", "")
            score = r.get("relevance_score", 0.5)
            score_map[code] = score
        
        for candidate in candidates:
            code = candidate['metadata'].get('primary_code', '')
            if code in score_map:
                candidate['rerank_score'] = score_map[code]
            else:
                candidate['rerank_score'] = candidate.get('similarity', 0.5) * 0.5
        
        reranked = sorted(candidates, key=lambda x: x.get('rerank_score', 0), reverse=True)
        
        return reranked[:top_k]