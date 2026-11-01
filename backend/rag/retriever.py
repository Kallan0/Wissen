from typing import List, Dict, Any
import re
from config import settings
from rag.vectorstore import vector_store

class RAGRetriever:
    def __init__(self, vector_db=vector_store):
        self.db = vector_db

    def extract_keywords(self, jd_text: str, top_n: int = 15) -> List[str]:
        """Simple extractor for prominent technical and role keywords from the JD."""
        stopwords = {
            "and", "the", "with", "for", "that", "this", "from", "you", "will", "have",
            "are", "our", "team", "work", "role", "looking", "candidate", "must", "experience",
            "years", "plus", "required", "skills", "ability", "strong", "understanding"
        }
        words = re.findall(r"\b[A-Za-z0-9#+.]+\b", jd_text)
        filtered = [w for w in words if len(w) > 2 and w.lower() not in stopwords]
        freq = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:top_n]]

    def retrieve_context_for_jd(
        self,
        job_description: str,
        expanded_concepts: List[str] | None = None,
        top_k_per_cat: int = 6,
    ) -> Dict[str, Any]:
        """
        Retrieves relevant experiences, projects, and skills tailored to the target Job Description.
        """
        expanded_concepts = expanded_concepts or []
        query_text = job_description
        if expanded_concepts:
            query_text += "\nRelated concepts: " + ", ".join(expanded_concepts)

        # Query experiences
        exp_results = self.db.query(query_text, collection_names=["experiences"], n_results=top_k_per_cat * 2)
        # Query projects
        proj_results = self.db.query(query_text, collection_names=["projects"], n_results=top_k_per_cat)
        # Query skills
        skill_results = self.db.query(query_text, collection_names=["skills"], n_results=top_k_per_cat)
        # Query education
        edu_results = self.db.query(query_text, collection_names=["education"], n_results=3)
        # Query raw docs (bio, notes)
        doc_results = self.db.query(query_text, collection_names=["raw_documents"], n_results=top_k_per_cat * 2)

        # Relevance controls ordering, but resume generation also needs complete
        # candidate coverage. Include verified source sections that semantic
        # ranking did not return, subject to the context budget below.
        try:
            all_items = self.db.get_all_items()
            seen_ids = {item.get("id") for item in doc_results}
            seen_content = {str(item.get("content") or "").strip() for item in doc_results}
            for item in all_items.get("raw_documents", []):
                content = str(item.get("document") or "").strip()
                if not content or item.get("id") in seen_ids or content in seen_content:
                    continue
                doc_results.append({
                    "id": item.get("id", ""),
                    "collection": "raw_documents",
                    "content": content,
                    "metadata": item.get("metadata") or {},
                    "similarity": 0.0,
                    "dense_score": 0.0,
                    "bm25_score": 0.0,
                    "retrieval_method": "complete_profile_coverage",
                })
                seen_ids.add(item.get("id"))
                seen_content.add(content)
        except (AttributeError, TypeError):
            pass

        # Build clean formatted text context for the LLM
        formatted_context_lines = []
        context_chars = 0

        def append_context(line: str) -> bool:
            nonlocal context_chars
            additional = len(line) + 1
            if context_chars + additional > settings.RAG_MAX_CONTEXT_CHARS:
                return False
            formatted_context_lines.append(line)
            context_chars += additional
            return True
        
        append_context("=== VERIFIED WORK EXPERIENCE ACHIEVEMENTS ===")
        for item in exp_results:
            append_context(f"- {item['content']} (Relevance Score: {item['similarity']})")

        append_context("\n=== VERIFIED TECHNICAL PROJECTS ===")
        for item in proj_results:
            append_context(f"- {item['content']} (Relevance Score: {item['similarity']})")

        append_context("\n=== VERIFIED CANDIDATE SKILLS ===")
        for item in skill_results:
            append_context(f"- {item['content']}")

        append_context("\n=== VERIFIED EDUCATION & CREDENTIALS ===")
        for item in edu_results:
            append_context(f"- {item['content']}")

        append_context("\n=== VERIFIED SOURCE DOCUMENT EXCERPTS ===")
        included_doc_ids = set()
        for item in doc_results:
            if append_context(f"- {item['content']} (Relevance Score: {item['similarity']})"):
                included_doc_ids.add(item.get("id"))

        all_matches = exp_results + proj_results + skill_results + edu_results + doc_results

        return {
            "formatted_context": "\n".join(formatted_context_lines),
            "retrieved_items": all_matches,
            "extracted_keywords": self.extract_keywords(job_description),
            "expanded_concepts": expanded_concepts,
            "match_count": len(all_matches),
            "retrieval_strategy": "hybrid_hnsw_ann_bm25",
            "context_metrics": {
                "characters": context_chars,
                "approximate_tokens": max(1, round(context_chars / 4)),
                "source_sections_available": len(doc_results),
                "source_sections_included": len(included_doc_ids),
                "max_characters": settings.RAG_MAX_CONTEXT_CHARS,
            },
        }

rag_retriever = RAGRetriever()
