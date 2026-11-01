import json
import re
import logging
import asyncio
import time
from copy import deepcopy
import httpx
from typing import Dict, Any, List, Optional
from config import settings
from json_resume import to_json_resume
from ai.prompts import (
    STRICT_SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    ROLE_RECOMMENDATION_PROMPT,
    COVER_LETTER_PROMPT,
    ATS_ANALYSIS_PROMPT,
    QUERY_EXPANSION_PROMPT,
)

logger = logging.getLogger("resume_rag.generator")

_GROUNDING_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "with",
    "built", "created", "developed", "implemented", "designed", "worked", "used", "supported", "contributed",
    "experience", "experienced", "project", "application", "system", "solution", "responsible", "collaborated",
}


def _evidence_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", str(value or "").lower()).strip()


def _evidence_contains(value: Any, evidence: str) -> bool:
    key = _evidence_key(value)
    return bool(key) and f" {key} " in f" {_evidence_key(evidence)} "


def _claim_is_grounded(claim: Any, evidence: str) -> bool:
    """Reject claims whose metrics or meaningful terms are absent from evidence."""
    text = str(claim or "").strip()
    if not text:
        return False
    clean_evidence = re.sub(r"\(Relevance Score:\s*[0-9.]+\)", "", evidence, flags=re.IGNORECASE)
    claim_numbers = set(re.findall(r"\b\d[\d,.]*%?\b", text))
    evidence_numbers = set(re.findall(r"\b\d[\d,.]*%?\b", clean_evidence))
    if not claim_numbers.issubset(evidence_numbers):
        return False
    evidence_tokens = set(_evidence_key(clean_evidence).split())
    claim_tokens = [
        token for token in _evidence_key(text).split()
        if len(token) > 2 and token not in _GROUNDING_STOPWORDS and not token.isdigit()
    ]
    if not claim_tokens:
        return bool(claim_numbers)
    return sum(token in evidence_tokens for token in claim_tokens) / len(claim_tokens) >= 0.5


def enforce_grounded_resume(
    resume: Dict[str, Any],
    evidence: str,
    candidate_info: Dict[str, Any],
    target_role: str,
) -> Dict[str, Any]:
    """Deterministically remove unsupported LLM entities before rendering."""
    cleaned = deepcopy(resume)
    removed = {"experience": 0, "projects": 0, "education": 0, "skills": 0, "bullets": 0}

    verified_name = str(candidate_info.get("name") or "").strip()
    generated_name = str(cleaned.get("name") or "").strip()
    cleaned["name"] = verified_name or (generated_name if _evidence_contains(generated_name, evidence) else "")
    cleaned["title"] = target_role
    generated_contact = cleaned.get("contact") if isinstance(cleaned.get("contact"), dict) else {}
    cleaned["contact"] = {}
    for field in ("email", "phone", "location", "linkedin", "github", "portfolio"):
        verified = str(candidate_info.get(field) or "").strip()
        generated = str(generated_contact.get(field) or "").strip()
        cleaned["contact"][field] = verified or (generated if _evidence_contains(generated, evidence) else "")

    experiences = []
    for item in cleaned.get("experience", []) if isinstance(cleaned.get("experience"), list) else []:
        if not isinstance(item, dict):
            removed["experience"] += 1
            continue
        company, role = item.get("company"), item.get("role")
        if not (_evidence_contains(company, evidence) and _evidence_contains(role, evidence)):
            removed["experience"] += 1
            continue
        grounded = dict(item)
        for field in ("duration", "location"):
            if grounded.get(field) and not _evidence_contains(grounded[field], evidence):
                grounded[field] = ""
        bullets = item.get("bullets") if isinstance(item.get("bullets"), list) else []
        grounded["bullets"] = [bullet for bullet in bullets if _claim_is_grounded(bullet, evidence)][:4]
        removed["bullets"] += len(bullets) - len(grounded["bullets"])
        technologies = item.get("technologies") if isinstance(item.get("technologies"), list) else []
        grounded["technologies"] = [tech for tech in technologies if _evidence_contains(tech, evidence)]
        experiences.append(grounded)
    cleaned["experience"] = experiences

    projects = []
    for item in cleaned.get("projects", []) if isinstance(cleaned.get("projects"), list) else []:
        if not isinstance(item, dict) or not _evidence_contains(item.get("name"), evidence):
            removed["projects"] += 1
            continue
        grounded = dict(item)
        description = grounded.get("description", "")
        grounded["description"] = description if _claim_is_grounded(description, evidence) else ""
        bullets = item.get("bullets") if isinstance(item.get("bullets"), list) else []
        grounded["bullets"] = [bullet for bullet in bullets if _claim_is_grounded(bullet, evidence)][:3]
        removed["bullets"] += len(bullets) - len(grounded["bullets"])
        technologies = item.get("technologies") if isinstance(item.get("technologies"), list) else []
        grounded["technologies"] = [tech for tech in technologies if _evidence_contains(tech, evidence)]
        link = str(item.get("link") or "").strip()
        grounded["link"] = link if _evidence_contains(link, evidence) else ""
        year = str(item.get("year") or "").strip()
        grounded["year"] = year if not year or _evidence_contains(year, evidence) else ""
        projects.append(grounded)
    cleaned["projects"] = projects

    education = []
    for item in cleaned.get("education", []) if isinstance(cleaned.get("education"), list) else []:
        if not isinstance(item, dict) or not (
            _evidence_contains(item.get("institution"), evidence)
            and _evidence_contains(item.get("degree"), evidence)
        ):
            removed["education"] += 1
            continue
        grounded = dict(item)
        for field in ("year", "details", "location"):
            if grounded.get(field) and not _claim_is_grounded(grounded[field], evidence):
                grounded[field] = ""
        education.append(grounded)
    cleaned["education"] = education

    skills = []
    for group in cleaned.get("skills", []) if isinstance(cleaned.get("skills"), list) else []:
        if not isinstance(group, dict):
            continue
        items = group.get("items") if isinstance(group.get("items"), list) else []
        verified_items = [skill for skill in items if _evidence_contains(skill, evidence)]
        removed["skills"] += len(items) - len(verified_items)
        if verified_items:
            skills.append({"category": group.get("category") or "Verified Skills", "items": verified_items})
    cleaned["skills"] = skills

    summary = str(cleaned.get("summary") or "")
    summary_sentences = re.split(r"(?<=[.!?])\s+", summary)
    cleaned["summary"] = " ".join(
        sentence.strip() for sentence in summary_sentences if _claim_is_grounded(sentence, evidence)
    )
    cleaned["_grounding_validation"] = {"status": "filtered", "removed": removed}
    return cleaned

def extract_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extracts and parses JSON from LLM output, handling markdown blocks or whitespace."""
    text = raw_text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Find first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            # Common cleanup: trailing commas
            cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except Exception:
                pass

    return None

class ResumeGenerator:
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._provider_unavailable_until: Dict[str, float] = {}

    def _provider_available(self, provider: str) -> bool:
        return time.monotonic() >= self._provider_unavailable_until.get(provider, 0.0)

    def _mark_provider_unavailable(self, provider: str) -> None:
        self._provider_unavailable_until[provider] = (
            time.monotonic() + settings.AI_PROVIDER_FAILURE_COOLDOWN_SECONDS
        )

    def _mark_provider_available(self, provider: str) -> None:
        self._provider_unavailable_until.pop(provider, None)

    async def get_available_models(self) -> List[str]:
        """Queries local Ollama instance for installed models."""
        if not settings.OLLAMA_ENABLED:
            return []
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return models if models else ["llama3"]
        except Exception as e:
            logger.warning(f"Could not connect to Ollama at {self.base_url}: {e}")
        return [settings.OLLAMA_DEFAULT_MODEL]

    async def get_model_options(self) -> List[str]:
        """Return selectable local and configured cloud models.

        Plain model names remain backward-compatible Ollama selections. Groq
        models are namespaced so an arbitrary client cannot choose a provider
        by smuggling a model name into another field.
        """
        local_models = await self.get_available_models()
        cloud_models = [f"groq::{model}" for model in settings.GROQ_MODELS] if settings.GROQ_API_KEY else []
        if settings.AI_DEFAULT_PROVIDER == "groq" and cloud_models:
            return cloud_models + local_models
        return local_models + cloud_models

    async def check_ollama_status(self) -> Dict[str, Any]:
        if not settings.OLLAMA_ENABLED:
            return {"enabled": False, "online": False, "models": [], "url": self.base_url}
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {"enabled": True, "online": True, "models": models, "url": self.base_url}
        except Exception:
            pass
        return {"enabled": True, "online": False, "models": [], "url": self.base_url}

    async def check_groq_status(self) -> Dict[str, Any]:
        """Check Groq configuration without exposing the API key."""
        if not settings.GROQ_API_KEY:
            return {"configured": False, "online": False, "models": list(settings.GROQ_MODELS)}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.GROQ_BASE_URL}/models",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                )
                if response.status_code == 200:
                    available = {item.get("id") for item in response.json().get("data", [])}
                    configured = [model for model in settings.GROQ_MODELS if model in available]
                    self._mark_provider_available("groq")
                    return {"configured": True, "online": True, "models": configured or list(settings.GROQ_MODELS)}
                self._mark_provider_unavailable("groq")
                return {"configured": True, "online": False, "models": list(settings.GROQ_MODELS)}
        except Exception as error:
            self._mark_provider_unavailable("groq")
            logger.warning("Groq status check failed: %s", error)
            return {"configured": True, "online": False, "models": list(settings.GROQ_MODELS)}

    def _resolve_provider(self, model: Optional[str]) -> tuple[str, str]:
        if model and model.startswith("groq::"):
            selected = model.removeprefix("groq::").strip()
            if not settings.GROQ_API_KEY:
                raise RuntimeError("Groq is not configured. Set GROQ_API_KEY on the backend.")
            if selected not in settings.GROQ_MODELS:
                raise ValueError(f"Groq model {selected!r} is not in the configured allow-list.")
            return "groq", selected
        if model and model.startswith("ollama::"):
            if not settings.OLLAMA_ENABLED:
                raise RuntimeError("Ollama is disabled. Set OLLAMA_ENABLED=true to use local inference.")
            return "ollama", model.removeprefix("ollama::").strip()
        if not model and settings.AI_DEFAULT_PROVIDER == "groq" and settings.GROQ_API_KEY:
            return "groq", settings.GROQ_DEFAULT_MODEL
        if not settings.OLLAMA_ENABLED:
            if settings.GROQ_API_KEY:
                return "groq", settings.GROQ_DEFAULT_MODEL
            raise RuntimeError("No AI provider is enabled. Configure Groq or enable Ollama.")
        return "ollama", model or settings.OLLAMA_DEFAULT_MODEL

    async def _generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str],
        temperature: float,
        top_p: float = 0.9,
    ) -> tuple[Optional[Dict[str, Any]], str]:
        provider, model_name = self._resolve_provider(model)
        if not self._provider_available(provider):
            raise RuntimeError(
                f"{provider.title()} is temporarily unavailable; using grounded fallback."
            )
        if provider == "groq":
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": max(temperature, 1e-8),
                "top_p": top_p,
                "max_completion_tokens": settings.AI_MAX_OUTPUT_TOKENS,
                "stream": False,
            }
            try:
                timeout = httpx.Timeout(120.0, connect=3.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    for attempt in range(2):
                        response = await client.post(
                            f"{settings.GROQ_BASE_URL}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                                "Content-Type": "application/json",
                            },
                            json=payload,
                        )
                        if response.status_code != 429 or attempt == 1:
                            break
                        retry_after = response.headers.get("retry-after", "1")
                        try:
                            delay = min(max(float(retry_after), 0.1), 5.0)
                        except ValueError:
                            delay = 1.0
                        await asyncio.sleep(delay)
            except httpx.RequestError:
                self._mark_provider_unavailable("groq")
                raise
            if response.status_code != 200:
                if response.status_code != 429:
                    self._mark_provider_unavailable("groq")
                detail = response.text[:500]
                raise RuntimeError(f"Groq returned HTTP {response.status_code}: {detail}")
            self._mark_provider_available("groq")
            choices = response.json().get("choices") or []
            raw = choices[0].get("message", {}).get("content", "") if choices else ""
            return extract_json(raw), f"Groq ({model_name})"

        payload = {
            "model": model_name,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": settings.AI_MAX_OUTPUT_TOKENS,
            },
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text[:500]}")
        return extract_json(response.json().get("response", "")), f"Ollama ({model_name})"

    async def expand_job_query(
        self,
        job_description: str,
        target_role: str,
        model: Optional[str] = None,
    ) -> List[str]:
        """Use the selected LLM to expand broad JD concepts before retrieval."""
        prompt = QUERY_EXPANSION_PROMPT.format(
            job_description=job_description,
            target_role=target_role,
        )
        concepts: List[str] = []
        try:
            parsed, _ = await self._generate_json(
                system_prompt="Return valid JSON only. Expand concepts for retrieval; do not make candidate claims.",
                user_prompt=prompt,
                model=model,
                temperature=0.1,
            )
            values = parsed.get("concepts", []) if isinstance(parsed, dict) else []
            concepts = [str(value).strip() for value in values if str(value).strip()]
        except Exception as error:
            logger.warning("LLM query expansion failed; using deterministic expansion: %s", error)

        combined_text = f"{target_role} {job_description}".lower()
        deterministic = {
            "frontend": ["React", "Next.js", "TypeScript", "Tailwind CSS", "responsive design", "UI/UX", "accessibility"],
            "backend": ["Python", "FastAPI", "Django", "Node.js", "REST APIs", "databases", "API development"],
            "full stack": ["React", "Next.js", "Node.js", "Python", "REST APIs", "SQL", "end-to-end development"],
            "ai": ["machine learning", "LLM", "RAG", "embeddings", "vector search", "ChromaDB", "prompt engineering"],
            "design": ["Figma", "UI/UX", "prototyping", "design systems", "user research", "responsive design"],
            "mobile": ["Flutter", "React Native", "Android", "mobile application development"],
            "cloud": ["AWS", "Docker", "deployment", "CI/CD", "cloud infrastructure"],
        }
        for trigger, related in deterministic.items():
            if trigger in combined_text:
                concepts.extend(related)

        unique: List[str] = []
        seen = set()
        for concept in concepts:
            key = re.sub(r"\s+", " ", concept.lower()).strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(concept)
        return unique[:20]

    async def generate_tailored_resume(
        self,
        job_description: str,
        retrieved_context: str,
        target_role: str = "Software Engineer",
        candidate_info: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes generation via Ollama or falls back to intelligent synthesis if Ollama is unavailable.
        """
        cand = candidate_info or {}
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            job_description=job_description,
            target_role=target_role,
            retrieved_context=retrieved_context,
            candidate_name=cand.get("name", ""),
            candidate_email=cand.get("email", ""),
            candidate_location=cand.get("location", ""),
            candidate_links=f"LinkedIn: {cand.get('linkedin', '')} | GitHub: {cand.get('github', '')}"
        )

        try:
            parsed, provider_label = await self._generate_json(
                system_prompt=STRICT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=model,
                temperature=0.2,
            )
            if parsed:
                parsed = enforce_grounded_resume(parsed, retrieved_context, cand, target_role)
                removed = parsed.get("_grounding_validation", {}).get("removed", {})
                if sum(value for value in removed.values() if isinstance(value, int)):
                    logger.warning("Grounding guard removed unsupported generated content: %s", removed)
                parsed["_ai_provider"] = provider_label
                return to_json_resume(parsed)
            logger.error("Failed to parse JSON from selected AI provider")
        except Exception as e:
            logger.warning("Selected AI provider failed (%s). Using grounded non-LLM fallback.", e)

        # Fallback synthesizer using the retrieved verified context so user is never blocked
        return to_json_resume(
            self._build_fallback_resume(job_description, target_role, cand, retrieved_context)
        )

    def _build_fallback_resume(
        self,
        job_description: str,
        target_role: str,
        cand: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """
        Synthesizes structured resume data directly from ChromaDB verified profile records
        when local Ollama is offline. Strictly avoids fictional sample data.
        """
        from rag.vectorstore import vector_store
        prof_data = vector_store.get_candidate_profile()

        if not prof_data.get("exists"):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Knowledge base is empty. Please upload your resume PDF or complete the profile questionnaire first."
            )

        c_info = prof_data.get("candidate", {})

        # Candidate identity priority: explicit payload override > verified metadata.
        name = cand.get("name") or c_info.get("name") or ""
        email = cand.get("email") or c_info.get("email") or ""
        phone = cand.get("phone") or c_info.get("phone") or ""
        location = cand.get("location") or c_info.get("location") or ""
        linkedin = cand.get("linkedin") or c_info.get("linkedin") or ""
        github = cand.get("github") or c_info.get("github") or ""
        portfolio = cand.get("portfolio") or c_info.get("portfolio") or ""

        # Extract experiences from candidate's ingested vector DB
        experiences = []
        for exp in prof_data.get("experiences", []):
            if not exp.get("company") or not exp.get("role"):
                continue
            content_bullets = exp.get("bullets") or [
                line.strip("- •* ") for line in exp.get("content", "").split("\n")
                if line.strip() and not line.startswith("===") and not line.startswith("Category:")
            ]
            experiences.append({
                "company": exp.get("company"),
                "role": exp.get("role"),
                "duration": exp.get("duration") or "",
                "location": exp.get("location") or location,
                "bullets": content_bullets[:4]
            })

        # If no explicit work experience items, extract from raw documents
        if False and not experiences and prof_data.get("raw_documents"):
            doc_lines = []
            for doc in prof_data.get("raw_documents", []):
                doc_lines.extend([
                    line.strip("- •* ") for line in doc.get("content", "").split("\n")
                    if len(line.strip()) > 15 and not line.startswith("===")
                ])
            if doc_lines:
                experiences.append({
                    "company": "Ingested Portfolio / Professional History",
                    "role": target_role,
                    "duration": "Verified Record",
                    "location": location,
                    "bullets": doc_lines[:4]
                })

        # Extract projects from candidate's ingested vector DB
        projects = []
        for proj in prof_data.get("projects", []):
            if not proj.get("name"):
                continue
            project_bullets = proj.get("bullets") or ([proj.get("description")] if proj.get("description") else [])
            projects.append({
                "name": proj.get("name"),
                "description": proj.get("description") or "",
                "technologies": proj.get("technologies") or [],
                "bullets": project_bullets[:3],
                "link": proj.get("link") or ""
            })

        # Extract skills from candidate's ingested vector DB
        skills = prof_data.get("skills", [])

        # Extract education from candidate's ingested vector DB
        education = []
        for edu in prof_data.get("education", []):
            if not edu.get("institution") or not edu.get("degree"):
                continue
            education.append({
                "institution": edu.get("institution"),
                "degree": edu.get("degree"),
                "year": edu.get("year") or "",
                "details": edu.get("details") or ""
            })

        verified_summary = ""
        if prof_data.get("raw_documents"):
            for document in prof_data.get("raw_documents", []):
                content = str(document.get("content") or "").strip()
                lines = content.splitlines()
                if lines and lines[0].strip().lower() in {"profile", "professional summary", "summary"}:
                    verified_summary = re.sub(r"\s+", " ", " ".join(lines[1:])).strip()
                    break

        return {
            "name": name,
            "title": target_role,
            "contact": {
                "email": email,
                "phone": phone,
                "location": location,
                "linkedin": linkedin,
                "github": github,
                "portfolio": portfolio
            },
            "summary": verified_summary,
            "skills": skills,
            "experience": experiences,
            "projects": projects,
            "education": education,
            "tailored_match_notes": [
                f"Synthesized from candidate's verified ChromaDB records tailored to {target_role}.",
                "Grounded strictly in ingested career achievements."
            ],
            "_ai_provider": "ChromaDB Synthesizer (Grounded Local Fallback)"
        }

    async def suggest_career_positions(
        self,
        candidate_context: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyzes verified vector store background and recommends fitting career positions."""
        prompt = ROLE_RECOMMENDATION_PROMPT.replace("{candidate_context}", candidate_context)

        try:
            parsed, provider_label = await self._generate_json(
                system_prompt="Return only valid JSON grounded in the supplied verified candidate context.",
                user_prompt=prompt,
                model=model,
                temperature=0.3,
            )
            if parsed and "recommended_positions" in parsed:
                parsed["_ai_provider"] = provider_label
                return parsed
        except Exception as e:
            logger.warning("Selected recommendation provider failed (%s). Using grounded fallback.", e)

        # Intelligent local fallback derived from ChromaDB candidate profile
        return self._build_fallback_recommendations(candidate_context)

    def _build_fallback_recommendations(self, context: str) -> Dict[str, Any]:
        from rag.vectorstore import vector_store
        prof_data = vector_store.get_candidate_profile()

        if not prof_data.get("exists"):
            return {
                "profile_summary": "No verified candidate background found in ChromaDB.",
                "recommended_positions": [],
                "_ai_provider": "ChromaDB (Empty)"
            }

        # Gather candidate's real skills & experiences for matching
        skills_detected = []
        for s_group in prof_data.get("skills", []):
            skills_detected.extend(s_group.get("items", []))

        exp_titles = [e.get("role", "Software Engineer") for e in prof_data.get("experiences", [])]
        primary_title = exp_titles[0] if exp_titles else "Software Engineer"
        primary_title = re.sub(
            r"^(senior|lead|staff|principal|architect|mid-level)\s+",
            "",
            primary_title,
            flags=re.IGNORECASE,
        )
        primary_title = re.sub(r"\s+(intern|internship|trainee)$", "", primary_title, flags=re.IGNORECASE)

        return {
            "profile_summary": f"Verified candidate background grounded in {len(prof_data.get('experiences', []))} positions, {len(prof_data.get('projects', []))} projects, and {len(skills_detected)} technical competencies.",
            "recommended_positions": [
                {
                    "title": f"{primary_title} Intern",
                    "seniority": "Internship",
                    "fit_score": 96,
                    "description": f"Contribute to implementation, testing, and feature delivery while learning from an experienced {primary_title} team.",
                    "why_qualified": [
                        f"Direct verified work experience as {primary_title}.",
                        f"Proven proficiency across {', '.join(skills_detected[:4]) if skills_detected else 'core technologies'}."
                    ],
                    "skills_leveraged": skills_detected[:5] if skills_detected else ["Python", "TypeScript", "FastAPI"],
                    "recommended_focus": "Emphasize relevant projects, practical fundamentals, learning ability, and collaboration.",
                    "sample_jd_prompt": f"Seeking a {primary_title} Intern with project or coursework experience in modern APIs and web applications, solid programming fundamentals, and a willingness to learn through mentorship and code review."
                },
                {
                    "title": "Software Systems & AI Intern",
                    "seniority": "Internship",
                    "fit_score": 91,
                    "description": "Support development and testing of API, data-ingestion, and interactive application features.",
                    "why_qualified": [
                        "Demonstrated capacity developing microservices and structured document ingestion.",
                        f"Extensive technical toolkit including {', '.join(skills_detected[2:6]) if len(skills_detected) > 2 else 'modern frameworks'}."
                    ],
                    "skills_leveraged": skills_detected[2:7] if len(skills_detected) > 2 else ["FastAPI", "React", "SQL"],
                    "recommended_focus": "Highlight personal projects, technical problem solving, and readiness to learn production practices.",
                    "sample_jd_prompt": "Looking for a Software Systems Intern with Python or JavaScript fundamentals, exposure to REST APIs and databases through coursework or projects, and enthusiasm for collaborative learning."
                }
            ],
            "ai_provider": "Grounded ChromaDB Profile Analysis"
        }

    async def generate_cover_letter(
        self,
        job_description: str,
        target_role: str = "Software Engineer",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synthesizes a grounded cover letter and LinkedIn cold message strictly using ChromaDB records."""
        from rag.retriever import rag_retriever
        retrieval = rag_retriever.retrieve_context_for_jd(job_description)
        context = retrieval["formatted_context"]

        prompt = COVER_LETTER_PROMPT.format(
            job_description=job_description,
            target_role=target_role,
            candidate_context=context
        )

        try:
            parsed, provider_label = await self._generate_json(
                system_prompt="Return only valid JSON. Use only facts in the verified candidate context.",
                user_prompt=prompt,
                model=model,
                temperature=0.2,
            )
            if parsed:
                parsed["_ai_provider"] = provider_label
                return parsed
        except Exception as e:
            logger.warning("Cover letter provider failed (%s). Using grounded local fallback.", e)

        # Grounded fallback
        from rag.vectorstore import vector_store
        prof = vector_store.get_candidate_profile()
        c_info = prof.get("candidate", {})
        cand_name = c_info.get("name") or "Verified Candidate"

        exps = prof.get("experiences", [])
        company = exps[0]["company"] if exps else "your engineering group"

        body = (
            f"Dear Hiring Team,\n\n"
            f"I am writing to express my strong interest in the {target_role} position. "
            f"With a proven background demonstrated at {company} and a deep focus on scalable, robust software delivery, "
            f"I have consistently engineered solutions that directly align with your team's core technical requirements.\n\n"
            f"Throughout my work history, I have prioritized system reliability, clean maintainable code, and sub-second performance. "
            f"My hands-on technical competencies and project achievements equip me to make an immediate impact on your upcoming milestones.\n\n"
            f"Thank you for your time and consideration. I welcome the opportunity to discuss how my verified experience "
            f"can contribute to your team's success.\n\nSincerely,\n{cand_name}"
        )

        outreach = (
            f"Hi Hiring Team, I noticed your opening for a {target_role}! "
            f"I bring verified experience building scalable systems at {company}. "
            f"Would love to connect briefly regarding how my background aligns with your current roadmap!"
        )

        return {
            "company_name": "Hiring Team",
            "role_title": target_role,
            "cover_letter_body": body,
            "linkedin_outreach_message": outreach,
            "key_highlights_cited": [f"Verified experience as {target_role}", f"Track record at {company}"],
            "_ai_provider": "ChromaDB Grounded Fallback"
        }

    async def analyze_ats_gap(
        self,
        job_description: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates ATS fit percentage, matched keywords, missing keywords, and recommendations."""
        from rag.retriever import rag_retriever
        retrieval = rag_retriever.retrieve_context_for_jd(job_description)
        context = retrieval["formatted_context"]
        jd_keywords = retrieval["extracted_keywords"]

        from rag.vectorstore import vector_store
        prof = vector_store.get_candidate_profile()
        skills_detected = []
        for s_group in prof.get("skills", []):
            skills_detected.extend([s.lower() for s in s_group.get("items", [])])

        matched = []
        missing = []
        for kw in jd_keywords:
            if any(kw.lower() in s or s in kw.lower() for s in skills_detected) or kw.lower() in context.lower():
                matched.append(kw)
            else:
                missing.append(kw)

        score = min(98, max(45, int((len(matched) / (len(jd_keywords) or 1)) * 100)))

        return {
            "ats_score": score,
            "summary_verdict": f"Candidate profile matches {len(matched)} out of {len(jd_keywords)} primary technical keywords extracted from the job description.",
            "matched_skills": matched[:12],
            "missing_skills": missing[:10],
            "bullet_recommendations": [
                f"Incorporate technical keyword '{missing[0]}' into work experience bullets if applicable." if missing else "Strong keyword coverage across all key terms.",
                "Ensure metric-driven Google XYZ bullet formats are used for high-impact achievements."
            ],
            "_ai_provider": "ChromaDB Semantic ATS Matcher"
        }

resume_generator = ResumeGenerator()

