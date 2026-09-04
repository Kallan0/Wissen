import chromadb
from chromadb.config import Settings as ChromaSettings
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

        # Sort combined results by similarity descending
        combined_results.sort(key=lambda x: x["similarity"], reverse=True)
        return combined_results[:n_results]

    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        total = 0
        for name, col in self.collections.items():
            cnt = col.count()
            stats[name] = cnt
            total += cnt
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
