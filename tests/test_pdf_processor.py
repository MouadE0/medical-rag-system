"""Test PDF processing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.pdf_processor import process_cocoa_pdf
from src.config import settings


def test_pdf_processing():

    
    print("Testing PDF processing...")
    print(f"PDF path: {settings.cocoa_pdf_path}")
    
    chunks = process_cocoa_pdf(settings.cocoa_pdf_path)
    
    print(f"\n{'='*80}")
    print("PROCESSING RESULTS")
    print(f"{'='*80}")
    print(f"Total chunks: {len(chunks)}")
    
    general_rules = [c for c in chunks if c.metadata.get('type') == 'GENERAL_RULES']
    code_chunks = [c for c in chunks if c.metadata.get('type') == 'CODE_DEFINITION']
    
    print(f"\nGeneral rules chunks: {len(general_rules)}")
    print(f"Code definition chunks: {len(code_chunks)}")
    
    print(f"\n{'='*80}")
    print("SAMPLE CHUNKS")
    print(f"{'='*80}")
    
    if general_rules:
        print("\n--- GENERAL RULES (first 500 chars) ---")
        print(general_rules[0].content[:500])
    
    if code_chunks:
        print("\n--- CODE DEFINITION SAMPLES ---")
        for i, chunk in enumerate(code_chunks[:3]):
            print(f"\nChunk {i+1}:")
            print(f"  ID: {chunk.chunk_id}")
            print(f"  Page: {chunk.page_number}")
            print(f"  Primary Code: {chunk.metadata.get('primary_code')}")
            print(f"  Label: {chunk.metadata.get('label')}")
            print(f"  Chapter: {chunk.metadata.get('chapter')}")
            print(f"  Has exclusions: {chunk.metadata.get('has_exclusions')}")
            print(f"  Content preview:")
            print(f"    {chunk.content[:300]}...")
    
    print(f"\n{'='*80}")
    print("STATISTICS")
    print(f"{'='*80}")
    
    codes_with_exclusions = sum(1 for c in code_chunks if c.metadata.get('has_exclusions'))
    codes_with_inclusions = sum(1 for c in code_chunks if c.metadata.get('has_inclusions'))
    codes_with_instructions = sum(1 for c in code_chunks if c.metadata.get('has_instructions'))
    
    print(f"Codes with exclusions: {codes_with_exclusions}")
    print(f"Codes with inclusions: {codes_with_inclusions}")
    print(f"Codes with instructions: {codes_with_instructions}")
    
    unique_codes = set()
    for chunk in code_chunks:
        if chunk.codes:
            unique_codes.update(chunk.codes)
    
    print(f"Unique codes found: {len(unique_codes)}")
    
    return chunks


if __name__ == "__main__":
    chunks = test_pdf_processing()