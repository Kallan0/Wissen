from typing import List, Dict, Any, Optional
import logging
import io
import math
import re
from rag.vectorstore import vector_store
from config import settings
from rag.embeddings import get_embedding_function

logger = logging.getLogger("resume_rag.ingestion")

_LOGICAL_HEADINGS = (
    "PROFESSIONAL SUMMARY", "SUMMARY", "PROFILE", "OBJECTIVE",
    "WORK EXPERIENCE", "WORK EXPERIENCE & INTERNSHIPS", "EXPERIENCE", "INTERNSHIPS",
    "PROJECTS", "TECHNICAL PROJECTS", "SKILLS", "TECHNICAL SKILLS",
    "EDUCATION", "CERTIFICATIONS", "CERTIFICATES", "AWARDS", "PUBLICATIONS",
    "VOLUNTEERING", "LANGUAGES", "INTERESTS",
)


def logical_section_chunks(text: str) -> List[str]:
    """Split resumes and structured notes at section boundaries, never by characters."""
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    if not normalized:
        return []

    heading_pattern = "|".join(re.escape(heading) for heading in sorted(_LOGICAL_HEADINGS, key=len, reverse=True))
    # PDF extraction sometimes flattens an entire page to one line. Restore
    # well-known resume section boundaries before parsing logical sections.
    normalized = re.sub(
        rf"(?<!\S)({heading_pattern})(?=\s)",
        r"\n\1\n",
        normalized,
    )

    sections: List[str] = []
    current_heading = ""
    current_lines: List[str] = []
    found_heading = False
    for raw_line in normalized.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        markdown_heading = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        heading_text = markdown_heading.group(1).strip() if markdown_heading else line
        is_heading = bool(markdown_heading) or heading_text.upper() in _LOGICAL_HEADINGS
        if is_heading:
            found_heading = True
            if current_lines:
                sections.append("\n".join(([current_heading] if current_heading else []) + current_lines))
            current_heading = heading_text
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append("\n".join(([current_heading] if current_heading else []) + current_lines))
    return sections if found_heading else []

def fixed_word_chunks(text: str, chunk_size: int = 220) -> List[str]:
    """Safe fallback used only when the local semantic embedder is unavailable."""
    words = text.split()
    chunks = [" ".join(words[index:index + chunk_size]) for index in range(0, len(words), chunk_size)]
    return chunks if chunks else [text]


def _sentence_units(text: str, hard_limit: int) -> List[str]:
    """Split at prose, line, and resume-bullet boundaries before embedding."""
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    raw_units = re.split(r"(?<=[.!?])\s+|\n+|\s*[\u2022\u25aa\u25e6]\s*", normalized)
    units: List[str] = []
    for raw in raw_units:
        sentence = re.sub(r"\s+", " ", raw).strip(" -*\t")
        if not sentence:
            continue
        words = sentence.split()
        if len(words) <= hard_limit:
            units.append(sentence)
        else:
            units.extend(" ".join(words[index:index + hard_limit]) for index in range(0, len(words), hard_limit))
    return units


def _cosine_similarity(left: Any, right: Any) -> float:
    left_values = [float(value) for value in left]
    right_values = [float(value) for value in right]
    dot = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _percentile(values: List[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * max(0.0, min(100.0, percentile)) / 100.0
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def semantic_chunk_text(
    text: str,
    *,
    embedder: Optional[Any] = None,
    min_words: Optional[int] = None,
    max_words: Optional[int] = None,
    break_percentile: Optional[float] = None,
) -> List[str]:
    """Group adjacent sentences until their embedding meaning changes.

    A chunk closes at a low adjacent-sentence cosine similarity once it has
    reached the minimum size. The maximum size is a hard safety boundary.
    """
    logical_chunks = logical_section_chunks(text)
    if logical_chunks:
        return logical_chunks

    minimum = min_words if min_words is not None else settings.SEMANTIC_CHUNK_MIN_WORDS
    maximum = max_words if max_words is not None else settings.SEMANTIC_CHUNK_MAX_WORDS
    percentile = break_percentile if break_percentile is not None else settings.SEMANTIC_CHUNK_BREAK_PERCENTILE
    if minimum < 1 or maximum < minimum:
        raise ValueError("Semantic chunk limits must satisfy 1 <= min_words <= max_words.")
    sentences = _sentence_units(text, maximum)
    if len(sentences) <= 1:
        return sentences or ([text.strip()] if text.strip() else [])

    try:
        if embedder is None:
            embedder = get_embedding_function()
        embeddings = embedder(sentences)
        similarities = [
            _cosine_similarity(embeddings[index], embeddings[index + 1])
            for index in range(len(sentences) - 1)
        ]
    except Exception as error:
        logger.warning("Semantic embedding failed; using fixed word chunks: %s", error)
        return fixed_word_chunks(text, maximum)

    breakpoint = _percentile(similarities, percentile)
    chunks: List[str] = []
    current: List[str] = []
    current_words = 0
    for index, sentence in enumerate(sentences):
        sentence_words = len(sentence.split())
        if current and current_words + sentence_words > maximum:
            chunks.append(" ".join(current))
            current, current_words = [], 0
        current.append(sentence)
        current_words += sentence_words
        boundary_similarity = similarities[index] if index < len(similarities) else None
        if boundary_similarity is not None and current_words >= minimum and boundary_similarity <= breakpoint:
            chunks.append(" ".join(current))
            current, current_words = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks


# Backward-compatible public name. Text and PDF ingestion now use semantics.
chunk_text = semantic_chunk_text


_DATE_RANGE = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}\s*[\-–—�]\s*"
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}|Present))$",
    re.IGNORECASE,
)
_SKILL_CATEGORIES = (
    "Machine Learning & Evaluation", "Mobile App Development", "Programming Languages",
    "AI/ML & GenAI", "Web & Frontend", "Backend & APIs", "Testing & Tools",
    "Databases", "Design", "Languages",
)


def _pdf_lines(text: str) -> List[str]:
    return [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]


def _strip_pdf_marker(value: str) -> str:
    return value.strip().lstrip("�•▪◦–—- ").strip()


def _date_and_location(value: str) -> tuple[str, str]:
    cleaned = _strip_pdf_marker(value)
    match = _DATE_RANGE.search(cleaned)
    if not match:
        return "", cleaned
    duration = re.sub(r"\s*[�–—]\s*", " - ", match.group(1)).strip()
    return duration, cleaned[:match.start()].strip(" -–—�")


def _bullet_lines(lines: List[str]) -> List[str]:
    bullets: List[str] = []
    current: List[str] = []
    markers = ("�", "•", "▪", "◦", "–", "—")
    for line in lines:
        standalone_marker = line in set(markers)
        boundary = standalone_marker or line.endswith(markers)
        content = _strip_pdf_marker(line.rstrip("".join(markers) + " "))
        if content:
            current.append(content)
        if boundary and current:
            bullets.append(" ".join(current))
            current = []
    if current:
        bullets.append(" ".join(current))
    return bullets


def _split_commas(value: str) -> List[str]:
    parts = re.split(r",\s*(?![^()]*\))", value)
    return [part.strip() for part in parts if part.strip()]


def extract_structured_resume(text: str) -> Dict[str, Any]:
    """Deterministically classify a text-based resume without inventing facts."""
    lines = _pdf_lines(text)
    section_indices: Dict[str, int] = {}
    aliases = {
        "profile": {"profile", "professional summary", "summary"},
        "experience": {"work experience", "work experience & internships", "experience", "internships"},
        "projects": {"projects", "technical projects"},
        "skills": {"skills", "technical skills"},
        "education": {"education"},
    }
    for index, line in enumerate(lines):
        for section, names in aliases.items():
            if line.lower() in names and section not in section_indices:
                section_indices[section] = index

    ordered = sorted((index, section) for section, index in section_indices.items())
    sections: Dict[str, List[str]] = {}
    for position, (start, section) in enumerate(ordered):
        end = ordered[position + 1][0] if position + 1 < len(ordered) else len(lines)
        sections[section] = lines[start + 1:end]

    header_end = ordered[0][0] if ordered else len(lines)
    header = lines[:header_end]
    contact_line = " ".join(header[1:])
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", contact_line)
    phone_match = re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){9,12}\d", contact_line)
    github_match = re.search(r"(?:https?://)?github\.com/[A-Za-z0-9_.-]+", contact_line, re.IGNORECASE)

    experiences: List[Dict[str, Any]] = []
    exp_lines = sections.get("experience", [])
    index = 0
    while index + 2 < len(exp_lines):
        company = _strip_pdf_marker(exp_lines[index])
        role = _strip_pdf_marker(exp_lines[index + 1])
        duration, location = _date_and_location(exp_lines[index + 2])
        if not duration:
            index += 1
            continue
        index += 3
        detail_start = index
        while index + 2 < len(exp_lines):
            next_duration, _ = _date_and_location(exp_lines[index + 2])
            if next_duration:
                break
            index += 1
        if index + 2 >= len(exp_lines):
            index = len(exp_lines)
        bullets = _bullet_lines(exp_lines[detail_start:index])
        experiences.append({
            "company": company, "role": role, "duration": duration,
            "location": location, "bullets": bullets, "technologies": [],
        })

    projects: List[Dict[str, Any]] = []
    project_lines = sections.get("projects", [])
    index = 0
    while index < len(project_lines):
        header_match = re.match(r"^(.+?)\s+(20\d{2})$", project_lines[index])
        if not header_match:
            index += 1
            continue
        name = re.sub(r"\s*[�–—]\s*", " - ", header_match.group(1)).strip()
        year = header_match.group(2)
        technologies = _split_commas(project_lines[index + 1]) if index + 1 < len(project_lines) else []
        index += 2
        detail_start = index
        while index < len(project_lines) and not re.match(r"^(.+?)\s+(20\d{2})$", project_lines[index]):
            index += 1
        highlights = _bullet_lines(project_lines[detail_start:index])
        projects.append({
            "name": name, "year": year, "description": "",
            "highlights": highlights, "technologies": technologies, "link": "",
        })

    skills: List[Dict[str, Any]] = []
    current_category = ""
    current_value: List[str] = []
    for line in sections.get("skills", []):
        matched = next((category for category in _SKILL_CATEGORIES if line.startswith(category + " ")), None)
        if matched:
            if current_category:
                skills.append({"category": current_category, "items": _split_commas(" ".join(current_value))})
            current_category = matched
            current_value = [line[len(matched):].strip()]
        elif current_category:
            current_value.append(line)
    if current_category:
        skills.append({"category": current_category, "items": _split_commas(" ".join(current_value))})

    education: List[Dict[str, Any]] = []
    education_lines = sections.get("education", [])
    index = 0
    while index + 2 < len(education_lines):
        institution = _strip_pdf_marker(education_lines[index])
        year, location = _date_and_location(education_lines[index + 1])
        degree = _strip_pdf_marker(education_lines[index + 2])
        if year:
            education.append({
                "institution": institution, "degree": degree, "year": year,
                "location": location, "details": "",
            })
            index += 3
        else:
            index += 1

    return {
        "name": header[0] if header else "",
        "contact": {
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "github": github_match.group(0) if github_match else "",
            "location": "",
        },
        "summary": " ".join(sections.get("profile", [])),
        "experience": experiences,
        "projects": projects,
        "skills": skills,
        "education": education,
    }

class IngestionService:
    @staticmethod
    def ingest_text(content: str, title: str, category: str = "raw_documents", tags: Optional[List[str]] = None) -> int:
        """Ingests unstructured markdown or text notes."""
        chunks = semantic_chunk_text(content)
        metas = [
            {
                "title": title,
                "category": category,
                "tags": ", ".join(tags or []),
                "chunk_index": idx
            }
            for idx in range(len(chunks))
        ]
        indexed_ids = vector_store.replace_source_items(
            collection_name="raw_documents",
            texts=chunks,
            metadatas=metas,
            source_field="title",
            source_value=title,
        )
        logger.info("Indexed %d semantic chunks for document: %s", len(indexed_ids), title)
        return len(indexed_ids)

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

        raw_count = IngestionService.ingest_text(
            content=full_text,
            title=f"Uploaded Resume ({filename})",
            category="raw_documents",
            tags=["resume", "uploaded_pdf", filename]
        )
        structured = extract_structured_resume(full_text)
        # The original source text remains the source of truth. Structured
        # records are deterministic classifications used by retrieval/fallback.
        summary = structured.pop("summary", "")
        IngestionService.ingest_structured_profile(structured)
        if summary:
            logger.info("Parsed verified profile summary (%d characters)", len(summary))
        return raw_count

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
                "bullet": bullet,
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
            "description": description,
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
                "highlight": hl,
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

        if name or any((email, phone, loc, linkedin, github, portfolio)):
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
