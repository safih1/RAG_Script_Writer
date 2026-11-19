import re
from django.db import connection
from .models import Document


def _match(q):
    words = re.findall(r"\w+", q, flags=re.UNICODE)[:15]
    return " OR ".join(f'"{w}"' for w in words)


def search(q, district=None, top=10):
    m = _match(q)
    if not m:
        return []
    with connection.cursor() as cur:
        cur.execute("""SELECT rowid, snippet(kb_docs_fts, 1, %s, %s, ' ... ', 24)
                       FROM kb_docs_fts WHERE kb_docs_fts MATCH %s
                       ORDER BY bm25(kb_docs_fts) LIMIT 100""", ["\x02", "\x03", m])
        rows = cur.fetchall()
    snippets = {r[0]: r[1] for r in rows}
    qs = Document.objects.filter(id__in=list(snippets)).select_related("source").prefetch_related("entities")
    if district:
        qs = qs.filter(entities__kind="district", entities__name=district)
    docs = {d.id: d for d in qs}
    return [(docs[i], snippets[i]) for i, _ in rows if i in docs][:top]


def hybrid_search(q, district=None, top=10):
    import numpy as np
    from .embedding import encode
    from .models import Embedding

    kw = search(q, district, top=50)
    kw_rank = {d.id: i for i, (d, _) in enumerate(kw)}
    snips = {d.id: s for d, s in kw}

    emb = Embedding.objects.all()
    if district:
        emb = emb.filter(document__entities__kind="district",
                         document__entities__name=district).distinct()
    rows = list(emb.values_list("document_id", "vector"))
    if not rows:
        return kw[:top]

    ids = [r[0] for r in rows]
    matrix = np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    sims = matrix @ encode([q])[0]
    order = np.argsort(-sims)[:50]
    vec_rank = {ids[i]: rank for rank, i in enumerate(order)}

    scores = {}
    for d in set(vec_rank) | set(kw_rank):
        scores[d] = 1 / (60 + vec_rank.get(d, 999)) + 1 / (60 + kw_rank.get(d, 999))
    best = sorted(scores, key=scores.get, reverse=True)[:top]

    docs = {d.id: d for d in Document.objects.filter(id__in=best)
            .select_related("source").prefetch_related("entities")}
    return [(docs[i], snips.get(i, docs[i].full_text[:250])) for i in best if i in docs]
