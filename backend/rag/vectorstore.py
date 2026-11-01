from typing import List, Dict, Any, Optional
import hashlib
import math
import re
import logging
import threading
from config import settings
from rag.embeddings import get_embedding_function

logger = logging.getLogger("resume_rag.vectorstore")


def _document_fingerprint(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _search_tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9][a-z0-9+#.]*", text.lower())


def _bm25_scores(query: str, documents: List[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
    """Small dependency-free BM25 scorer for the local Chroma corpus."""
    query_terms = set(_search_tokens(query))
    tokenized = [_search_tokens(document) for document in documents]
    if not query_terms or not documents:
        return [0.0] * len(documents)
    average_length = sum(len(tokens) for tokens in tokenized) / max(len(tokenized), 1)
    document_frequency = {
        term: sum(1 for tokens in tokenized if term in set(tokens))
        for term in query_terms
    }
    scores: List[float] = []
    for tokens in tokenized:
        frequencies: Dict[str, int] = {}
        for token in tokens:
            frequencies[token] = frequencies.get(token, 0) + 1
        score = 0.0
        for term in query_terms:
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            frequency_in_documents = document_frequency[term]
            inverse_frequency = math.log(
                1 + (len(documents) - frequency_in_documents + 0.5) / (frequency_in_documents + 0.5)
            )
            length_factor = 1 - b + b * len(tokens) / max(average_length, 1.0)
            score += inverse_frequency * frequency * (k1 + 1) / (frequency + k1 * length_factor)
        scores.append(score)
    return scores


def _hybrid_weights() -> tuple[float, float]:
    dense = max(0.0, settings.HYBRID_DENSE_WEIGHT)
    lexical = max(0.0, settings.HYBRID_BM25_WEIGHT)
    total = dense + lexical
    return (dense / total, lexical / total) if total else (0.7, 0.3)

class ChromaManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super(ChromaManager, cls).__new__(cls)
            instance._init_client()
            cls._instance = instance
        return cls._instance

    def _init_client(self):
        import chromadb
        from chromadb import Settings as ChromaSettings

        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_function = get_embedding_function()
        self._query_embedding_cache: Dict[str, Any] = {}
        self._query_embedding_lock = threading.Lock()
        self.collection_names = ["experiences", "skills", "projects", "education", "raw_documents"]
        self.collections = {}
        for name in self.collection_names:
            self.collections[name] = self.client.get_or_create_collection(
                name=f"{settings.COLLECTION_NAME}_{name}",
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function,
            )
        logger.info("ChromaDB initialized with collections: %s", self.collection_names)

    def get_collection(self, name: str):
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=f"{settings.COLLECTION_NAME}_{name}",
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function,
            )
        return self.collections[name]

    def add_items(self, collection_name: str, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None):
        if not texts:
            return []
        col = self.get_collection(collection_name)
        if metadatas is None:
            metadatas = [{"category": collection_name} for _ in texts]

        # Repeated connector syncs and resume uploads must be idempotent. Clean
        # historical exact duplicates and refuse duplicates from the new batch.
        existing = col.get(include=["documents"])
        existing_by_fingerprint: Dict[str, str] = {}
        redundant_existing_ids: List[str] = []
        for existing_id, document in zip(existing.get("ids", []), existing.get("documents", [])):
            fingerprint = _document_fingerprint(document or "")
            if fingerprint in existing_by_fingerprint:
                redundant_existing_ids.append(existing_id)
            else:
                existing_by_fingerprint[fingerprint] = existing_id
        if redundant_existing_ids:
            col.delete(ids=redundant_existing_ids)
            logger.info("Removed %d duplicate records from %s", len(redundant_existing_ids), collection_name)

        supplied_ids = ids or [None] * len(texts)
        unique_rows = []
        batch_fingerprints = set()
        for text, metadata, supplied_id in zip(texts, metadatas, supplied_ids):
            fingerprint = _document_fingerprint(text)
            if not fingerprint or fingerprint in existing_by_fingerprint or fingerprint in batch_fingerprints:
                continue
            batch_fingerprints.add(fingerprint)
            stable_id = supplied_id or f"{collection_name}-{fingerprint[:32]}"
            unique_rows.append((text, metadata, stable_id))
        if not unique_rows:
            return []
        texts = [row[0] for row in unique_rows]
        metadatas = [row[1] for row in unique_rows]
        ids = [row[2] for row in unique_rows]
        
        # Clean metadatas for ChromaDB (must only have str, int, float, bool)
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif isinstance(v, list):
                    clean_meta[k] = ", ".join(str(item) for item in v)
                elif v is None:
                    clean_meta[k] = ""
                else:
                    clean_meta[k] = str(v)
            clean_metadatas.append(clean_meta)

        col.upsert(
            documents=texts,
            metadatas=clean_metadatas,
            ids=ids
        )
        return ids

    def replace_source_items(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        *,
        source_field: str,
        source_value: str,
    ) -> List[str]:
        """Replace one source after its new chunks embed successfully.

        Exact chunks may be retained by ``add_items``. Obsolete chunks are
        deleted only after every replacement chunk has been processed, so an
        embedding failure cannot erase the previous source.
        """
        col = self.get_collection(collection_name)
        previous = col.get(where={source_field: source_value}, include=["documents"])
        previous_rows = list(zip(previous.get("ids", []), previous.get("documents", []) or []))
        replacement_fingerprints = {_document_fingerprint(text) for text in texts if _document_fingerprint(text)}
        inserted_ids = self.add_items(collection_name, texts, metadatas)
        retained_ids = [
            item_id for item_id, document in previous_rows
            if _document_fingerprint(document or "") in replacement_fingerprints
        ]
        obsolete_ids = [
            item_id for item_id, document in previous_rows
            if _document_fingerprint(document or "") not in replacement_fingerprints
        ]
        if obsolete_ids:
            col.delete(ids=obsolete_ids)
            logger.info("Replaced %d obsolete chunks for %s=%s", len(obsolete_ids), source_field, source_value)
        return retained_ids + inserted_ids

    def query(self, query_text: str, collection_names: Optional[List[str]] = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Hybrid search: HNSW ANN dense candidates fused with corpus BM25."""
        target_collections = collection_names or ["experiences", "projects", "skills", "education", "raw_documents"]
        combined_results: List[Dict[str, Any]] = []
        dense_weight, lexical_weight = _hybrid_weights()
        query_embedding = None
        embedding_failed = False
        embedding_function = getattr(self, "embedding_function", None)
        if embedding_function is not None:
            cache_key = hashlib.sha256(query_text.encode("utf-8")).hexdigest()
            cache = getattr(self, "_query_embedding_cache", {})
            lock = getattr(self, "_query_embedding_lock", threading.Lock())
            try:
                with lock:
                    query_embedding = cache.get(cache_key)
                if query_embedding is None:
                    query_embedding = embedding_function([query_text])[0]
                    with lock:
                        if len(cache) >= 64:
                            cache.pop(next(iter(cache)))
                        cache[cache_key] = query_embedding
                    self._query_embedding_cache = cache
                    self._query_embedding_lock = lock
            except Exception as embedding_error:
                embedding_failed = True
                logger.warning("Dense query embedding failed; continuing with BM25: %s", embedding_error)

        for name in target_collections:
            try:
                col = self.get_collection(name)
                count = col.count()
                if count == 0:
                    continue

                corpus = col.get(include=["documents", "metadatas"])
                corpus_ids = corpus.get("ids", [])
                corpus_documents = corpus.get("documents", []) or []
                corpus_metadatas = corpus.get("metadatas", []) or [{}] * len(corpus_documents)
                lexical_scores = _bm25_scores(query_text, corpus_documents)
                maximum_lexical = max(lexical_scores, default=0.0)

                # Chroma's cosine HNSW index supplies approximate dense nearest
                # neighbours. A wider candidate pool improves fusion recall.
                candidate_count = min(count, max(n_results * 4, 20))
                dense_available = True
                try:
                    if embedding_failed:
                        raise RuntimeError("query embedding is unavailable")
                    query_arguments = (
                        {"query_embeddings": [query_embedding]}
                        if query_embedding is not None
                        else {"query_texts": [query_text]}
                    )
                    dense_results = col.query(
                        **query_arguments,
                        n_results=candidate_count,
                        include=["documents", "metadatas", "distances"],
                    )
                    dense_ids = dense_results.get("ids", [[]])[0] if dense_results else []
                    dense_distances = dense_results.get("distances", [[]])[0] if dense_results else []
                    dense_by_id = {
                        item_id: max(0.0, min(1.0, 1.0 - float(distance or 0.0)))
                        for item_id, distance in zip(dense_ids, dense_distances)
                    }
                except Exception as dense_error:
                    dense_available = False
                    dense_by_id = {}
                    logger.warning(
                        "Dense embedding query failed for '%s'; continuing with BM25: %s",
                        name,
                        dense_error,
                    )

                collection_results: List[Dict[str, Any]] = []
                for item_id, document, metadata, bm25 in zip(
                    corpus_ids, corpus_documents, corpus_metadatas, lexical_scores
                ):
                    dense_score = dense_by_id.get(item_id, 0.0)
                    lexical_score = bm25 / maximum_lexical if maximum_lexical else 0.0
                    hybrid_score = (
                        dense_weight * dense_score + lexical_weight * lexical_score
                        if dense_available else lexical_score
                    )
                    if hybrid_score < max(0.0, settings.HYBRID_MIN_SCORE):
                        continue
                    collection_results.append({
                        "id": item_id,
                        "collection": name,
                        "content": document,
                        "metadata": metadata or {},
                        "similarity": round(hybrid_score, 4),
                        "dense_score": round(dense_score, 4),
                        "bm25_score": round(lexical_score, 4),
                        "retrieval_method": (
                            "hybrid_hnsw_ann_bm25" if dense_available else "bm25_degraded_fallback"
                        ),
                    })
                collection_results.sort(key=lambda item: item["similarity"], reverse=True)
                combined_results.extend(collection_results[:n_results])
            except Exception as e:
                logger.warning("Skipping collection '%s' during query due to error: %s", name, e)
                continue

        def _get_similarity(item: Dict[str, Any]) -> float:
            val = item.get("similarity", 0.0)
            if isinstance(val, (int, float)):
                return float(val)
            return 0.0

        # Sort combined results by similarity descending
        combined_results.sort(key=_get_similarity, reverse=True)
        return combined_results[:n_results]

    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        total = 0
        for name, col in self.collections.items():
            try:
                cnt = col.count()
                stats[name] = cnt
                total += cnt
            except Exception as e:
                logger.warning("Could not count collection '%s': %s", name, e)
                stats[name] = 0
        stats["total_items"] = total
        return stats

    def get_all_items(self) -> Dict[str, List[Dict[str, Any]]]:
        all_data = {}
        for name, col in self.collections.items():
            cnt = col.count()
            if cnt > 0:
                records = col.get()
                items = []
                for i in range(len(records["ids"])):
                    items.append({
                        "id": records["ids"][i],
                        "document": records["documents"][i],
                        "metadata": records["metadatas"][i] if records["metadatas"] else {}
                    })
                all_data[name] = items
            else:
                all_data[name] = []
        return all_data

    def get_candidate_profile(self) -> Dict[str, Any]:
        """
        Extracts verified candidate profile metadata, contact info, and structured records
        from ChromaDB. Returns exists=False if the knowledge base is empty.
        """
        all_items = self.get_all_items()
        total_items = sum(len(items) for items in all_items.values())

        if total_items == 0:
            return {"exists": False, "total_items": 0, "candidate": {}, "experiences": [], "projects": [], "skills": [], "education": []}

        candidate = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "github": "",
            "portfolio": ""
        }

        experience_map: Dict[str, Dict[str, Any]] = {}
        project_map: Dict[str, Dict[str, Any]] = {}
        skills_map = {}
        education = []
        raw_documents = []

        # Scan all collections for candidate contact metadata
        import re
        email_regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

        for cat, items in all_items.items():
            for item in items:
                meta = item.get("metadata") or {}
                doc = item.get("document") or ""

                # Extract contact attributes if present in metadata
                if meta.get("candidate_name"):
                    candidate["name"] = str(meta["candidate_name"]).strip()
                elif not candidate["name"] and cat != "projects" and meta.get("name"):
                    candidate["name"] = str(meta["name"]).strip()

                for key in ["email", "phone", "location", "linkedin", "github", "portfolio"]:
                    if not candidate[key] and meta.get(key):
                        candidate[key] = str(meta[key]).strip()

                # Fallback email extraction from raw text if missing
                if not candidate["email"]:
                    match = email_regex.search(doc)
                    if match:
                        candidate["email"] = match.group(0)

                if cat == "raw_documents":
                    if not candidate["name"]:
                        name_match = re.match(
                            r"^\s*([A-Z][A-Z .'-]{2,60}?)\s+(?=(?:Bachelor|Master|BCA|B\.Tech|M\.Tech)\b)",
                            doc,
                        )
                        if name_match:
                            candidate["name"] = name_match.group(1).strip()
                    if not candidate["phone"]:
                        phone_match = re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){9,12}\d", doc)
                        if phone_match:
                            candidate["phone"] = phone_match.group(0).strip()

                # Categorize item by type
                if cat == "experiences":
                    company = str(meta.get("company", "Company")).strip()
                    role = str(meta.get("role", "Position")).strip()
                    entity_key = re.sub(r"[^a-z0-9]+", " ", f"{company}|{role}".lower()).strip()
                    record = experience_map.setdefault(entity_key, {
                        "company": company,
                        "role": role,
                        "duration": "",
                        "location": "",
                        "content_parts": [],
                        "bullets": [],
                        "technologies": [],
                    })
                    record["duration"] = record["duration"] or meta.get("duration", "")
                    record["location"] = record["location"] or meta.get("location", "")
                    if doc and doc not in record["content_parts"]:
                        record["content_parts"].append(doc)
                    bullet = str(meta.get("bullet", "")).strip()
                    if not bullet and meta.get("type") == "experience_bullet":
                        bullet = re.sub(r"^Experience Achievement at .*? as .*?:\s*", "", doc)
                        bullet = re.sub(r"\s*\[Tech:.*\]\s*$", "", bullet).strip()
                    if bullet and bullet not in record["bullets"]:
                        record["bullets"].append(bullet)
                    for technology in str(meta.get("technologies", "")).split(","):
                        technology = technology.strip()
                        if technology and technology not in record["technologies"]:
                            record["technologies"].append(technology)
                elif cat == "projects":
                    name = str(meta.get("name") or meta.get("project_name") or "Project").strip()
                    entity_key = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
                    record = project_map.setdefault(entity_key, {
                        "name": name,
                        "description": "",
                        "content_parts": [],
                        "bullets": [],
                        "technologies": [],
                        "link": "",
                    })
                    record["description"] = record["description"] or meta.get("description", "")
                    record["link"] = record["link"] or meta.get("link", "")
                    if doc and doc not in record["content_parts"]:
                        record["content_parts"].append(doc)
                    highlight = str(meta.get("highlight", "")).strip()
                    if not highlight and meta.get("type") == "project_highlight":
                        highlight = re.sub(r"^Project .*? detail:\s*", "", doc)
                        highlight = re.sub(r"\s*\(Technologies:.*\)\s*$", "", highlight).strip()
                    if highlight and highlight not in record["bullets"]:
                        record["bullets"].append(highlight)
                    for technology in str(meta.get("technologies", "")).split(","):
                        technology = technology.strip()
                        if technology and technology not in record["technologies"]:
                            record["technologies"].append(technology)
                elif cat == "skills":
                    group = meta.get("category", "General Skills")
                    if group not in skills_map:
                        skills_map[group] = []
                    skill_values = str(meta.get("skills") or meta.get("skill") or "").split(",")
                    if not any(value.strip() for value in skill_values):
                        skill_values = [doc]
                    for skill_item in skill_values:
                        skill_item = skill_item.strip()
                        if skill_item and skill_item not in skills_map[group]:
                            skills_map[group].append(skill_item)
                elif cat == "education":
                    education.append({
                        "institution": meta.get("institution", "Institution"),
                        "degree": meta.get("degree", "Degree"),
                        "year": meta.get("year", ""),
                        "details": doc
                    })
                elif cat == "raw_documents":
                    raw_documents.append({"title": meta.get("title", "Document"), "content": doc})

        experiences = []
        for record in experience_map.values():
            record["content"] = "\n".join(record.pop("content_parts"))
            experiences.append(record)
        projects = []
        for record in project_map.values():
            content_parts = record.pop("content_parts")
            record["description"] = record["description"] or (content_parts[0] if content_parts else "")
            projects.append(record)

        formatted_skills = [{"category": cat, "items": items} for cat, items in skills_map.items()]

        return {
            "exists": True,
            "total_items": total_items,
            "candidate": candidate,
            "experiences": experiences,
            "projects": projects,
            "skills": formatted_skills,
            "education": education,
            "raw_documents": raw_documents
        }

    def delete_item(self, collection_name: str, item_id: str):
        col = self.get_collection(collection_name)
        col.delete(ids=[item_id])

    def clear_all(self):
        for name in self.collection_names:
            try:
                self.client.delete_collection(name=f"{settings.COLLECTION_NAME}_{name}")
            except Exception:
                pass
        self._init_client()

class LazyChromaManager:
    """Initialize ChromaDB only when a knowledge-base operation needs it."""

    def __init__(self) -> None:
        self._manager: Optional[ChromaManager] = None
        self._lock = threading.Lock()

    def _get_manager(self) -> ChromaManager:
        if self._manager is None:
            with self._lock:
                if self._manager is None:
                    self._manager = ChromaManager()
        return self._manager

    @property
    def is_initialized(self) -> bool:
        return self._manager is not None

    def get_collection(self, name: str):
        return self._get_manager().get_collection(name)

    def add_items(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ):
        return self._get_manager().add_items(collection_name, texts, metadatas, ids)

    def query(
        self,
        query_text: str,
        collection_names: Optional[List[str]] = None,
        n_results: int = 5,
    ):
        return self._get_manager().query(query_text, collection_names, n_results)

    def replace_source_items(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        *,
        source_field: str,
        source_value: str,
    ):
        return self._get_manager().replace_source_items(
            collection_name,
            texts,
            metadatas,
            source_field=source_field,
            source_value=source_value,
        )

    def get_stats(self):
        return self._get_manager().get_stats()

    def get_all_items(self):
        return self._get_manager().get_all_items()

    def get_candidate_profile(self):
        return self._get_manager().get_candidate_profile()

    def delete_item(self, collection_name: str, item_id: str):
        return self._get_manager().delete_item(collection_name, item_id)

    def clear_all(self):
        return self._get_manager().clear_all()

    def __getattr__(self, name: str):
        return getattr(self._get_manager(), name)


vector_store = LazyChromaManager()
