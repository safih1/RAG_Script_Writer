import html as htmllib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date

import trafilatura
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from kb.models import Source, Document
from kb.tagging import build_patterns, tag_document

UA = "DeptKB-Bot/0.1 (contact: kb@yourdept.example)"   # put a real contact address here
KEYWORDS = ["balochistan", "quetta", "gwadar", "بلوچستان", "کوئٹہ", "گوادر"]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")), r.headers


def to_text(content_html):
    text = trafilatura.extract(content_html) or ""
    if len(text) < 100:
        text = htmllib.unescape(re.sub(r"<[^>]+>", " ", content_html))
        text = re.sub(r"\s+", " ", text).strip()
    return text


class Command(BaseCommand):
    help = "Import posts from a WordPress site through its public REST API"

    def add_arguments(self, parser):
        parser.add_argument("--site", default="https://khabarkada.pk")
        parser.add_argument("--source", default="Khabarkada")
        parser.add_argument("--delay", type=float, default=2.0)
        parser.add_argument("--max-pages", type=int, default=0, help="0 means all pages")
        parser.add_argument("--balochistan-only", action="store_true")
        parser.add_argument("--analysis-slugs", default="articles,analysis,opinion,editorial")

    def handle(self, *args, **opts):
        site = opts["site"].rstrip("/")
        src, _ = Source.objects.get_or_create(
            name=opts["source"],
            defaults=dict(tier=2, actor_type="media", language="en"))
        patterns = build_patterns()
        analysis = {s.strip() for s in opts["analysis_slugs"].split(",") if s.strip()}

        cats = {}
        try:
            data, _ = get_json(f"{site}/wp-json/wp/v2/categories?per_page=100&_fields=id,slug")
            cats = {c["id"]: c["slug"] for c in data}
        except Exception as e:
            self.stdout.write(f"Could not read categories (continuing): {e}")

        page, added, skipped = 1, 0, 0
        while True:
            if opts["max_pages"] and page > opts["max_pages"]:
                break
            url = (f"{site}/wp-json/wp/v2/posts?per_page=50&page={page}"
                   "&_fields=id,date,link,title,content,categories")
            try:
                posts, headers = get_json(url)
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    self.stdout.write("Reached the last page.")
                else:
                    self.stdout.write(f"HTTP error {e.code} on page {page}. Stopping.")
                break
            except Exception as e:
                self.stdout.write(f"Error on page {page}: {e}. Stopping.")
                break
            if not posts:
                break
            if page == 1:
                self.stdout.write(f"Total posts reported by site: {headers.get('X-WP-Total')}")
            for p in posts:
                link = p.get("link")
                if not link or Document.objects.filter(url=link).exists():
                    skipped += 1
                    continue
                title = htmllib.unescape(p["title"]["rendered"]).strip()
                text = to_text(p["content"]["rendered"])
                if len(text) < 150:
                    skipped += 1
                    continue
                if opts["balochistan_only"] and not any(
                        k in (title + " " + text).lower() for k in KEYWORDS):
                    skipped += 1
                    continue
                try:
                    pub = date.fromisoformat(p["date"][:10])
                except Exception:
                    pub = None
                slugs = {cats.get(c) for c in p.get("categories", [])}
                doc_type = "report" if slugs & analysis else "news"
                doc = Document(source=src, url=link, title=title, published=pub,
                               language=src.language, doc_type=doc_type, full_text=text)
                try:
                    doc.save()
                except IntegrityError:
                    skipped += 1
                    continue
                tag_document(doc, patterns)
                added += 1
            self.stdout.write(f"page {page} done, added so far: {added}")
            page += 1
            time.sleep(opts["delay"])
        self.stdout.write(f"Done. Added {added}, skipped {skipped}")