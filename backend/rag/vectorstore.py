import chromadb
from chromadb import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import uuid
import logging
from config import settings

logger = logging.getLogger("resume_rag.vectorstore")

class ChromaManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaManager, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_names = ["experiences", "skills", "projects", "education", "raw_documents"]
        self.collections = {}
        for name in self.collection_names:
            self.collections[name] = self.client.get_or_create_collection(
                name=f"{settings.COLLECTION_NAME}_{name}",
                metadata={"hnsw:space": "cosine"}
            )
        logger.info("ChromaDB initialized with collections: %s", self.collection_names)

    def get_collection(self, name: str):
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=f"{settings.COLLECTION_NAME}_{name}",
                metadata={"hnsw:space": "cosine"}
            )
        return self.collections[name]

    def add_items(self, collection_name: str, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None):
        if not texts:
            return []
        col = self.get_collection(collection_name)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{"category": collection_name} for _ in texts]
        
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

    def query(self, query_text: str, collection_names: Optional[List[str]] = None, n_results: int = 5) -> List[Dict[str, Any]]:
        target_collections = collection_names or ["experiences", "projects", "skills", "education", "raw_documents"]
        combined_results = []

        for name in target_collections:
            try:
                col = self.get_collection(name)
                count = col.count()
                if count == 0:
                    continue

                top_k = min(n_results, count)
                results = col.query(
                    query_texts=[query_text],
                    n_results=top_k
                )

                if results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
                    ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

                    for doc, meta, dist, item_id in zip(docs, metas, distances, ids):
                        # cosine distance: 0 is identical, similarity = 1 - distance
                        sim = max(0.0, min(1.0, 1.0 - (dist if dist is not None else 0.0)))
                        combined_results.append({
                            "id": item_id,
                            "collection": name,
                            "content": doc,
                            "metadata": meta,
                            "similarity": round(sim, 4)
                        })
            except Exception as e:
                logger.warning("Skipping collection '%s' during query due to error: %s", name, e)
                continue

        # Sort combined results by similarity descending
        combined_results.sort(key=lambda x: x["similarity"], reverse=True)
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

        experiences = []
        projects = []
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
                for key in ["name", "email", "phone", "location", "linkedin", "github", "portfolio"]:
                    if not candidate[key] and meta.get(key):
                        candidate[key] = str(meta[key]).strip()

                # Fallback email extraction from raw text if missing
                if not candidate["email"]:
                    match = email_regex.search(doc)
                    if match:
                        candidate["email"] = match.group(0)

                # Categorize item by type
                if cat == "experiences":
                    experiences.append({
                        "company": meta.get("company", "Company"),
                        "role": meta.get("role", "Position"),
                        "duration": meta.get("duration", ""),
                        "location": meta.get("location", ""),
                        "content": doc,
                        "technologies": [t.strip() for t in meta.get("technologies", "").split(",") if t.strip()]
                    })
                elif cat == "projects":
                    projects.append({
                        "name": meta.get("name") or meta.get("project_name") or "Project",
                        "description": doc,
                        "technologies": [t.strip() for t in meta.get("technologies", "").split(",") if t.strip()],
                        "link": meta.get("link", "")
                    })
                elif cat == "skills":
                    group = meta.get("category", "General Skills")
                    if group not in skills_map:
                        skills_map[group] = []
                    skill_item = meta.get("skill") or doc
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

vector_store = ChromaManager()
