import re
from .models import Entity

LEAD_CHARS = 800   # how much of the opening text counts for news, scripts and reports


def build_patterns():
    patterns = []
    for e in Entity.objects.all():
        names = [e.name] + [a.strip() for a in e.aliases.splitlines() if a.strip()]
        rx = re.compile("|".join(rf"(?<!\w){re.escape(n)}(?!\w)" for n in names), re.IGNORECASE)
        patterns.append((e, rx))
    return patterns


def tag_text(doc):
    if doc.doc_type in ("news", "script", "report"):
        return f"{doc.title}\n{doc.full_text[:LEAD_CHARS]}"
    return f"{doc.title}\n{doc.full_text}"


def tag_document(doc, patterns=None):
    patterns = patterns or build_patterns()
    text = tag_text(doc)
    found = [e for e, rx in patterns if rx.search(text)]
    if found:
        doc.entities.add(*found)    # only adds, so manual editor tags are never removed
    return found