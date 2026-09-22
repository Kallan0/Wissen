from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from rag.ingestion import IngestionService

logger = logging.getLogger("resume_rag.creative_fs_connector")

class CreativeFileSystemConnector:
    @staticmethod
    def scan_and_ingest_directory(
        directory_path: str,
        custom_project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scans a local filesystem folder (Unity, Blender, or code repository),
        detects metadata, summaries, and file distributions, then embeds the project.
        """
        path = Path(directory_path).resolve()
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Directory path '{directory_path}' does not exist or is not a directory.")

        project_name = custom_project_name or path.name
        technologies = set()
        highlights = []
        project_type = "General Project"

        # 1. Check for Unity project markers
        is_unity = (path / "Assets").exists() and (path / "ProjectSettings").exists()
        if is_unity:
            project_type = "Unity Game Engine Project"
            technologies.add("Unity")
            technologies.add("C#")
            technologies.add("Game Development")

        # 2. Check for Blender project markers
        blend_files = list(path.glob("*.blend")) + list(path.glob("**/*.blend"))[:10]
        if blend_files:
            if not is_unity:
                project_type = "3D Graphics & Blender Project"
            technologies.add("Blender")
            technologies.add("3D Modeling")
            highlights.append(f"Contains {len(blend_files)} 3D scene (.blend) files.")

        # 3. Check for specific summary or README files
        summary_candidates = ["project_summary.txt", "SUMMARY.md", "README.md", "readme.txt"]
        summary_text = ""
        for cand in summary_candidates:
            cand_path = path / cand
            if cand_path.exists():
                try:
                    with open(cand_path, "r", encoding="utf-8", errors="ignore") as f:
                        summary_text = f.read(1500)
                        highlights.append(f"Project Description from {cand}: {summary_text[:200]}...")
                        break
                except Exception:
                    pass

        # 4. Inventory file types
        csharp_scripts = list(path.glob("**/*.cs"))[:50]
        python_scripts = list(path.glob("**/*.py"))[:50]
        shader_files = list(path.glob("**/*.shader")) + list(path.glob("**/*.hlsl"))

        if csharp_scripts:
            technologies.add("C#")
            highlights.append(f"Engineered {len(csharp_scripts)} C# source script components.")
        if python_scripts:
            technologies.add("Python")
            highlights.append(f"Implemented {len(python_scripts)} Python automation scripts.")
        if shader_files:
            technologies.add("Shaders / HLSL")
            highlights.append(f"Authored {len(shader_files)} custom shader and lighting programs.")

        # 5. Fallback description
        description = summary_text[:300] if summary_text else f"{project_type} located at {path.name} featuring modular asset pipelines and custom code architecture."
        
        tech_list = list(technologies) if technologies else ["Software Development", "Local Workspace"]

        # Ingest into ChromaDB projects
        path_str = str(path).replace("\\", "/")
        IngestionService.ingest_project_item(
            name=f"{project_name} ({project_type})",
            description=description,
            highlights=highlights if highlights else [f"Local project workspace containing active codebase at {path.name}"],
            technologies=tech_list,
            link=f"file:///{path_str}"
        )

        # Ingest identified technologies as skills
        if technologies:
            IngestionService.ingest_skills(
                category=f"{project_type} Stack",
                skills_list=tech_list
            )

        return {
            "project_name": project_name,
            "project_type": project_type,
            "detected_technologies": tech_list,
            "directory_path": str(path),
            "highlights_count": len(highlights)
        }

creative_fs_connector = CreativeFileSystemConnector()
