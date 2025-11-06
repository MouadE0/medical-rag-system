import fitz
import re
from pathlib import Path
from collections import Counter
import json

def main():
    pdf_path = Path("data/CoCoA.pdf")
    
    print("="*80)
    print("COCOA PDF ANALYSIS")
    print("="*80)
    
    doc = fitz.open(pdf_path)
    print(f"\nTotal pages: {len(doc)}")
    print(f"Metadata: {doc.metadata}")
    

    print("\n" + "="*80)
    print("SAMPLE PAGES")
    print("="*80)
    
    sample_pages = [0, 1, 2, 5, 10, 50, 100, 200, 500]
    for page_num in sample_pages:
        if page_num < len(doc):
            page = doc[page_num]
            text = page.get_text()
            print(f"\n{'='*80}")
            print(f"PAGE {page_num}")
            print(f"{'='*80}")
            print(text[:1000])
    
    print("\n" + "="*80)
    print("CIM-10 CODE ANALYSIS")
    print("="*80)
    
    code_pattern = r'\b[A-Z]\d{2}\.?\d?\b'
    all_codes = []
    
    for page_num in range(min(200, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        codes = re.findall(code_pattern, text)
        all_codes.extend(codes)
    
    print(f"\nFound {len(all_codes)} total codes in first 200 pages")
    print(f"Unique codes: {len(set(all_codes))}")
    print(f"\nMost common codes:")
    for code, count in Counter(all_codes).most_common(30):
        print(f"  {code}: {count}")
    
    print("\n" + "="*80)
    print("DOCUMENT STRUCTURE")
    print("="*80)
    
    keywords = ['sommaire', 'chapitre', 'règle', 'codage', 'exemple', 
                'note', 'inclus', 'exclus', 'ne pas coder']
    
    keyword_pages = {kw: [] for kw in keywords}
    
    for page_num in range(min(100, len(doc))):
        page = doc[page_num]
        text = page.get_text().lower()
        
        for keyword in keywords:
            if keyword in text:
                keyword_pages[keyword].append(page_num)
    
    print("\nKeyword occurrences (first 100 pages):")
    for keyword, pages in keyword_pages.items():
        if pages:
            print(f"  '{keyword}': {len(pages)} times on pages {pages[:10]}")
    
    print("\n" + "="*80)
    print("CODE-DENSE PAGES (Examples)")
    print("="*80)
    
    code_dense = []
    for page_num in range(100, min(300, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        codes = re.findall(code_pattern, text)
        
        if len(codes) >= 5:
            code_dense.append((page_num, len(codes), codes[:5]))
    
    print(f"\nFound {len(code_dense)} code-dense pages")
    
    for page_num, code_count, sample_codes in code_dense[:3]:
        page = doc[page_num]
        text = page.get_text()
        print(f"\n{'='*80}")
        print(f"Page {page_num} - {code_count} codes - {sample_codes}")
        print(f"{'='*80}")
        print(text[:1000])
    
    print("\n" + "="*80)
    print("CODING RULES EXAMPLES")
    print("="*80)
    
    rule_indicators = ['ne pas coder', 'coder en premier', 'inclus', 'exclus']
    
    for page_num in range(50, min(150, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        text_lower = text.lower()
        
        for indicator in rule_indicators:
            if indicator in text_lower:
                idx = text_lower.find(indicator)
                context = text[max(0, idx-100):idx+300]
                print(f"\n--- Page {page_num}: '{indicator}' ---")
                print(context)
                break
        
        if page_num > 50 and len([i for i in rule_indicators if i in text_lower]) > 0:
            if page_num > 80:
                break
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    summary = {
        'total_pages': len(doc),
        'unique_codes_sampled': len(set(all_codes)),
        'code_dense_pages': len(code_dense),
        'pages_with_rules': sum(len(pages) for pages in keyword_pages.values())
    }
    
    print(json.dumps(summary, indent=2))
    
    print("\n\nRECOMMENDATIONS:")
    print("- Focus on pages 50-1000 (likely main content)")
    print("- Chunk size: 600-800 tokens")
    print("- Keep code + description + rules together")
    print("- Extract metadata: page, codes, rule types")
    
    doc.close()

if __name__ == "__main__":
    main()