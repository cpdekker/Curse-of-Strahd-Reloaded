#!/usr/bin/env python3
"""
Replace all category 1 references in Arc P - Ravenloft Heist.md
with inlined PDF content.
"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz

GUIDE_PATH = 'Act III - The Broken Land/Arc P - Ravenloft Heist.md'
PDF_PATH = 'Curse of Strahd.pdf'

doc = fitz.open(PDF_PATH)
pdf_pages = {}
for i in range(len(doc)):
    pdf_pages[i] = doc[i].get_text()

# ============================================================
# SECTION EXTRACTION
# ============================================================

def get_text(page_num, next_pages=2):
    """Get combined text from page_num and following pages."""
    parts = []
    for p in range(page_num, min(page_num + next_pages + 1, len(doc))):
        if p in pdf_pages:
            parts.append(pdf_pages[p])
    return '\n'.join(parts)

def find_header(text, header_patterns):
    """Find a section header in text using multiple patterns."""
    for pat in header_patterns:
        m = re.search(pat, text)
        if m:
            return m
    return None

def extract_until_next(text, start, end_patterns=None):
    """Extract text from start to next section header."""
    rest = text[start:]
    if end_patterns is None:
        end_patterns = [
            r'\n(?:K\d+[a-z]?\.|Kl\d*[a-z]?\.|KlO\.|CRYPT\s+\d+\b|FORTUNES\s+OF\s+RAVENLOFT|DEVELOPMENT\b|MAP\s*\d|TELEPORT\s+DEST)',
        ]
    for pat in end_patterns:
        ns = re.search(pat, rest[20:])
        if ns:
            return rest[:20 + ns.start()].strip()
    return rest[:5000].strip()

def clean_text(raw):
    """Clean raw PDF text for markdown use."""
    if not raw:
        return ''
    # Remove header
    lines = raw.split('\n')
    body = []
    past_header = False
    for line in lines:
        s = line.strip()
        if not past_header:
            if re.match(r'^K\w*\d*[a-z]?\.', s) or re.match(r'^CRYPT\s+\d+', s, re.I):
                continue
            if s.isupper() and len(s) > 3:
                continue
            if not s:
                continue
            past_header = True
        body.append(s)

    text = ' '.join(body)
    text = text.replace('\u00ad', '')
    text = re.sub(r'(\w)- (\w)', r'\1\2', text)
    text = text.replace('Raven loft', 'Ravenloft')
    text = text.replace('Ravenloit', 'Ravenloft')
    text = re.sub(r'CHAPTER\s+\d+\s*[|I]\s*CASTLE\s+RAVENLOFT\s*', '', text)
    text = re.sub(r'\s+\d{2,3}\s*$', '', text)
    text = re.sub(r'\s*\|+\s*', ' ', text)
    text = text.replace('2Y2', '2½')
    text = text.replace("2'h", '2½')
    text = re.sub(r'  +', ' ', text)
    return text.strip()

# ============================================================
# BUILD SECTION DATABASE
# For each section we need, extract and clean the text
# ============================================================

section_db = {}

def add_section(key, page, header_pats):
    """Add a section to the database."""
    text = get_text(page)
    m = find_header(text, header_pats)
    if m:
        raw = extract_until_next(text, m.start())
        section_db[key] = clean_text(raw)
    else:
        section_db[key] = None

# Special extraction for tricky sections
def add_section_direct(key, page, start_str, end_str=None):
    """Add a section using direct string search."""
    text = get_text(page)
    idx = text.find(start_str)
    if idx < 0:
        # Try case-insensitive
        idx_upper = text.upper().find(start_str.upper())
        if idx_upper >= 0:
            idx = idx_upper
    if idx >= 0:
        if end_str:
            end = text.find(end_str, idx + len(start_str))
            if end >= 0:
                raw = text[idx:end].strip()
            else:
                raw = text[idx:idx+5000].strip()
        else:
            raw = extract_until_next(text, idx)
        section_db[key] = clean_text(raw)
    else:
        section_db[key] = None

# ---- Extract all needed sections ----

# P2a references
add_section('Vistani Bandits', 32, [r'VISTANI BANDITS'])
add_section('I. Black Carriage', 37, [r'BLACK CARRIAGE'])
add_section('J. Gates of Ravenloft', 38, [r'GATES OF RAVENLOFT'])

# Castle Grounds
add_section('K1', 52, [r'Kl\.\s*FRONT COURTYARD', r'K1\.\s*FRONT COURTYARD'])
add_section('K2', 54, [r'K2\.\s*CENTER COURT GATE'])
add_section('K3', 54, [r'K3\.\s*SERVANTS'])
add_section_direct('K4', 54, 'K4. CARRIAGE HOUSE', 'K5.')
add_section_direct('K5', 54, 'K5. CHAPEL GARDEN', 'K6.')
add_section_direct('K6', 54, 'OV ERLOOK', 'MAIN FLOOR')
add_section('K7', 54, [r'K7\.\s*ENTRY'])

# Castle Commons
add_section('K8', 55, [r'K8\.\s*GREAT ENTRY'])
add_section('K9', 55, [r'K9\.\s*GUESTS'])
add_section('K19', 58, [r'K19\.\s*GRAND LANDING', r'Kl9\.\s*GRAND LANDING'])
add_section_direct('K10', 56, 'DINING HALL', 'Kll.')
add_section('K14', 57, [r'Kl4\.\s*HALL OF FAITH', r'K14\.\s*HALL OF FAITH'])
add_section('K15', 57, [r'Kl5\.\s*CHAPEL', r'K15\.\s*CHAPEL'])
add_section('K16', 58, [r'Kl\s*6\.\s*NORTH CHAPEL', r'Kl6\.\s*NORTH CHAPEL', r'K16\.\s*NORTH CHAPEL'])
add_section('K17', 58, [r'Kl\s*7\.\s*SOUTH CHAPEL', r'Kl7\.\s*SOUTH CHAPEL', r'K17\.\s*SOUTH CHAPEL'])
add_section('K59', 73, [r'K59\.\s*HIGH TOWER PEAK'])

# Chapel area
add_section('K29', 62, [r'K29\.\s*CREAKY LANDING'])
add_section('K28', 62, [r'K28\.\s*KING.S BALCONY'])

# Audience Hall area
add_section('K25', 61, [r'K25\.\s*AUDIENCE HALL'])
add_section_direct('K30', 62, "K30. KING'S ACCOUNTANT", 'K31')
add_section('K27', 61, [r'K27\.\s*KING.S HALL'])

# Servants' Wing
add_section('K23', 59, [r'K23\.\s*SERVANTS'])
add_section_direct('K24', 61, "K24. SERVANTS'", 'COURT OF THE COUNT')
add_section('K34', 64, [r'K34\.\s*SERVANTS'])

# Trapworks
add_section('K31', 63, [r'K31\.\s*TRAPWORKS', r'K3l\.\s*TRAPWORKS'])
add_section('K31a', 63, [r'K31[Aa]\.\s*ELEVATOR SHAFT', r'K3lA\.\s*ELEVATOR'])
add_section('K31b', 64, [r'K31[Bb]\.\s*SHAFT ACCESS', r'K3lB\.\s*SHAFT'])

# Servants' Hall
add_section_direct('K62', 76, "K62. SERVANTS'", 'K63')

# Elevator / Cellars
add_section('K61', 74, [r'K61\.\s*ELEVATOR TRAP'])
add_section('K63', 77, [r'K63\.\s*WINE CELLAR'])
add_section('K65', 78, [r'K65\.\s*KITCHEN'])
add_section_direct('K66', 78, "K66. BUTLER'S", 'K67')

# King's Apartments
add_section_direct('K33', 64, "K33. KING'S APARTMENT", 'K34')
add_section('K32', 64, [r'K32\.\s*MAID IN HELL'])
add_section('K35', 64, [r'K35\.\s*GUARDIAN'])
add_section_direct('K36', 65, 'K36. DINING HALL OF THE COUNT', 'K37')
add_section('K37', 66, [r'K37\.\s*STUDY'])
add_section('K43', 68, [r'K43\.\s*BATH CHAMBER'])
add_section('K44', 68, [r'K44\.\s*CLOSET'])
add_section_direct('K42', 68, "K42. KING'S BEDCHAMBER", 'K43')
add_section('K83a', 85, [r'K83[Aa]\.\s*SPIRAL STAIR LANDING'])

# False Treasury / Treasury
add_section('K45', 68, [r'K45\.\s*HALL OF HEROES'])
add_section('K38', 66, [r'K38\.\s*FALSE TREASURY'])
add_section('K39', 67, [r'K39\.\s*HALL OF WEBS'])
add_section('K40', 67, [r'K40\.\s*BELFRY'])
add_section('K41', 67, [r'K41\.\s*TREASURY'])
add_section('K47', 68, [r'K47\.\s*P.?ORTRAIT'])

# Guest Suite
add_section('K49', 70, [r'K49\.\s*LOUNGE'])
add_section('K50', 70, [r'K50\.\s*GUEST ROOM'])
add_section('K51', 70, [r'K51\.\s*CLOSET'])

# Coven's Quarters
add_section('K54', 71, [r'K54\.\s*FAMILIAR ROOM'])
add_section('K55', 72, [r'K55\.\s*ELEMENT ROOM'])
add_section('K56', 72, [r'K56\.\s*CAULDRON'])

# Garrison
add_section('K67', 78, [r'K67\.\s*HALL OF BONES'])
add_section('K68', 79, [r'K68\.\s*GUARDS'])
add_section_direct('K69', 79, "K69. GUARDS' QUARTERS", 'K70')
add_section('K70', 79, [r'K70\.\s*KINGSMEN HALL'])
add_section('K71', 79, [r'K71\.\s*KINGSMEN QUARTERS'])
add_section_direct('K72', 79, "K72. CHAMBERLAIN'S OFFICE", 'K73')

# Tower areas
add_section_direct('K13', 57, 'TURRET POST ACCESS HALL', 'Kl4')
add_section_direct('K11', 57, 'SOUTH ARCHERS', 'Kl2')
add_section('K12', 57, [r'Kl2\.\s*TURRET POST', r'K12\.\s*TURRET POST'])
add_section('K20', 59, [r'K20\.\s*HEART OF SORROW'])
add_section('K20a', 59, [r'K20[Aa]\.\s*TOWER HALL'])
add_section('K22', 59, [r'K22\.\s*NORTH ARCHERS'])
add_section('K46', 68, [r'K46\.\s*PARAPETS'])

# High Tower
add_section('K57', 72, [r'K57\.\s*TOWER ROOF'])
add_section('K58', 73, [r'K58\.\s*BRIDGE'])
add_section('K60', 74, [r'K60\.\s*NORTH TOWER PEAK'])
add_section('K60a', 74, [r'K60[Aa]\.\s*NORTH TOWER ROOFTOP'])

# Dungeons
add_section('K73', 79, [r'K73\.\s*DUNGEON HALL'])
add_section('K74', 80, [r'K74\.\s*NORTH DUNGEON'])
add_section('K75', 81, [r'K75\.\s*SOUTH DUNGEON'])
add_section('K76', 82, [r'K76\.\s*TORTURE CHAMBER'])
add_section('K77', 82, [r'K77\.\s*OBSERVATION BALCONY'])
add_section('K78', 82, [r'K78\.\s*BRAZIER ROOM'])
add_section('K79', 84, [r'K79\.\s*WESTERN STAIR'])
add_section('K81', 84, [r'K81\.\s*TUNNEL', r'K81\.\s*TuNNEL'])
add_section('K82', 85, [r'K82\.\s*MARBLE SLIDE'])

# Catacombs
add_section('K84', 85, [r'K84\.\s*CATACOMBS'])
add_section('K85', 93, [r'K85\.\s*SERGEI'])
add_section_direct('K86', 93, "K86. STRAHD'S TOMB", 'K87')
add_section('K87', 94, [r'K87\.\s*GUARDIANS'])
add_section_direct('K88', 94, 'TOMB OF KING BAROV', None)

# Crypts
for n in range(1, 41):
    # Some crypts have no space (CRYPT2 vs CRYPT 2)
    page_est = 86 + (n-1)//6
    if page_est > 93:
        page_est = 93
    add_section(f'Crypt {n}', page_est, [rf'CRYPT\s*{n}\b'])

# Special sections
add_section('Flight of the Vampire', 61, [r'FLIGHT OF THE VAMPIRE'])
add_section('Broom of Animated Attack', 50, [r'BROOM OF ANIMATED'])
add_section('Crawling Claws', 50, [r'CRAWLING CLAWS'])
add_section_direct('Shadows', 51, 'SHADOWS', 'STRAHD ZOMBIE')
add_section('Giant Spider Cocoon', 51, [r'GIANT SPIDER COCOON'])
add_section('Pidlwick II', 73, [r'PIDLWICK II'])
add_section('Teleport Traps', 85, [r'TELEPORT TRAPS'])
add_section_direct('Icon of Ravenloft', 222, 'Icon of Raven', 'SUNSWORD')
add_section('Lands Common Features', 33, [r'COMMON FEATURES'])

# Print stats
found = sum(1 for v in section_db.values() if v)
total = len(section_db)
print(f"Section database: {found}/{total} sections found")
for k, v in section_db.items():
    if v is None:
        print(f"  MISSING: {k}")
    elif len(v) < 20:
        print(f"  SHORT ({len(v)}): {k}: {v}")

# ============================================================
# PROCESS THE GUIDE
# ============================================================

with open(GUIDE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')

cat1_pattern = re.compile(
    r'(is|are|unfolds|begins) (largely |otherwise |similarly )?as described in <span class="citation">'
)
ref_pattern = re.compile(r'<span class="citation">([^<]+?)\s*\(p\.\s*(\d+)\)</span>')
skip_books = ["Player's Handbook", "Dungeon Master's Guide", "Monster Manual", "Van Richten's"]

def get_section_key(name):
    """Map a reference name to our section_db key."""
    # K-number refs
    m = re.match(r'(K\d+[a-z]?)\.\s*(.*)', name)
    if m:
        return m.group(1)
    # Crypt refs
    m = re.match(r'(Crypt\s+\d+)', name)
    if m:
        return m.group(1)
    # Named refs
    for key in section_db:
        if key in name:
            return key
    # Try partial match
    clean_name = name.replace("'", "").lower()
    for key in section_db:
        if key.replace("'", "").lower() in clean_name:
            return key
    return name

def lookup_section(name, page):
    """Look up a section in our database."""
    key = get_section_key(name)
    if key in section_db:
        return section_db[key]
    # Try alternate keys
    for k, v in section_db.items():
        if k.lower() in name.lower():
            return v
    return None

edit_count = 0
new_lines = list(lines)

for i, line in enumerate(lines):
    if not cat1_pattern.search(line):
        continue

    lineno = i + 1

    # Skip other-book-only references
    has_cos_ref = False
    has_other_ref = False
    for ref_m in ref_pattern.finditer(line):
        rname = ref_m.group(1)
        if any(b in rname for b in skip_books):
            has_other_ref = True
        else:
            has_cos_ref = True

    if has_other_ref and not has_cos_ref:
        print(f"SKIP L{lineno}: other-book-only refs")
        continue

    # Skip category 2 references
    if 'Pidlwick II, who is' in line and 'This area' not in line:
        print(f"SKIP L{lineno}: cat2 (character description)")
        continue
    # (Icon of Dawn's Grace IS a cat1 ref - it describes the item by reference to book)

    # Parse the line structure
    # Get the blockquote prefix if any
    prefix_m = re.match(r'^((?:>\s*)+)', line)
    prefix = prefix_m.group(1) if prefix_m else ''
    body = line[len(prefix):]

    # Find the "as described in" clause
    as_desc_m = re.search(
        r'((This area|This encounter|These north and south courtyards|The castle crossroads|'
        r'The gates of Ravenloft|This row of crypts|The contents of the treasury|'
        r'The spiral stair landing|the high tower peak, which|'
        r'The \*Icon of Dawn.s Grace\*|The oil is otherwise|'
        r'the amphora and an \*alchemy jug\*|this area)\s+'
        r'(?:is|are|begins|unfolds)\s+(?:largely |otherwise |similarly )?'
        r'as described in\s+'
        r'(?:<span class="citation">[^<]+\(p\.\s*\d+\)</span>(?:,?\s*(?:and\s*)?)?)+)',
        body
    )

    if not as_desc_m:
        print(f"WARN L{lineno}: no match for as-described pattern, skipping")
        continue

    as_desc_clause = as_desc_m.group(0)
    before_clause = body[:as_desc_m.start()].strip()
    after_clause = body[as_desc_m.end():].strip()

    # Remove leading period/comma from after_clause
    if after_clause.startswith('.'):
        after_clause = after_clause[1:].strip()
    elif after_clause.startswith(','):
        after_clause = after_clause[1:].strip()

    # Get all CoS refs in the as-described clause
    cos_refs = []
    for ref_m in ref_pattern.finditer(as_desc_clause):
        rname = ref_m.group(1)
        rpage = int(ref_m.group(2))
        if not any(b in rname for b in skip_books):
            cos_refs.append((rname, rpage))

    if not cos_refs:
        print(f"WARN L{lineno}: no CoS refs found in clause, skipping")
        continue

    # Look up section texts
    section_texts = []
    for rname, rpage in cos_refs:
        st = lookup_section(rname, rpage)
        if st:
            section_texts.append(st)

    if not section_texts:
        print(f"WARN L{lineno}: could not find any section text for {cos_refs}")
        continue

    combined_section = ' '.join(section_texts)

    # Check if there's a description block after this line (within next 5 lines)
    has_desc_block = False
    for j in range(i+1, min(i+6, len(lines))):
        if '<div class="description">' in lines[j]:
            has_desc_block = True
            break
        if lines[j].strip() and not lines[j].strip().startswith('>') and not lines[j].strip().startswith('<'):
            break

    # Check for "However/Except/But/In addition" modifications in after_clause
    has_modification = bool(re.match(
        r'(?:However|Except|But|In addition|Also|Instead)',
        after_clause, re.IGNORECASE
    ))

    # Also check for secondary "as described in" refs within after_clause (category 2)
    # These should be preserved as-is

    # Build replacement
    if has_desc_block:
        # Guide already has a description block - just keep the modifications
        if after_clause:
            if before_clause:
                new_body = before_clause + ' ' + after_clause
            else:
                # Capitalize first word if needed
                if after_clause[0].islower():
                    new_body = after_clause[0].upper() + after_clause[1:]
                else:
                    new_body = after_clause
        else:
            if before_clause:
                new_body = before_clause
            else:
                new_body = ''
    else:
        # No description block - inline the PDF content
        if after_clause:
            if has_modification:
                new_body = combined_section + ' ' + after_clause
            else:
                new_body = combined_section + ' ' + after_clause
        else:
            new_body = combined_section

    # Reconstruct line
    if new_body:
        new_line = prefix + new_body
    else:
        new_line = ''

    if new_line != line:
        new_lines[i] = new_line
        edit_count += 1
        print(f"EDIT L{lineno}")
    else:
        print(f"NOCHG L{lineno}")

# Write output
with open(GUIDE_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\n=== TOTAL EDITS: {edit_count} ===")
