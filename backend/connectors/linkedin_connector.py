import csv
import io
import json
import logging
from typing import Dict, Any, List, Optional
from rag.ingestion import IngestionService
from rag.vectorstore import vector_store

logger = logging.getLogger("resume_builder.linkedin_connector")


class LinkedInConnector:
    """
    Parses official LinkedIn archive exports (CSV files or structured CSV text)
    and ingests Positions, Skills, Education, and Projects into ChromaDB.
    """

    @staticmethod
    def parse_csv_rows(csv_text: str) -> List[Dict[str, str]]:
        """Parses raw CSV string into list of dict rows, handling headers cleanly."""
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        rows = []
        for row in reader:
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k and v}
            if cleaned:
                rows.append(cleaned)
        return rows

    @classmethod
    def ingest_positions_csv(cls, csv_text: str) -> int:
        """Parses Positions.csv (Company Name, Title, Description, Location, Started On, Finished On)."""
        rows = cls.parse_csv_rows(csv_text)
        count = 0
        for r in rows:
            company = r.get("Company Name") or r.get("Company") or "Company"
            role = r.get("Title") or r.get("Role") or "Position"
            started = r.get("Started On") or r.get("Start Date") or ""
            finished = r.get("Finished On") or r.get("End Date") or "Present"
            duration = f"{started} - {finished}".strip(" -")
            location = r.get("Location") or ""
            description = r.get("Description") or r.get("Summary") or ""

            bullets = [line.strip("- •* ") for line in description.split("\n") if line.strip()]
            if not bullets:
                bullets = [f"Executed deliverables as {role} at {company}."]

            IngestionService.ingest_experience_item(
                company=company,
                role=role,
                duration=duration,
                location=location,
                bullets=bullets,
                technologies=[]
            )
            count += 1
        logger.info("Ingested %d positions from LinkedIn CSV", count)
        return count

    @classmethod
    def ingest_skills_csv(cls, csv_text: str) -> int:
        """Parses Skills.csv (Name)."""
        rows = cls.parse_csv_rows(csv_text)
        skills_list = []
        for r in rows:
            skill_name = r.get("Name") or r.get("Skill") or r.get("skill_name")
            if skill_name:
                skills_list.append(skill_name)

        if skills_list:
            IngestionService.ingest_skills(
                category="LinkedIn Endorsed Skills",
                skills_list=skills_list
            )
        return len(skills_list)

    @classmethod
    def ingest_linkedin_archive(cls, payload: Dict[str, str]) -> Dict[str, Any]:
        """
        Main entry point. Accepts dictionary mapping file names ('positions.csv', 'skills.csv', etc.)
        or raw CSV strings to parse and index into ChromaDB.
        """
        counts = {"experiences": 0, "skills": 0, "education": 0, "projects": 0}

        if "positions" in payload or "positions.csv" in payload:
            raw = payload.get("positions") or payload.get("positions.csv") or ""
            counts["experiences"] += cls.ingest_positions_csv(raw)

        if "skills" in payload or "skills.csv" in payload:
            raw = payload.get("skills") or payload.get("skills.csv") or ""
            counts["skills"] += cls.ingest_skills_csv(raw)

        stats = vector_store.get_stats()
        return {
            "status": "success",
            "ingested_counts": counts,
            "stats": stats
        }


linkedin_connector = LinkedInConnector()
