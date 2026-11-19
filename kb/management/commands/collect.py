import calendar, json, time
from datetime import datetime, timezone
import urllib.robotparser as rp
from urllib.parse import urlparse

import feedparser, trafilatura
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from kb.models import Source, Document
from kb.tagging import build_patterns, tag_document

UA = "DeptKB-Bot/0.1 (contact: kb@yourdept.example)"   # put a real contact address here
KEYWORDS = ["balochistan", "quetta", "gwadar", "بلوچستان", "کوئٹہ", "گوادر"]
_robots = {}


def allowed(url):
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        r = rp.RobotFileParser(base + "/robots.txt")
        try:
            r.read()
        except Exception:
            r = None
        _robots[base] = r
    r = _robots[base]
    return bool(r) and r.can_fetch(UA, url)


class Command(BaseCommand):
    help = "Collect new articles from active RSS sources"

    def add_arguments(self, parser):
        parser.add_argument("--delay", type=float, default=2.0)
        parser.add_argument("--source", default=None, help="Only this source name")

    def handle(self, *args, **opts):
        patterns = build_patterns()
        sources = Source.objects.filter(active=True).exclude(feed_url="")
        if opts["source"]:
            sources = sources.filter(name=opts["source"])
        for s in sources:
            feed = feedparser.parse(s.feed_url, agent=UA)
            self.stdout.write(f"{s.name}: {len(feed.entries)} items in feed")
            added = 0
            for e in feed.entries:
                url = e.get("link")
                if not url or Document.objects.filter(url=url).exists():
                    continue
                title = e.get("title", "")
                if s.balochistan_only and not any(
                        k in (title + e.get("summary", "")).lower() for k in KEYWORDS):
                    continue
                if not allowed(url):
                    continue
                html = trafilatura.fetch_url(url)
                time.sleep(opts["delay"])
                if not html:
                    continue
                raw = trafilatura.extract(html, output_format="json",
                                          with_metadata=True, include_comments=False)
                if not raw:
                    continue
                d = json.loads(raw)
                text = d.get("text") or ""
                if len(text) < 200:
                    continue
                pub = None
                if e.get("published_parsed"):
                    pub = datetime.fromtimestamp(
                        calendar.timegm(e.published_parsed), tz=timezone.utc).date()
                doc = Document(source=s, url=url, title=d.get("title") or title,
                               author=d.get("author") or "", published=pub,
                               language=s.language, doc_type="news", full_text=text)
                try:
                    doc.save()
                except IntegrityError:
                    continue            # same article text already stored
                tag_document(doc, patterns)
                added += 1
            self.stdout.write(f"  added {added}")