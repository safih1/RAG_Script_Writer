from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .models import Entity
from .search import search


def search_view(request):
    q = request.GET.get("q", "").strip()
    district = request.GET.get("district") or None
    results = []
    if q:
        for doc, snip in search(q, district):
            html = escape(snip).replace("\x02", "<mark>").replace("\x03", "</mark>")
            results.append({"doc": doc, "snippet": mark_safe(html)})
    return render(request, "kb/search.html", {
        "q": q,
        "district": district,
        "results": results,
        "districts": Entity.objects.filter(kind="district").order_by("name"),
    })
