from django.core.management.base import BaseCommand
from kb.models import Source, Entity


class Command(BaseCommand):
    help = "Create starter sources and entities (edit them in the admin afterwards)"

    def handle(self, *args, **opts):
        sources = [
            ("Dawn Balochistan", "https://www.dawn.com/feeds/pakistan/balochistan", "en", 2, "media", False),
            ("Express Tribune Balochistan", "https://tribune.com.pk/feed/balochistan", "en", 2, "media", False),
            ("Express News", "https://www.express.pk/feed", "ur", 2, "media", True),
            ("Aaj News", "https://www.aaj.tv/feeds/latest-news", "ur", 2, "media", True),
        ]
        for name, url, lang, tier, typ, bal in sources:
            Source.objects.get_or_create(name=name, defaults=dict(
                feed_url=url, language=lang, tier=tier, actor_type=typ, balochistan_only=bal))

        # Starter list only. Replace with the full official district list (e.g. from HDX).
        entities = [
            ("district", "Quetta", "کوئٹہ"), ("district", "Gwadar", "گوادر"),
            ("district", "Kech", "Turbat\nتربت"), ("district", "Panjgur", "پنجگور"),
            ("actor", "BLA", "Baloch Liberation Army"), ("actor", "FC", "Frontier Corps"),
            ("actor", "TTP", "Tehrik-e-Taliban Pakistan"),
        ]
        for kind, name, aliases in entities:
            Entity.objects.get_or_create(kind=kind, name=name, defaults={"aliases": aliases})
        self.stdout.write("Seed done.")