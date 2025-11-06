import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.pdf_processor import process_cocoa_pdf
from src.config import settings

chunks = process_cocoa_pdf(settings.cocoa_pdf_path)


code_chunks = [c for c in chunks if c.metadata.get('type') == 'CODE_DEFINITION']

print(f"Total code chunks: {len(code_chunks)}")

# Count unique codes
unique_codes = set([c.metadata.get('primary_code') for c in code_chunks])
print(f"Unique codes: {len(unique_codes)}")

# Analyze code patterns
code_lengths = Counter([len(c.metadata.get('primary_code', '')) for c in code_chunks])
print(f"\nCode length distribution:")
for length, count in sorted(code_lengths.items()):
    print(f"  {length} chars: {count} codes")

# Check for duplicates
code_counts = Counter([c.metadata.get('primary_code') for c in code_chunks])
duplicates = {code: count for code, count in code_counts.items() if count > 1}
print(f"\nDuplicate codes: {len(duplicates)}")
if duplicates:
    print("Sample duplicates:")
    for code, count in list(duplicates.items())[:10]:
        print(f"  {code}: appears {count} times")

# Analyze exclusions
with_exclusions = [c for c in code_chunks if c.metadata.get('has_exclusions')]
print(f"\nCodes with exclusions: {len(with_exclusions)}")

# Sample codes with exclusions
print("\nSample codes WITH exclusions:")
for chunk in with_exclusions[:5]:
    print(f"\n{chunk.metadata.get('primary_code')} - {chunk.metadata.get('label')}")
    print(chunk.content[:300])

# Check for invalid codes
short_labels = [c for c in code_chunks if len(c.metadata.get('label', '')) < 10]
print(f"\nCodes with short labels (<10 chars): {len(short_labels)}")
print("Samples:")
for chunk in short_labels[:10]:
    print(f"  {chunk.metadata.get('primary_code')}: '{chunk.metadata.get('label')}'")
    