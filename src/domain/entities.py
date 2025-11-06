from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class CodeCategory(Enum):
    """CIM-10 code categories based on CoCoA chapters."""
    INFECTIOUS = "I"  # A00-B99
    TUMORS = "II"  # C00-D48
    BLOOD = "III"  # D50-D89
    ENDOCRINE = "IV"  # E00-E90
    MENTAL = "V"  # F00-F99
    NERVOUS = "VI"  # G00-G99
    EYE = "VII"  # H00-H59
    EAR = "VIII"  # H60-H95
    CIRCULATORY = "IX"  # I00-I99
    RESPIRATORY = "X"  # J00-J99
    DIGESTIVE = "XI"  # K00-K93
    SKIN = "XII"  # L00-L99
    MUSCULOSKELETAL = "XIII"  # M00-M99
    GENITOURINARY = "XIV"  # N00-N99
    PREGNANCY = "XV"  # O00-O99
    PERINATAL = "XVI"  # P00-P96
    CONGENITAL = "XVII"  # Q00-Q99
    SYMPTOMS = "XVIII"  # R00-R99
    INJURY = "XIX"  # S00-T98
    EXTERNAL_CAUSES = "XX"  # V01-Y98
    HEALTH_FACTORS = "XXI"  # Z00-Z99
    SPECIAL = "XXII"  # U00-U99
    UNKNOWN = "unknown"

class ChunkType(Enum):
    GENERAL_RULES = "general_rules"  # Pages 1-30
    CODE_DEFINITION = "code_definition"  # Individual code blocks
    CHAPTER_INTRO = "chapter_intro"  # Chapter explanations
@dataclass
class CIMCode:
    """Represents a CIM-10 code with CoCoA enrichments."""
    code: str
    label: str
    description: Optional[str] = None
    category: CodeCategory = CodeCategory.UNKNOWN
    chapter: Optional[str] = None
    parent_code: Optional[str] = None
    
    exclusions: List[str] = field(default_factory=list)
    inclusions: List[str] = field(default_factory=list)
    coding_instructions: List[str] = field(default_factory=list)
    priority: Optional[str] = None  # From P R A markers
    
    def __post_init__(self):
        if self.code:
            prefix = self.code[0]
            category_map = {
                'A': CodeCategory.INFECTIOUS, 'B': CodeCategory.INFECTIOUS,
                'C': CodeCategory.TUMORS, 'D': CodeCategory.TUMORS,
                'E': CodeCategory.ENDOCRINE,
                'F': CodeCategory.MENTAL,
                'G': CodeCategory.NERVOUS,
                'H': CodeCategory.EYE,
                'I': CodeCategory.CIRCULATORY,
                'J': CodeCategory.RESPIRATORY,
                'K': CodeCategory.DIGESTIVE,
                'L': CodeCategory.SKIN,
                'M': CodeCategory.MUSCULOSKELETAL,
                'N': CodeCategory.GENITOURINARY,
                'O': CodeCategory.PREGNANCY,
                'P': CodeCategory.PERINATAL,
                'Q': CodeCategory.CONGENITAL,
                'R': CodeCategory.SYMPTOMS,
                'S': CodeCategory.INJURY, 'T': CodeCategory.INJURY,
                'V': CodeCategory.EXTERNAL_CAUSES, 'W': CodeCategory.EXTERNAL_CAUSES,
                'X': CodeCategory.EXTERNAL_CAUSES, 'Y': CodeCategory.EXTERNAL_CAUSES,
                'Z': CodeCategory.HEALTH_FACTORS,
                'U': CodeCategory.SPECIAL
            }
            self.category = category_map.get(prefix, CodeCategory.UNKNOWN)




@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    page_number: int
    metadata: Dict
    embedding: Optional[List[float]] = None
    
    codes: List[str] = field(default_factory=list)
    
    chunk_type: ChunkType = ChunkType.CODE_DEFINITION
    
    def __post_init__(self):
        if self.codes is None:
            self.codes = []
        if 'type' in self.metadata:
            try:
                self.chunk_type = ChunkType(self.metadata['type'].lower())
            except ValueError:
                pass


@dataclass
class CodeSuggestion:
    code: str
    label: str
    relevance_score: float
    explanation: str
    
    cocoa_rules: Optional[str] = None
    exclusions: List[str] = field(default_factory=list)
    inclusions: List[str] = field(default_factory=list)
    coding_instructions: List[str] = field(default_factory=list)
    
    chapter: Optional[str] = None
    priority: Optional[str] = None
    additional_info: Optional[str] = None
    source_chunks: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.source_chunks is None:
            self.source_chunks = []



@dataclass
class QueryResult:
    query: str
    suggestions: List[CodeSuggestion]
    processing_time_ms: float
    retrieval_metadata: Dict
    reasoning: Optional[str] = None

    general_rules_applied: Optional[str] = None