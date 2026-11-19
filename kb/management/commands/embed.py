from django.core.management.base import BaseCommand
from kb.models import Document, Embedding
from kb.embedding import encode, MODEL_NAME


class Command(BaseCommand):
    help = "Create meaning-vectors for documents that do not have one yet"

    def handle(self, *args, **opts):
        todo = list(Document.objects.filter(embedding__isnull=True))
        self.stdout.write(f"{len(todo)} documents to embed")
        for i in range(0, len(todo), 16):
            batch = todo[i:i + 16]
            texts = [f"{d.title}\n{d.full_text[:3000]}" for d in batch]
            vecs = encode(texts)
            for d, v in zip(batch, vecs):
                Embedding.objects.create(document=d, model_name=MODEL_NAME, vector=v.tobytes())
            self.stdout.write(f"  {min(i + 16, len(todo))} / {len(todo)}")
        self.stdout.write("Done.")