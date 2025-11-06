import fitz
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from tqdm import tqdm

from ..domain.entities import DocumentChunk


@dataclass
class CodeBlock:
    code: str
    label: str
    page_number: int
    full_text: str
    exclusions: List[str] = field(default_factory=list)
    inclusions: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    priority: Optional[str] = None
    chapter: Optional[str] = None


class CoCoAPDFProcessor:
    
    CODE_PATTERN = r'\b([A-Z]\d{2}\.?\d?)\b'
    CHAPTER_PATTERN = r'CHAPITRE\s+([IVXLCDM]+|[0-9]+)\s*[:：]'
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.doc = None
        
    def open(self):
        self.doc = fitz.open(self.pdf_path)
        print(f"Opened PDF: {len(self.doc)} pages")
        
    def close(self):
        if self.doc:
            self.doc.close()
            
    def extract_general_rules(self) -> DocumentChunk:

        print("Extracting general coding rules (pages 1-30)...")
        
        text_parts = []
        for page_num in range(1, min(31, len(self.doc))):
            page = self.doc[page_num]
            text = page.get_text()
            if text and text.strip():
                text_parts.append(f"--- Page {page_num} ---\n{text}")
        
        full_text = "\n\n".join(text_parts)
        
        
        max_length = 30000
        if len(full_text) > max_length:
            full_text = full_text[:max_length] + "\n\n[Tronqué pour raisons de taille]"
        
        return DocumentChunk(
            chunk_id="general_rules_001",
            content=full_text,
            page_number=1,
            metadata={
                'type': 'GENERAL_RULES',
                'page_range': '1-30',
                'description': 'Règles générales de codage CIM-10 pour PMSI',
                'priority': 'critical'
            }
        )
    
    def detect_chapter(self, text: str) -> Optional[str]:
        """Detect chapter from text."""
        match = re.search(self.CHAPTER_PATTERN, text, re.IGNORECASE)
        if match:
            line = text[match.start():match.start()+200]
            return line.split('\n')[0].strip()
        return None
    
    def split_text_into_code_blocks(self, text: str, page_num: int) -> List[Tuple[str, str, int]]:

        lines = text.split('\n')
        blocks = []
        current_code = None
        current_block_lines = []
        current_start_line = 0

        code_line_regex = re.compile(r'^\s*([A-Z]\d{2}\.?\d?)\s*$') 
        code_inline_regex = re.compile(r'\b([A-Z]\d{2}\.?\d?)\b') 
        pra_marker_regex = re.compile(r'\bP\s+R\s+A\b', re.IGNORECASE)

        for i, line in enumerate(lines):
            stripped = line.strip()

            m_exact = code_line_regex.match(stripped)
            if m_exact:
                if current_code and current_block_lines:
                    blocks.append((current_code, '\n'.join(current_block_lines), current_start_line))
                current_code = m_exact.group(1)
                current_block_lines = [line]
                current_start_line = i
                continue

            if pra_marker_regex.search(line):
                codes_after = code_inline_regex.findall(line)
                if codes_after:
                    if current_code and current_block_lines:
                        blocks.append((current_code, '\n'.join(current_block_lines), current_start_line))
                    current_code = codes_after[0]
                    current_block_lines = [line]
                    current_start_line = i
                    continue

            if current_code:
                current_block_lines.append(line)
            else:
                inline_codes = code_inline_regex.findall(line)
                if inline_codes:
                    current_code = inline_codes[0]
                    current_block_lines = [line]
                    current_start_line = i

        if current_code and current_block_lines:
            blocks.append((current_code, '\n'.join(current_block_lines), current_start_line))

        return blocks
    
    def extract_label_from_block(self, block_text: str, code: str) -> str:

        lines = block_text.split('\n')
        
        for line in lines[1:]:
            stripped = line.strip()
            
            if not stripped:
                continue
            if stripped in ['P', 'R', 'A']:
                continue
            if stripped.isdigit():
                continue
            if re.match(r'^(À l\'exclusion|Comprend|Note|Utiliser)', stripped, re.IGNORECASE):
                break 
            
            if len(stripped) > 3:
                return stripped
        
        return "[Voir document]"
    
    def extract_priority_from_block(self, block_text: str) -> Optional[str]:
        lines = block_text.split('\n')
        
        for i in range(len(lines) - 3):
            if (lines[i].strip() == 'P' and 
                lines[i+1].strip() == 'R' and 
                lines[i+2].strip() == 'A'):
                if i+3 < len(lines) and lines[i+3].strip().isdigit():
                    return lines[i+3].strip()
                return "unspecified"
        
        inline_match = re.search(r'P\s+R\s+A\s+(\d+)', block_text)
        if inline_match:
            return inline_match.group(1)
        
        return None
    
    def extract_exclusions_from_block(self, block_text: str) -> List[str]:
        exclusions = []

        marker_match = re.search(r"À\s*l['’′]?exclusion(?:\s+de)?", block_text, re.IGNORECASE)
        if not marker_match:
            return []

        after_marker = block_text[marker_match.end():]

        stop_patterns = [
            r'\nComprend', r'\nNote', r'\nUtiliser', r'\n\n\n',
            r'\n[A-Z]\d{2}\.?\d?\s+[A-Z]' 
        ]
        end_pos = len(after_marker)
        for pat in stop_patterns:
            m = re.search(pat, after_marker, re.IGNORECASE)
            if m and m.start() < end_pos:
                end_pos = m.start()

        exclusion_text = after_marker[:end_pos]

        bullets = re.findall(r'[•●·-]\s*([^\n]+)', exclusion_text)
        exclusions.extend(bullets)

        code_refs = re.findall(r'([^•●·\n]{3,}?\([A-Z]\d{2}[^\)]*\))', exclusion_text)
        exclusions.extend(code_refs)

        first_line = exclusion_text.split('\n')[0].strip()
        if first_line and len(first_line) > 3 and first_line not in exclusions:
            exclusions.insert(0, first_line)

        seen = set()
        cleaned = []
        for item in exclusions:
            item = item.strip()
            if len(item) > 5 and item.lower() not in seen:
                seen.add(item.lower())
                cleaned.append(item)

        return cleaned[:50]
    
    def extract_inclusions_from_block(self, block_text: str) -> List[str]:
        """Extract inclusions (Comprend) from block."""
        inclusions = []
        
        marker_pos = block_text.lower().find("comprend")
        if marker_pos == -1:
            return []
        
        after_marker = block_text[marker_pos:]
        
        terminators = ['\nÀ l\'exclusion', '\nNote', '\nUtiliser', '\n\n\n']
        end_pos = len(after_marker)
        for term in terminators:
            pos = after_marker.lower().find(term.lower())
            if pos != -1 and pos < end_pos:
                end_pos = pos
        
        inclusion_text = after_marker[:end_pos]
        
        items = []
        bullet_items = re.findall(r'[•●·-]\s*([^\n]+)', inclusion_text)
        items.extend(bullet_items)
        
        first_line = inclusion_text.split('\n')[0]
        if 'comprend' in first_line.lower():
            after_comprend = re.sub(r'.*?comprend\s*[:：]?\s*', '', first_line, flags=re.IGNORECASE)
            if after_comprend.strip():
                items.insert(0, after_comprend.strip())
        
        cleaned = [item.strip() for item in items if len(item.strip()) > 3]
        return cleaned[:20]
    
    def extract_instructions_from_block(self, block_text: str) -> List[str]:
        instructions = []
        
        patterns = [
            r'Utiliser[^.]*?\.?',
            r'Coder\s+(?:en\s+)?(?:premier|également|aussi)[^.]*?\.?',
            r'Ne\s+pas\s+coder[^.]*?\.?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, block_text, re.IGNORECASE)
            instructions.extend([m.strip() for m in matches if len(m.strip()) > 10])
        
        return instructions[:10]
    
    def extract_notes_from_block(self, block_text: str) -> List[str]:
        notes = []
        
        note_match = re.search(r'Note\s*[:：]?\s*(.+?)(?=\n\n|\Z)', block_text, re.IGNORECASE | re.DOTALL)
        if note_match:
            note_text = note_match.group(1).strip()
            if len(note_text) > 10:
                notes.append(note_text[:500])
        
        return notes
    
    def process_code_pages(self, start_page: int = 31, end_page: Optional[int] = None) -> List[DocumentChunk]:
        if end_page is None:
            end_page = len(self.doc)

        print(f"Processing code pages ({start_page}-{end_page})...")

        chunks = []
        current_chapter = None

        for page_num in tqdm(range(start_page, min(end_page, len(self.doc)))):
            page = self.doc[page_num]

            try:
                text = page.get_text("text")
            except Exception:
                text = page.get_text()

            if not text or len(text.strip()) < 50:
                continue

            chapter = self.detect_chapter(text)
            if chapter:
                current_chapter = chapter

            blocks = self.split_text_into_code_blocks(text, page_num)

            pra_count = text.count('P R A')
            found_codes_on_page = len(blocks)
            if pra_count > found_codes_on_page + 1:
                try:
                    raw_blocks = page.get_text("blocks")
                except Exception:
                    raw_blocks = []

                if raw_blocks:
                    raw_blocks_sorted = sorted(raw_blocks, key=lambda b: (b[1], b[0]))
                    fallback_blocks = []
                    code_inline_regex = re.compile(r'\b([A-Z]\d{2}\.?\d?)\b')
                    for rb in raw_blocks_sorted:
                        block_text = rb[4].strip()
                        if not block_text:
                            continue
                        codes = code_inline_regex.findall(block_text)
                        if codes:
                            for code_match in codes:
                                idx = block_text.find(code_match)
                                start = max(0, idx - 300)
                                end = min(len(block_text), idx + 600)
                                context = block_text[start:end]
                                fallback_blocks.append((code_match, context, int(rb[1])))
                    if fallback_blocks:
                        blocks = fallback_blocks

            for code, block_text, line_num in blocks:
                code = code.strip()
                if code in ['SAI', 'NCA'] or len(code) < 2:
                    continue

                label = self.extract_label_from_block(block_text, code)
                priority = self.extract_priority_from_block(block_text)
                exclusions = self.extract_exclusions_from_block(block_text)
                inclusions = self.extract_inclusions_from_block(block_text)
                instructions = self.extract_instructions_from_block(block_text)
                notes = self.extract_notes_from_block(block_text)

                content_parts = [
                    f"Code: {code}",
                    f"Libellé: {label}",
                ]

                if exclusions:
                    content_parts.append("\nÀ l'exclusion de:")
                    content_parts.extend([f"  • {excl}" for excl in exclusions])

                if inclusions:
                    content_parts.append("\nComprend:")
                    content_parts.extend([f"  • {incl}" for incl in inclusions])

                if instructions:
                    content_parts.append("\nInstructions de codage:")
                    content_parts.extend([f"  • {instr}" for instr in instructions])

                if notes:
                    content_parts.append("\nNotes:")
                    content_parts.extend([f"  • {note}" for note in notes])

                content = "\n".join(content_parts)

                mentioned_codes = list(set(re.findall(self.CODE_PATTERN, block_text)))
                mentioned_codes = [c for c in mentioned_codes if c not in ['SAI', 'NCA']]

                chunk = DocumentChunk(
                    chunk_id=f"code_{code}_{page_num}_{line_num}",
                    content=content,
                    page_number=page_num,
                    metadata={
                        'type': 'CODE_DEFINITION',
                        'primary_code': code,
                        'label': label,
                        'chapter': current_chapter,
                        'priority': priority,
                        'has_exclusions': len(exclusions) > 0,
                        'has_inclusions': len(inclusions) > 0,
                        'has_instructions': len(instructions) > 0,
                        'mentioned_codes': mentioned_codes
                    },
                    codes=[code]
                )
                chunks.append(chunk)

        return chunks
    
    def process_all(self) -> List[DocumentChunk]:
        self.open()
        
        try:
            all_chunks = []
            
            general_rules = self.extract_general_rules()
            all_chunks.append(general_rules)
            
            code_chunks = self.process_code_pages(start_page=31)
            all_chunks.extend(code_chunks)
            
            print(f"\nProcessing complete!")
            print(f"Total chunks created: {len(all_chunks)}")
            print(f"  - General rules: 1")
            print(f"  - Code definitions: {len(code_chunks)}")
            
            return all_chunks
            
        finally:
            self.close()


def process_cocoa_pdf(pdf_path: Path) -> List[DocumentChunk]:
    processor = CoCoAPDFProcessor(pdf_path)
    return processor.process_all()