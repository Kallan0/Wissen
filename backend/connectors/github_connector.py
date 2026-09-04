import logging
import base64
import httpx
from typing import Dict, Any, List, Optional
from rag.ingestion import IngestionService

logger = logging.getLogger("resume_rag.github_connector")

class GitHubConnector:
    @staticmethod
    async def sync_user_repositories(
        username: str,
        token: Optional[str] = None,
        max_repos: int = 15,
        fetch_readme: bool = True
    ) -> Dict[str, Any]:
        """
        Connects to GitHub API, extracts repositories, language statistics, topics,
        and README summaries, then indexes them into ChromaDB.
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LocalAI-Resume-Builder"
        }
        if token and token.strip():
            headers["Authorization"] = f"token {token.strip()}"

        async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
            # 1. Fetch public repositories
            repos_url = f"https://api.github.com/users/{username.strip()}/repos?sort=updated&per_page={max_repos}"
            repo_res = await client.get(repos_url)
            
            if repo_res.status_code == 404:
                raise ValueError(f"GitHub user '{username}' was not found.")
            if repo_res.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded. Provide a personal access token for higher limits.")
            if repo_res.status_code != 200:
                raise ValueError(f"GitHub API returned error {repo_res.status_code}: {repo_res.text}")

            repos = repo_res.json()
            if not isinstance(repos, list):
                raise ValueError("Unexpected response from GitHub API.")

            ingested_repos = []
            skills_detected = set()

            for repo in repos:
                repo_name = repo.get("name", "Unnamed Repo")
                description = repo.get("description") or "No description provided."
                primary_lang = repo.get("language") or "Software"
                topics = repo.get("topics") or []
                html_url = repo.get("html_url", "")
                stars = repo.get("stargazers_count", 0)
                forks = repo.get("forks_count", 0)

                technologies = [primary_lang] + [t for t in topics if t.lower() != primary_lang.lower()]
                if primary_lang and primary_lang != "Software":
                    skills_detected.add(primary_lang)
                for t in topics:
                    skills_detected.add(t)

                highlights = [
                    f"Repository metrics: {stars} GitHub stars, {forks} forks.",
                    f"Core programming language: {primary_lang}."
                ]

                # 2. Optionally fetch README content for rich project detail
                if fetch_readme:
                    try:
                        readme_url = f"https://api.github.com/repos/{username.strip()}/{repo_name}/readme"
                        readme_res = await client.get(readme_url)
                        if readme_res.status_code == 200:
                            readme_data = readme_res.json()
                            content_b64 = readme_data.get("content", "")
                            if content_b64:
                                decoded_readme = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                                # Extract first 300 words of README
                                summary_words = decoded_readme.split()[:120]
                                if summary_words:
                                    readme_snippet = " ".join(summary_words).replace("\n", " ")
                                    highlights.append(f"README Summary: {readme_snippet}")
                    except Exception as e:
                        logger.warning(f"Could not fetch README for {repo_name}: {e}")

                # Ingest project item into ChromaDB
                IngestionService.ingest_project_item(
                    name=repo_name,
                    description=description,
                    highlights=highlights,
                    technologies=technologies,
                    link=html_url
                )

                ingested_repos.append({
                    "name": repo_name,
                    "language": primary_lang,
                    "stars": stars,
                    "url": html_url,
                    "topics": topics
                })

            # Ingest identified languages and topics into skills collection
            if skills_detected:
                IngestionService.ingest_skills(
                    category="GitHub Repositories & Tech Stack",
                    skills_list=list(skills_detected)[:15]
                )

            return {
                "username": username,
                "repos_synced": len(ingested_repos),
                "skills_extracted": len(skills_detected),
                "repositories": ingested_repos
            }

github_connector = GitHubConnector()
