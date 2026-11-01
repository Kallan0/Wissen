from rag.vectorstore import ChromaManager


class FakeCollection:
    def __init__(self):
        self.ids = ["old-1", "old-2"]
        self.documents = ["Built REST APIs", "built REST APIs!"]
        self.deleted = []
        self.upserted = None

    def get(self, include=None, where=None):
        return {"ids": self.ids, "documents": self.documents}

    def delete(self, ids):
        self.deleted.extend(ids)

    def upsert(self, **kwargs):
        self.upserted = kwargs


def test_add_items_removes_existing_duplicates_and_skips_reingestion():
    collection = FakeCollection()
    manager = object.__new__(ChromaManager)
    manager.get_collection = lambda _name: collection

    inserted = manager.add_items(
        "experiences",
        ["Built REST APIs", "Added automated tests", "Added automated tests."],
        [{}, {}, {}],
    )

    assert collection.deleted == ["old-2"]
    assert len(inserted) == 1
    assert collection.upserted["documents"] == ["Added automated tests"]
    assert inserted[0].startswith("experiences-")


def test_source_replacement_keeps_matching_chunks_and_removes_obsolete_chunks():
    collection = FakeCollection()
    collection.ids = ["obsolete", "retained"]
    collection.documents = ["Old fixed-window chunk", "Same semantic chunk"]
    manager = object.__new__(ChromaManager)
    manager.get_collection = lambda _name: collection

    final_ids = manager.replace_source_items(
        "raw_documents",
        ["Same semantic chunk", "New semantic chunk"],
        [{"title": "Resume.pdf"}, {"title": "Resume.pdf"}],
        source_field="title",
        source_value="Resume.pdf",
    )

    assert collection.deleted == ["obsolete"]
    assert "retained" in final_ids
    assert collection.upserted["documents"] == ["New semantic chunk"]
