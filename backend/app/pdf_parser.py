"""Parse a footwear spec-sheet PDF into structured fields (best-effort).

The exact layout of customer spec sheets varies, so this is a keyword/regex
heuristic. Results are meant to be reviewed/edited by the user (US-17), not
blindly trusted.
"""

import re

try:
    import pymupdf as fitz
except ImportError:
    import fitz


def _find_value(lines, keywords):
    """Look for 'keyword: value' or 'keyword value' on a line."""
    for line in lines:
        for kw in keywords:
            m = re.search(rf"{re.escape(kw)}\s*[:#]\s*(.+)", line, re.IGNORECASE)
            if m and m.group(1).strip():
                return m.group(1).strip()
            m = re.search(rf"{re.escape(kw)}\s+([A-Za-z0-9][A-Za-z0-9\-/\.]*)", line, re.IGNORECASE)
            if m and m.group(1).strip():
                return m.group(1).strip()
    return None


def _find_codes(text):
    """Find material/SKU-like codes (e.g. LEA-BLK-001)."""
    codes = re.findall(r"\b[A-Z]{2,4}[\-][A-Z0-9\-]{3,}\b", text)
    return list(dict.fromkeys(codes))  # dedupe, keep order


def _find_sizes(text):
    """Find size ranges like '36-42' or lists like '36 37 38 39 40'."""
    m = re.search(r"\b(3[5-9]|4[0-5])\s*[-–]\s*(3[5-9]|4[0-5])\b", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    sizes = re.findall(r"\b(3[5-9]|4[0-5])\b", text)
    return list(dict.fromkeys(sizes)) if sizes else None


def _find_dates(lines):
    dates = []
    for kw in ("request", "delivery", "due", "sample date", "confirm"):
        for line in lines:
            if re.search(kw, line, re.IGNORECASE) and re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", line):
                m = re.search(r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", line)
                if m:
                    dates.append({"keyword": kw, "value": m.group(1)})
                    break
    return dates if dates else None


def parse_spec_sheet(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(page.get_text() for page in doc)
    doc.close()

    lines = [l.strip() for l in full_text.split("\n") if l.strip()]

    return {
        "ref_no": _find_value(lines, ["STYLE NO", "STYLE", "REF NO", "REFERENCE", "ARTICLE", "ART NO", "MODEL"]),
        "designer": _find_value(lines, ["DESIGNER", "DESIGNED BY"]),
        "customer": _find_value(lines, ["CUSTOMER", "BUYER", "BRAND", "ACCOUNT"]),
        "color": _find_value(lines, ["COLORWAY", "COLOURWAY", "COLOR", "COLOUR"]),
        "materials": _find_codes(full_text),
        "sizes": _find_sizes(full_text),
        "dates": _find_dates(lines),
    }
