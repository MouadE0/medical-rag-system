"""Debug what's actually in blocks that should have exclusions."""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz
from src.config import settings


pdf_path = settings.cocoa_pdf_path
doc = fitz.open(pdf_path)

# We know page 50 has A41 with exclusions

print("Searching for A15.4 (known to have exclusions)...")

found_page = None
for page_num in range(30, 100):
    page = doc[page_num]
    text = page.get_text()
    
    if 'A15.4' in text and 'exclusion' in text.lower():
        found_page = page_num
        print(f"\n Found A15.4 with exclusion on page {page_num}")
        
        # Extract the relevant section
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'A15.4' in line:
                
                print("\n" + "="*80)
                print(f"CONTEXT AROUND A15.4 (lines {i-5} to {i+10})")
                print("="*80)
                for j in range(max(0, i-5), min(len(lines), i+10)):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j:3d}: {lines[j]}")
                
                
                print("\n" + "="*80)
                print("SIMULATING BLOCK EXTRACTION")
                print("="*80)
                
                
                block_start = i
                block_lines = [lines[i]]
                
                
                for j in range(i+1, min(len(lines), i+50)):
                    next_line = lines[j].strip()
                    
                    if re.match(r'^[A-Z]\d{2}\.?\d?$', next_line):
                        break
                    block_lines.append(lines[j])
                
                block_text = '\n'.join(block_lines)
                
                print(f"Block text ({len(block_text)} chars):")
                print("-"*80)
                print(block_text[:1000])
                print("-"*80)
                
                
                print("\n TESTING EXCLUSION EXTRACTION ON THIS BLOCK:")
                
                marker_pattern = r"À\s*l[''′]exclusion\s+(?:de\s*)?"
                marker_match = re.search(marker_pattern, block_text, re.IGNORECASE)
                
                if marker_match:
                    print(f"Found exclusion marker at position {marker_match.start()}")
                    after_marker = block_text[marker_match.end():]
                    print(f"Text after marker: '{after_marker[:200]}'")
                else:
                    print("No exclusion marker found in block")
                
                break
        break

if not found_page:
    print("Could not find A15.4 with exclusion")


print("\n\n" + "="*80)
print("CHECKING PAGE 50 (A41 - known exclusions)")
print("="*80)

page = doc[50]
text = page.get_text()


lines = text.split('\n')
for i, line in enumerate(lines):
    if line.strip() == 'A41':
        print(f"\nFound A41 at line {i}")
        
        
        block_lines = [lines[i]]
        for j in range(i+1, min(len(lines), i+100)):
            next_line = lines[j].strip()
            if re.match(r'^A41\.\d+$', next_line):
                break
            block_lines.append(lines[j])
        
        block_text = '\n'.join(block_lines)
        
        print(f"\nA41 block ({len(block_text)} chars):")
        print("-"*80)
        print(block_text[:1500])
        print("-"*80)
        
        # Test extraction
        marker_pattern = r"À\s*l[''′]exclusion\s+(?:de\s*)?"
        marker_match = re.search(marker_pattern, block_text, re.IGNORECASE)
        
        if marker_match:
            print(f"\n Found exclusion marker")
            after_marker = block_text[marker_match.end():]
            print(f"Text after marker (first 500 chars):")
            print(after_marker[:500])
        else:
            print("\n No exclusion marker found")
        
        break

doc.close()