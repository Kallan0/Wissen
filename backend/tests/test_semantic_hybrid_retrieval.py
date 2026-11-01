from rag.ingestion import extract_structured_resume, logical_section_chunks, semantic_chunk_text
from rag.retriever import RAGRetriever
from rag.vectorstore import ChromaManager


class TopicEmbedder:
    def __call__(self, sentences):
        return [
            [1.0, 0.0],
            [0.99, 0.01],
            [0.0, 1.0],
            [0.01, 0.99],
        ][:len(sentences)]


def test_semantic_chunker_breaks_when_sentence_meaning_changes():
    text = (
        "Python APIs process application requests. "
        "FastAPI services validate backend payloads. "
        "Figma prototypes define the visual hierarchy. "
        "Interface layouts document reusable design components."
    )

    chunks = semantic_chunk_text(
        text,
        embedder=TopicEmbedder(),
        min_words=1,
        max_words=100,
        break_percentile=25,
    )

    assert len(chunks) == 2
    assert "FastAPI" in chunks[0]
    assert "Figma" not in chunks[0]
    assert chunks[1].startswith("Figma")


def test_resume_text_is_chunked_by_logical_sections_before_semantics():
    text = (
        "JOJI A G\n"
        "PROFESSIONAL SUMMARY\nBackend and frontend developer.\n"
        "WORK EXPERIENCE\nUI/UX Intern at Verified Company.\n"
        "PROJECTS\nResume Builder using Next.js and Tailwind CSS.\n"
        "SKILLS\nReact, Next.js, Tailwind CSS"
    )

    chunks = logical_section_chunks(text)

    assert chunks == [
        "JOJI A G",
        "PROFESSIONAL SUMMARY\nBackend and frontend developer.",
        "WORK EXPERIENCE\nUI/UX Intern at Verified Company.",
        "PROJECTS\nResume Builder using Next.js and Tailwind CSS.",
        "SKILLS\nReact, Next.js, Tailwind CSS",
    ]
    assert semantic_chunk_text(text, embedder=lambda _: (_ for _ in ()).throw(AssertionError())) == chunks


def test_flattened_resume_does_not_treat_lowercase_prose_as_a_heading():
    chunks = logical_section_chunks(
        "PROFESSIONAL SUMMARY Software engineer with project experience and an objective approach. "
        "PROJECTS Verified Resume Builder using Next.js."
    )

    assert len(chunks) == 2
    assert "project experience" in chunks[0]
    assert chunks[1].startswith("PROJECTS")


def test_text_resume_is_classified_into_verified_structured_records():
    parsed = extract_structured_resume(
        "JOJI A G\nDeveloper\njoji@example.com +91 9999999999 github.com/example\n"
        "Profile\nVerified candidate summary.\n"
        "Work Experience & Internships\nVerified Company\n• Frontend Intern\n• Remote Apr 2025 – May 2025\nBuilt a React interface.•\n"
        "Projects\nVerified Project 2026\nReact, FastAPI\nBuilt a verified project.•\n"
        "Skills\nWeb & Frontend React, Next.js\n"
        "Education\nVerified University\n• City 2024 – 2027\nBachelor of Computer Applications"
    )

    assert parsed["experience"][0]["company"] == "Verified Company"
    assert parsed["experience"][0]["bullets"] == ["Built a React interface."]
    assert parsed["projects"][0]["name"] == "Verified Project"
    assert parsed["skills"][0]["items"] == ["React", "Next.js"]
    assert parsed["education"][0]["institution"] == "Verified University"


class HybridCollection:
    def count(self):
        return 3

    def get(self, include=None):
        return {
            "ids": ["dense", "lexical", "irrelevant"],
            "documents": [
                "Distributed systems architecture and event processing",
                "Created an exact Figma prototype for accessible navigation",
                "General office administration",
            ],
            "metadatas": [{}, {}, {}],
        }

    def query(self, **kwargs):
        return {
            "ids": [["dense"]],
            "documents": [["Distributed systems architecture and event processing"]],
            "metadatas": [[{}]],
            "distances": [[0.05]],
        }


def test_hybrid_search_fuses_ann_dense_and_bm25_candidates():
    manager = object.__new__(ChromaManager)
    manager.get_collection = lambda _name: HybridCollection()

    results = manager.query(
        "exact Figma prototype",
        collection_names=["projects"],
        n_results=2,
    )

    assert {item["id"] for item in results} == {"dense", "lexical"}
    assert all(item["retrieval_method"] == "hybrid_hnsw_ann_bm25" for item in results)
    lexical = next(item for item in results if item["id"] == "lexical")
    assert lexical["dense_score"] == 0.0
    assert lexical["bm25_score"] == 1.0


class BrokenDenseCollection(HybridCollection):
    def query(self, **kwargs):
        raise PermissionError("embedding cache is not readable")


def test_hybrid_search_keeps_bm25_results_when_dense_embedding_fails():
    manager = object.__new__(ChromaManager)
    manager.get_collection = lambda _name: BrokenDenseCollection()

    results = manager.query(
        "exact Figma prototype",
        collection_names=["projects"],
        n_results=2,
    )

    assert results[0]["id"] == "lexical"
    assert results[0]["retrieval_method"] == "bm25_degraded_fallback"
    assert len(results) == 2


class QueryCaptureDB:
    def __init__(self):
        self.queries = []

    def query(self, query_text, collection_names=None, n_results=5):
        self.queries.append(query_text)
        return []


def test_retriever_appends_expanded_concepts_to_every_collection_query():
    db = QueryCaptureDB()
    result = RAGRetriever(db).retrieve_context_for_jd(
        "Frontend Development internship",
        expanded_concepts=["Next.js", "Tailwind CSS", "responsive design"],
    )

    assert len(db.queries) == 5
    assert all("Next.js, Tailwind CSS, responsive design" in query for query in db.queries)
    assert result["expanded_concepts"] == ["Next.js", "Tailwind CSS", "responsive design"]


class CoverageDB(QueryCaptureDB):
    def query(self, query_text, collection_names=None, n_results=5):
        super().query(query_text, collection_names, n_results)
        if collection_names == ["raw_documents"]:
            return [{
                "id": "ranked",
                "collection": "raw_documents",
                "content": "PROJECTS\nVerified frontend project",
                "metadata": {},
                "similarity": 0.8,
            }]
        return []

    def get_all_items(self):
        return {"raw_documents": [
            {"id": "ranked", "document": "PROJECTS\nVerified frontend project", "metadata": {}},
            {"id": "education", "document": "EDUCATION\nVerified university record", "metadata": {}},
        ]}


def test_retriever_includes_unranked_verified_source_sections_for_complete_coverage():
    result = RAGRetriever(CoverageDB()).retrieve_context_for_jd("Frontend internship")

    assert "Verified frontend project" in result["formatted_context"]
    assert "Verified university record" in result["formatted_context"]
    assert result["context_metrics"]["source_sections_available"] == 2
    assert result["context_metrics"]["source_sections_included"] == 2
