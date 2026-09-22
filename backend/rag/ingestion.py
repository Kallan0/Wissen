from typing import List, Dict, Any, Optional
import logging
import io
from rag.vectorstore import vector_store

logger = logging.getLogger("resume_rag.ingestion")

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Splits plain text into overlapping chunks without requiring heavy dependencies."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += (chunk_size - overlap)
        if i >= len(words):
            break
    return chunks if chunks else [text]

class IngestionService:
    @staticmethod
    def ingest_text(content: str, title: str, category: str = "raw_documents", tags: Optional[List[str]] = None) -> int:
        """Ingests unstructured markdown or text notes."""
        chunks = chunk_text(content, chunk_size=250, overlap=40)
        metas = [
            {
                "title": title,
                "category": category,
                "tags": ", ".join(tags or []),
                "chunk_index": idx
            }
            for idx in range(len(chunks))
        ]
        vector_store.add_items(collection_name="raw_documents", texts=chunks, metadatas=metas)
        logger.info(f"Ingested {len(chunks)} chunks for document: {title}")
        return len(chunks)

    @staticmethod
    def ingest_pdf_file(file_bytes: bytes, filename: str) -> int:
        """Extracts text from an uploaded resume PDF and indexes it into ChromaDB."""
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        extracted_pages = []
        for p_idx, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt and txt.strip():
                extracted_pages.append(txt.strip())

        full_text = "\n\n".join(extracted_pages)
        if not full_text.strip():
            raise ValueError("No extractable text found in PDF. Make sure it is not an image scan.")

        return IngestionService.ingest_text(
            content=full_text,
            title=f"Uploaded Resume ({filename})",
            category="raw_documents",
            tags=["resume", "uploaded_pdf", filename]
        )

    @staticmethod
    def ingest_experience_item(
        company: str,
        role: str,
        duration: str,
        location: str,
        bullets: List[str],
        technologies: Optional[List[str]] = None
    ) -> List[str]:
        """Ingests work experience items into ChromaDB."""
        texts = []
        metas: List[Dict[str, Any]] = []
        tech_str = ", ".join(technologies or [])
        
        # High-level overview chunk
        overview_text = f"Work Experience: {role} at {company} ({duration}, {location}). Skills: {tech_str}. Key responsibilities and impact: " + " ".join(bullets)
        texts.append(overview_text)
        metas.append({
            "type": "experience_overview",
            "company": company,
            "role": role,
            "duration": duration,
            "location": location,
            "technologies": tech_str
        })

        # Individual bullet points for fine-grained retrieval
        for b_idx, bullet in enumerate(bullets):
            bullet_text = f"Experience Achievement at {company} as {role}: {bullet} [Tech: {tech_str}]"
            texts.append(bullet_text)
            metas.append({
                "type": "experience_bullet",
                "company": company,
                "role": role,
                "bullet_index": b_idx,
                "technologies": tech_str
            })

        return vector_store.add_items("experiences", texts=texts, metadatas=metas)

    # Backward-compatible alias
    ingest_work_experience_item = ingest_experience_item

    @staticmethod
    def ingest_project_item(
        name: str,
        description: str,
        highlights: List[str],
        technologies: List[str],
        link: Optional[str] = None
    ) -> List[str]:
        """Ingests portfolio, software, Unity/Blender or Github projects."""
        tech_str = ", ".join(technologies)
        texts = []
        metas: List[Dict[str, Any]] = []

        overview = f"Project: {name}. Description: {description}. Stack: {tech_str}. Highlights: " + " ".join(highlights)
        texts.append(overview)
        metas.append({
            "type": "project_overview",
            "name": name,
            "technologies": tech_str,
            "link": link or ""
        })

        for idx, hl in enumerate(highlights):
            hl_text = f"Project {name} detail: {hl} (Technologies: {tech_str})"
            texts.append(hl_text)
            metas.append({
                "type": "project_highlight",
                "name": name,
                "highlight_index": idx,
                "technologies": tech_str
            })

        return vector_store.add_items("projects", texts=texts, metadatas=metas)

    @staticmethod
    def ingest_skills(category: str, skills_list: List[str]) -> List[str]:
        """Ingests skill clusters."""
        text = f"Skills in category '{category}': " + ", ".join(skills_list)
        meta = {
            "category": category,
            "skills": ", ".join(skills_list)
        }
        return vector_store.add_items("skills", texts=[text], metadatas=[meta])

    @staticmethod
    def ingest_education(institution: str, degree: str, year: str, details: Optional[str] = None) -> List[str]:
        """Ingests educational credentials."""
        text = f"Education: {degree} from {institution} ({year}). {details or ''}"
        meta = {
            "institution": institution,
            "degree": degree,
            "year": year
        }
        return vector_store.add_items("education", texts=[text], metadatas=[meta])

    @classmethod
    def ingest_structured_profile(cls, profile_data: Dict[str, Any]) -> Dict[str, int]:
        """Ingests a complete structured profile JSON."""
        counts = {"experiences": 0, "projects": 0, "skills": 0, "education": 0, "raw_documents": 0}

        # Experiences
        for exp in profile_data.get("experience", []):
            ids = cls.ingest_experience_item(
                company=exp.get("company", ""),
                role=exp.get("role", ""),
                duration=exp.get("duration", ""),
                location=exp.get("location", ""),
                bullets=exp.get("bullets", []),
                technologies=exp.get("technologies", [])
            )
            counts["experiences"] += len(ids)

        # Projects
        for proj in profile_data.get("projects", []):
            ids = cls.ingest_project_item(
                name=proj.get("name", ""),
                description=proj.get("description", ""),
                highlights=proj.get("highlights", []),
                technologies=proj.get("technologies", []),
                link=proj.get("link", "")
            )
            counts["projects"] += len(ids)

        # Skills
        for skill_group in profile_data.get("skills", []):
            ids = cls.ingest_skills(
                category=skill_group.get("category", "General"),
                skills_list=skill_group.get("items", [])
            )
            counts["skills"] += len(ids)

        # Education
        for edu in profile_data.get("education", []):
            ids = cls.ingest_education(
                institution=edu.get("institution", ""),
                degree=edu.get("degree", ""),
                year=edu.get("year", ""),
                details=edu.get("details", "")
            )
            counts["education"] += len(ids)

        # Candidate identity & contact metadata
        contact = profile_data.get("contact") if isinstance(profile_data.get("contact"), dict) else {}
        name = profile_data.get("name") or contact.get("name") or ""
        email = contact.get("email") or profile_data.get("email") or ""
        phone = contact.get("phone") or profile_data.get("phone") or ""
        loc = contact.get("location") or profile_data.get("location") or ""
        linkedin = contact.get("linkedin") or profile_data.get("linkedin") or ""
        github = contact.get("github") or profile_data.get("github") or ""
        portfolio = contact.get("portfolio") or profile_data.get("portfolio") or ""

        if name or email:
            contact_text = f"Candidate Profile: {name} | Email: {email} | Phone: {phone} | Location: {loc} | LinkedIn: {linkedin} | GitHub: {github} | Portfolio: {portfolio}"
            contact_meta = {
                "category": "candidate_identity",
                "candidate_name": name,
                "name": name,
                "email": email,
                "phone": phone,
                "location": loc,
                "linkedin": linkedin,
                "github": github,
                "portfolio": portfolio
            }
            vector_store.add_items("raw_documents", texts=[contact_text], metadatas=[contact_meta])
            counts["raw_documents"] += 1

        # Bio or summary
        if profile_data.get("summary"):
            ids = cls.ingest_text(
                content=profile_data["summary"],
                title="Professional Summary",
                category="summary"
            )
            counts["raw_documents"] += ids

        return counts
