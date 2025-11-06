"""Debug script to understand exact page structure."""

import fitz
from pathlib import Path
import re

pdf_path = Path("data/CoCoA.pdf")
doc = fitz.open(pdf_path)


page = doc[86]
text = page.get_text()

print("="*80)
print("PAGE 50 RAW TEXT")
print("="*80)
print(text)

print("\n\n")
print("="*80)
print("LINES ANALYSIS")
print("="*80)

lines = text.split('\n')
for i, line in enumerate(lines):
    if line.strip():
        
        has_code = bool(re.search(r'[A-Z]\d{2}\.?\d?', line))
        has_exclusion = 'exclusion' in line.lower()
        has_comprend = 'comprend' in line.lower()
        
        marker = ""
        if has_code:
            marker += "[CODE] "
        if has_exclusion:
            marker += "[EXCLUSION] "
        if has_comprend:
            marker += "[COMPREND] "
        
        if marker:
            print(f"{i:3d} {marker:20s} | {line[:100]}")

print("\n\n")
print("="*80)
print("TESTING EXCLUSION PATTERN")
print("="*80)


exclusion_pattern = r'À l\'exclusion de\s*[:：]?\s*(.+?)(?=\n\s*\n|\nComprend|\nNote|\nUtiliser|\n[A-Z]\d{2}\.?\d?\s+[A-Z]|$)'
matches = re.findall(exclusion_pattern, text, re.DOTALL | re.IGNORECASE)

print(f"Found {len(matches)} exclusion blocks")
for i, match in enumerate(matches):
    print(f"\n--- Exclusion Block {i+1} ---")
    print(match[:300])

doc.close()