import re
from typing import List, Dict


class QueryProcessor:
    
    def __init__(self):
        
        self.synonyms = {
            'dyspnée': ['essoufflement', 'difficulté respiratoire', 'respiration difficile'],
            'fièvre': ['hyperthermie', 'température élevée', 'pyrexie'],
            'toux': ['expectoration', 'tussigène'],
            'douleur': ['algie', 'souffrance'],
            'infection': ['sepsis', 'septique', 'infectieux'],
            'inflammation': ['inflammatoire', 'enflammé'],
            # Can be improved
        }
    
    def clean_query(self, query: str) -> str:

        query = ' '.join(query.split())
        query = query.lower()
        query = re.sub(r'[^\w\s\-àâäéèêëïîôùûüÿæœç]', ' ', query)
        
        return query.strip()
    
    def extract_codes(self, query: str) -> List[str]:
        
        code_pattern = r'\b([A-Z]\d{2}\.?\d?)\b'
        codes = re.findall(code_pattern, query.upper())
        
        codes = [c for c in codes if c not in ['SAI', 'NCA']]
        
        return codes
    
    def expand_query(self, query: str) -> str:

        expanded = query
        
        for term, synonyms in self.synonyms.items():
            if term in query.lower():
                expanded += ' ' + ' '.join(synonyms)
        
        return expanded
    
    def process(self, query: str) -> Dict:

        cleaned = self.clean_query(query)
        
        mentioned_codes = self.extract_codes(query)
        
        expanded = self.expand_query(cleaned)
        
        return {
            'original': query,
            'cleaned': cleaned,
            'expanded': expanded,
            'mentioned_codes': mentioned_codes,
            'search_query': expanded 
        }