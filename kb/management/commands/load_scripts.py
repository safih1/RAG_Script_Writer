import glob, os
from datetime import date
from django.core.management.base import BaseCommand
from kb.models import Source, Document
from kb.tagging import build_patterns, tag_document


class Command(BaseCommand):
    help = "Load past scripts from a folder"

    def add_arguments(self, parser):
        parser.add_argument("--folder", default="scripts")
        parser.add_argument("--lang", default="ur")

    def handle(self, *args, **opts):
        src, _ = Source.objects.get_or_create(
            name="Own scripts", defaults=dict(tier=1, actor_type="own_script", language=opts["lang"]))
        patterns = build_patterns()
        n = 0
        for path in glob.glob(os.path.join(opts["folder"], "*.txt")):
            name = os.path.basename(path)[:-4]
            d, _, title = name.partition("_")
            try:
                pub = date.fromisoformat(d)
            except ValueError:
                pub = None
            text = open(path, encoding="utf-8").read().strip()
            doc = Document(source=src, url=f"script:{name}", title=title, published=pub,
                           language=opts["lang"], doc_type="script", full_text=text)
            if not Document.objects.filter(url=doc.url).exists():
                doc.save()
                tag_document(doc, patterns)
                n += 1
        self.stdout.write(f"Loaded {n} scripts")