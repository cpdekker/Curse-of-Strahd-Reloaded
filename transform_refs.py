#!/usr/bin/env python3
"""
Transform all category 1 references in Arc P - Ravenloft Heist.md
by inlining the referenced PDF content.
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz

GUIDE_PATH = 'Act III - The Broken Land/Arc P - Ravenloft Heist.md'
PDF_PATH = 'Curse of Strahd.pdf'

doc = fitz.open(PDF_PATH)
pdf_pages = {}
for i in range(len(doc)):
    pdf_pages[i] = doc[i].get_text()
# book page N = doc[N] for this PDF

def get_section(name, page):
    """Extract a named section from the PDF starting at the given book page."""
    # Search page and nearby pages
    combined = ''
    for p in range(max(0, page-1), min(len(doc), page+3)):
        combined += '\n---PAGEBREAK---\n' + pdf_pages[p]

    clean = name.strip()

    # K-number sections
    k_match = re.match(r'(K\d+[a-z]?)\.\s*(.*)', clean)
    if k_match:
        k_num = k_match.group(1)
        variants = set()
        variants.add(k_num)
        # OCR: 1->l, 0->O in various combos
        for old, new in [('1', 'l'), ('10', 'lO'), ('11', 'll'), ('12', 'l2'),
                         ('13', 'l3'), ('14', 'l4'), ('15', 'l5'), ('16', 'l6'),
                         ('17', 'l7'), ('18', 'l8'), ('19', 'l9')]:
            v = k_num.replace(old, new)
            if v != k_num:
                variants.add(v)

        for kv in variants:
            pat = re.escape(kv) + r'\.\s+'
            for mm in re.finditer(pat, combined):
                # Verify it's a section header
                after = combined[mm.end():mm.end()+80]
                if re.match(r'[A-Z\'\"]', after.strip()):
                    return _extract_section(mm.start(), combined)

    # Crypt sections
    crypt_match = re.match(r'Crypt\s+(\d+)', clean)
    if crypt_match:
        num = crypt_match.group(1)
        pat = r'CRYPT\s+' + num + r'\b'
        m = re.search(pat, combined)
        if m:
            return _extract_section(m.start(), combined, crypt=True)

    # Named sections (Vistani Bandits, etc.)
    words = clean.replace("'", "").replace(".", " ").split()
    if words:
        pat = r'[\s\S]{0,5}'.join(re.escape(w) for w in words)
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            return _extract_section(m.start(), combined)

    return None

def _extract_section(start, text, crypt=False):
    """Extract from start to next section header."""
    rest = text[start:]
    if crypt:
        ns = re.search(r'\nCRYPT\s+\d+', rest[20:])
    else:
        ns = re.search(
            r'\n(?:K\d+[a-z]?\.|Kl\d*[a-z]?\.|KlO\.|CRYPT\s+\d+\b|FORTUNES\s+OF\s+RAVENLOFT|DEVELOPMENT\b|MAP\s*\d|TELEPORT\s+DEST)',
            rest[20:]
        )
    if ns:
        return rest[:20 + ns.start()].strip()
    return rest[:5000].strip()

def clean_section_to_description(raw):
    """Convert raw PDF section text into clean description text for the guide.
    Returns (read_aloud_text, mechanics_text) tuple."""
    if not raw:
        return '', ''

    lines = raw.split('\n')

    # Remove the header line(s) - section number and title
    body_lines = []
    past_header = False
    for line in lines:
        s = line.strip()
        if not past_header:
            if re.match(r'^K\w+[\.\s]', s) or re.match(r'^CRYPT\s+\d+', s):
                continue
            if s.isupper() and len(s) > 3 and not any(c.isdigit() for c in s):
                continue
            past_header = True
        if s:
            body_lines.append(s)

    text = ' '.join(body_lines)

    # Fix common issues
    text = text.replace('\u00ad', '')
    text = re.sub(r'(\w)- (\w)', r'\1\2', text)
    text = text.replace('Raven loft', 'Ravenloft')
    text = text.replace('Ravenloit', 'Ravenloft')
    text = re.sub(r'CHAPTER\s+\d+\s*[|I]\s*CASTLE\s+RAVENLOFT\s*', '', text)
    text = re.sub(r'\s+\d{2,3}\s*$', '', text)
    text = re.sub(r'  +', ' ', text)
    # Remove page break markers
    text = text.replace('---PAGEBREAK---', '')

    return text.strip(), ''

def format_read_aloud(text):
    """Format text as a description block."""
    return f'\n<div class="description">\n<p>{text}</p>\n</div>\n'

# Read the guide
with open(GUIDE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')

cat1_pattern = re.compile(
    r'(is|are|unfolds|begins) (largely |otherwise |similarly )?as described in <span class="citation">'
)
ref_pattern = re.compile(r'<span class="citation">([^<]+?)\s*\(p\.\s*(\d+)\)</span>')

# Books to skip
skip_books = ["Player's Handbook", "Dungeon Master's Guide", "Monster Manual", "Van Richten's"]

# Category 2 subjects to skip (not area descriptions)
cat2_subjects = [
    'who is',  # character descriptions
    'the cocoon', 'which is', # item descriptions within sentences
    'the broom is', 'The broom is',
    'the claws', 'behave as', 'otherwise behave',
    'the manacles', 'the chains',
    'a single **shadow** dwells here, as described in',
    'crawling claws...as described in',
]

edit_count = 0
new_lines = list(lines)

for i, line in enumerate(lines):
    if not cat1_pattern.search(line):
        continue

    lineno = i + 1

    # Check for other-book references
    has_other_book = False
    for book in skip_books:
        if book in line:
            has_other_book = True
            break

    # Lines 1750, 1762, 1769 - Player's Handbook references only - SKIP
    if has_other_book:
        # Check if the line has CoS refs too (like line 1726)
        cos_refs = []
        other_refs = []
        for ref_match in ref_pattern.finditer(line):
            name = ref_match.group(1)
            is_other = any(b in name for b in skip_books)
            if is_other:
                other_refs.append(ref_match)
            else:
                cos_refs.append(ref_match)

        if not cos_refs:
            # All refs are to other books - skip entirely
            print(f"SKIP line {lineno}: all refs to other books")
            continue
        # If mixed, we still process the CoS refs (line 1726)

    # Check if this is a category 2 reference (character/item within sentence)
    # Category 2: "who is as described in", "which is as described in" (for items/characters)
    match = cat1_pattern.search(line)
    before_match = line[:match.start()]

    # Pidlwick II line - category 2
    if 'Pidlwick II, who is' in line:
        print(f"SKIP line {lineno}: category 2 (character description)")
        continue

    # Lines in blockquotes that describe items (Icon of Dawn's Grace)
    if "Icon of Dawn's Grace" in line:
        print(f"SKIP line {lineno}: category 2 (item description)")
        continue

    # Get primary reference
    refs = ref_pattern.findall(line)
    if not refs:
        continue

    primary_name, primary_page = refs[0]
    primary_page_int = int(primary_page)

    # Extract the primary section from PDF
    primary_section = get_section(primary_name, primary_page_int)

    if not primary_section:
        print(f"WARNING: Could not extract '{primary_name}' (p.{primary_page}), skipping")
        continue

    primary_clean, _ = clean_section_to_description(primary_section)

    # Now build the replacement line
    # Determine the structure:
    # 1. "This area is [largely] as described in REF." -> Replace whole sentence with inlined text
    # 2. "This area is [largely] as described in REF. However, ..." -> Replace "as described" sentence, keep "However"
    # 3. "This area is [largely] as described in REF, REF, and REF." -> Multiple section refs
    # 4. Within blockquote (> prefix)

    # Detect blockquote prefix
    prefix = ''
    stripped = line
    if line.startswith('>'):
        # Count leading > characters
        m_prefix = re.match(r'^((?:>\s*)+)', line)
        if m_prefix:
            prefix = m_prefix.group(1)
            stripped = line[len(prefix):]

    # Parse the sentence structure
    # Find the "as described in" clause and everything after it
    # The clause is: "SUBJECT (is|are|begins|unfolds) (largely|etc)? as described in <span...>...</span>(, <span...>...</span>)*(. | and <span...>...</span>.)"
    # Followed optionally by: ". However, ...", ". In addition, ...", etc.

    # Strategy: find the "as described in" reference(s) and what follows
    as_desc_match = re.search(
        r'((?:This area|This encounter|These north and south courtyards|The castle crossroads|The gates of Ravenloft|'
        r'This row of crypts|The contents of the treasury|The spiral stair landing|this area|'
        r'This area|the high tower peak, which)\s+)'
        r'(is|are|begins|unfolds)\s+(largely |otherwise |similarly )?'
        r'as described in\s+'
        r'((?:<span class="citation">[^<]+\(p\.\s*\d+\)</span>(?:,?\s*(?:and\s+)?)?)+)',
        stripped
    )

    if not as_desc_match:
        print(f"WARNING: Could not parse reference pattern on line {lineno}, skipping")
        continue

    # What comes after all the references?
    full_ref_span_end = as_desc_match.end()
    after_refs = stripped[full_ref_span_end:].strip()

    # Remove trailing period from the reference clause if present
    if after_refs.startswith('.'):
        after_refs = after_refs[1:].strip()
    elif after_refs.startswith(','):
        after_refs = after_refs[1:].strip()

    # Get the subject part (before "is/are as described")
    subject = as_desc_match.group(1).strip()
    verb = as_desc_match.group(2)

    # Before the "as described" sentence, is there anything?
    before_as_desc = stripped[:as_desc_match.start()].strip()

    # Build replacement
    # Get all additional section texts for multi-ref lines
    all_section_texts = []
    for name, page in refs:
        # Skip non-CoS refs
        if any(b in name for b in skip_books):
            continue
        sect = get_section(name, int(page))
        if sect:
            cleaned, _ = clean_section_to_description(sect)
            all_section_texts.append((name, cleaned))
        else:
            all_section_texts.append((name, None))

    # Determine if the guide already has read-aloud text after this line
    has_existing_description = False
    for j in range(i+1, min(i+5, len(lines))):
        if '<div class="description">' in lines[j]:
            has_existing_description = True
            break
        if lines[j].strip() and not lines[j].startswith('>'):
            break

    # Build the replacement based on the pattern
    # For lines that have "However, ..." modifications, preserve those
    modifications = ''
    if after_refs:
        # Check for however/except/in addition/also/but
        if re.match(r'(?:However|Except|But|In addition|Also|Instead)', after_refs, re.IGNORECASE):
            modifications = ' ' + after_refs
        elif after_refs:
            # It's a continuation - preserve it
            modifications = ' ' + after_refs

    # For secondary "as described in" refs WITHIN the same line (cat2), preserve those
    # These are things like "locked as described in Common Features", "behaves as described in Crawling Claws"
    # They appear after the main area reference, in the modifications part

    # Now create the actual inlined text
    if has_existing_description:
        # The guide already has a description block - just remove the "as described" sentence
        # and add any mechanical details from the PDF
        if modifications:
            new_stripped = modifications.strip()
            # Capitalize first letter if it starts with However etc.
            if new_stripped and new_stripped[0].islower():
                new_stripped = new_stripped[0].upper() + new_stripped[1:]
        else:
            new_stripped = ''
    else:
        # No existing description - inline the PDF text
        if len(all_section_texts) == 1:
            sect_text = all_section_texts[0][1] if all_section_texts[0][1] else ''
        else:
            # Multiple sections - combine
            parts = []
            for name, text in all_section_texts:
                if text:
                    parts.append(text)
            sect_text = ' '.join(parts)

        if sect_text:
            new_stripped = sect_text
            if modifications:
                new_stripped += modifications
        else:
            new_stripped = modifications.strip() if modifications else ''

    # Reconstruct the line with prefix
    if new_stripped:
        new_line = prefix + new_stripped
    else:
        new_line = ''  # Remove the line entirely

    # Apply the edit
    if new_line != line:
        old_line_preview = line[:100] + ('...' if len(line) > 100 else '')
        new_line_preview = new_line[:100] + ('...' if len(new_line) > 100 else '')
        print(f"EDIT line {lineno}:")
        print(f"  OLD: {old_line_preview}")
        print(f"  NEW: {new_line_preview}")
        new_lines[i] = new_line
        edit_count += 1
    else:
        print(f"NO CHANGE line {lineno}")

# Write output
output = '\n'.join(new_lines)
with open(GUIDE_PATH, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n=== TOTAL EDITS: {edit_count} ===")
