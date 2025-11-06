"""Test exclusion extraction on known text."""

import re

sample_text = """
P R A 2 A15.4 Tuberculose des ganglions intra-thoraciques, avec confirmation bactériologique et histologique Tuberculose ganglionnaire : • hilaire • médiastinale avec confirmation bactériologique et histologique • trachéo-bronchique À l'exclusion de précisée comme primo-infection (A15.7)
"""

def extract_exclusions_test(block_text: str):
    """Test exclusion extraction."""
    exclusions = []
    
    print("="*80)
    print("INPUT TEXT:")
    print("="*80)
    print(block_text)
    

    marker_pattern = r"À\s*l[''′]exclusion\s+(?:de\s*)?"
    marker_match = re.search(marker_pattern, block_text, re.IGNORECASE)
    
    if not marker_match:
        print("\n NO MARKER FOUND")
        return []
    
    print(f"\n MARKER FOUND at position {marker_match.start()}-{marker_match.end()}")
    print(f"Marker text: '{marker_match.group()}'")
    
    start_pos = marker_match.end()
    after_marker = block_text[start_pos:]
    
    print(f"\n TEXT AFTER MARKER:")
    print(f"'{after_marker[:200]}'")
    
    first_line = after_marker.split('\n')[0].strip()
    print(f"\n FIRST LINE: '{first_line}'")
    
    if first_line and len(first_line) > 3:
        exclusions.append(first_line)
    
    code_pattern = r'([^•\n]{3,}?\([A-Z]\d{2}[^\)]*\))'
    matches = re.findall(code_pattern, after_marker)
    print(f"\n CODE PATTERN MATCHES: {len(matches)}")
    for match in matches:
        print(f"  - '{match}'")
        exclusions.append(match)
    
    seen = set()
    cleaned = []
    for item in exclusions:
        item = item.strip()
        if len(item) > 5 and item.lower() not in seen:
            seen.add(item.lower())
            cleaned.append(item)
    
    print(f"\n FINAL EXCLUSIONS: {len(cleaned)}")
    for i, excl in enumerate(cleaned, 1):
        print(f"  {i}. {excl}")
    
    return cleaned

result = extract_exclusions_test(sample_text)

print("\n" + "="*80)
print(f"EXTRACTED {len(result)} EXCLUSIONS")
print("="*80)