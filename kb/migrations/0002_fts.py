from django.db import migrations

CREATE = [
    """CREATE VIRTUAL TABLE kb_docs_fts USING fts5(
         title, full_text, content='kb_document', content_rowid='id',
         tokenize='unicode61 remove_diacritics 2')""",
    """CREATE TRIGGER kb_doc_ai AFTER INSERT ON kb_document BEGIN
         INSERT INTO kb_docs_fts(rowid, title, full_text) VALUES (new.id, new.title, new.full_text); END""",
    """CREATE TRIGGER kb_doc_ad AFTER DELETE ON kb_document BEGIN
         INSERT INTO kb_docs_fts(kb_docs_fts, rowid, title, full_text)
         VALUES ('delete', old.id, old.title, old.full_text); END""",
    """CREATE TRIGGER kb_doc_au AFTER UPDATE ON kb_document BEGIN
         INSERT INTO kb_docs_fts(kb_docs_fts, rowid, title, full_text)
         VALUES ('delete', old.id, old.title, old.full_text);
         INSERT INTO kb_docs_fts(rowid, title, full_text) VALUES (new.id, new.title, new.full_text); END""",
]
DROP = ["DROP TRIGGER kb_doc_au", "DROP TRIGGER kb_doc_ad", "DROP TRIGGER kb_doc_ai", "DROP TABLE kb_docs_fts"]


class Migration(migrations.Migration):
    dependencies = [("kb", "0001_initial")]
    operations = [migrations.RunSQL(CREATE, DROP)]