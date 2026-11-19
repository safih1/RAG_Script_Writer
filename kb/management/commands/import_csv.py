import csv, re
from datetime import date
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from kb.models import Source, Document
from kb.tagging import build_patterns, tag_document


def parse_date(s):
    m = re.fullmatch(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", (s or "").strip())
    if not m:
        return None, "unknown"
    y, mo, d = int(m.group(1)), m.group(2), m.group(3)
    if d:
        return date(y, int(mo), int(d)), "day"
    if mo:
        return date(y, int(mo), 1), "month"
    return date(y, 1, 1), "year"


class Command(BaseCommand):
    help = "Import historical documents from CSV: title,text,date,source,url,doc_type,language"

    def add_arguments(self, parser):
        parser.add_argument("csvfile")

    def handle(self, *args, **opts):
        patterns = build_patterns()
        added = skipped = 0
        with open(opts["csvfile"], encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                text = (row.get("text") or "").strip()
                if len(text) < 30:
                    skipped += 1
                    continue
                src, _ = Source.objects.get_or_create(
                    name=(row.get("source") or "Historical import").strip(),
                    defaults=dict(tier=3, actor_type="dataset", language=row.get("language") or "en"))
                ed, prec = parse_date(row.get("date"))
                doc = Document(source=src, url=(row.get("url") or "").strip(),
                               title=(row.get("title") or "").strip(), published=ed,
                               event_date=ed, date_precision=prec,
                               language=row.get("language") or "en",
                               doc_type=(row.get("doc_type") or "background").strip(), full_text=text)
                try:
                    doc.save()
                except IntegrityError:
                    skipped += 1
                    continue
                tag_document(doc, patterns)
                added += 1
        self.stdout.write(f"Imported {added}, skipped {skipped}")