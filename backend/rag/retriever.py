from typing import List, Dict, Any
import re
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

    def retrieve_context_for_jd(self, job_description: str, top_k_per_cat: int = 4) -> Dict[str, Any]:
        """
        Retrieves relevant experiences, projects, and skills tailored to the target Job Description.
        """
        # Query experiences
        exp_results = self.db.query(job_description, collection_names=["experiences"], n_results=top_k_per_cat * 2)
        # Query projects
        proj_results = self.db.query(job_description, collection_names=["projects"], n_results=top_k_per_cat)
        # Query skills
        skill_results = self.db.query(job_description, collection_names=["skills"], n_results=top_k_per_cat)
        # Query education
        edu_results = self.db.query(job_description, collection_names=["education"], n_results=2)
        # Query raw docs (bio, notes)
        doc_results = self.db.query(job_description, collection_names=["raw_documents"], n_results=2)

        # Build clean formatted text context for the LLM
        formatted_context_lines = []
        
        formatted_context_lines.append("=== VERIFIED WORK EXPERIENCE ACHIEVEMENTS ===")
        for item in exp_results:
            formatted_context_lines.append(f"- {item['content']} (Relevance Score: {item['similarity']})")

        formatted_context_lines.append("\n=== VERIFIED TECHNICAL PROJECTS ===")
        for item in proj_results:
            formatted_context_lines.append(f"- {item['content']} (Relevance Score: {item['similarity']})")

        formatted_context_lines.append("\n=== VERIFIED CANDIDATE SKILLS ===")
        for item in skill_results:
            formatted_context_lines.append(f"- {item['content']}")

        formatted_context_lines.append("\n=== VERIFIED EDUCATION & CREDENTIALS ===")
        for item in edu_results:
            formatted_context_lines.append(f"- {item['content']}")

        all_matches = exp_results + proj_results + skill_results + edu_results + doc_results

        return {
            "formatted_context": "\n".join(formatted_context_lines),
            "retrieved_items": all_matches,
            "extracted_keywords": self.extract_keywords(job_description),
            "match_count": len(all_matches)
        }

rag_retriever = RAGRetriever()
