import logging
from typing import Dict, Any, List, Optional
from rag.ingestion import IngestionService

logger = logging.getLogger("resume_rag.canva_connector")

class CanvaDesignConnector:
    @staticmethod
    def ingest_design_project(
        title: str,
        description: str,
        design_type: str = "UI/UX & Visual Design",
        tools_used: Optional[List[str]] = None,
        prototype_url: Optional[str] = None,
        deliverables: Optional[List[str]] = None,
        user_impact: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses Canva/Figma/UI-UX design projects, extracts design competencies,
        and indexes the case study into ChromaDB projects and skills collections.
        """
        tools = tools_used or ["Canva", "Figma"]
        highlights = []
        
        if deliverables and len(deliverables) > 0:
            highlights.append("Deliverables: " + ", ".join(deliverables) + ".")
        if user_impact and user_impact.strip():
            highlights.append("Design & Business Impact: " + user_impact.strip())
        
        highlights.append(f"Design Discipline: {design_type} using {', '.join(tools)}.")

        # Ingest into projects collection
        IngestionService.ingest_project_item(
            name=f"{title} ({design_type})",
            description=description,
            highlights=highlights,
            technologies=tools,
            link=prototype_url
        )

        # Ingest design skills
        IngestionService.ingest_skills(
            category="Design & Creative Tools",
            skills_list=tools + [design_type, "Wireframing", "Visual Hierarchy"]
        )

        return {
            "title": title,
            "design_type": design_type,
            "tools": tools,
            "status": "indexed"
        }

canva_connector = CanvaDesignConnector()
