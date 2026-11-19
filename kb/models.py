import hashlib
from django.db import models


class Source(models.Model):
    ACTOR_TYPES = [("media", "Media"), ("official", "Official"), ("party", "Party/advocacy"),
                   ("dataset", "Dataset"), ("own_script", "Own script")]
    name = models.CharField(max_length=120, unique=True)
    feed_url = models.URLField(blank=True)
    language = models.CharField(max_length=5, default="en")
    tier = models.IntegerField(default=2, help_text="Set by editorial policy. 1 = most trusted.")
    actor_type = models.CharField(max_length=20, choices=ACTOR_TYPES, default="media")
    balochistan_only = models.BooleanField(
        default=False, help_text="Tick for national feeds: keep only items mentioning Balochistan keywords.")
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (tier {self.tier})"


class Entity(models.Model):
    KINDS = [("district", "District"), ("actor", "Actor"), ("place", "Place"), ("event_type", "Event type")]
    kind = models.CharField(max_length=20, choices=KINDS)
    name = models.CharField(max_length=120)
    aliases = models.TextField(blank=True, help_text="One alias per line (Urdu and English spellings).")

    class Meta:
        unique_together = ("kind", "name")
        verbose_name_plural = "entities"

    def __str__(self):
        return f"{self.name} [{self.kind}]"


class Document(models.Model):
    DOC_TYPES = [("news", "News"), ("script", "Script"), ("report", "Report"), ("background", "Background")]
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    url = models.CharField(max_length=1000, unique=True, blank=True)
    title = models.CharField(max_length=500, blank=True)
    author = models.CharField(max_length=200, blank=True)
    published = models.DateField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=5, default="en")
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES, default="news")
    full_text = models.TextField()
    content_hash = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    entities = models.ManyToManyField(Entity, blank=True)
    reviewed = models.BooleanField(default=False, help_text="Tags checked by an editor.")
    event_date = models.DateField(null=True, blank=True, help_text="When the event happened, if known")
    date_precision = models.CharField(max_length=10, default="day", help_text="day, month, year or unknown")

    class Meta:
        ordering = ["-published", "-id"]

    def save(self, *args, **kwargs):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.full_text.encode("utf-8")).hexdigest()
        if not self.url:
            self.url = f"manual:{self.content_hash[:16]}"   # for documents pasted in the admin
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.url

class Embedding(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name="embedding")
    model_name = models.CharField(max_length=100)
    vector = models.BinaryField()