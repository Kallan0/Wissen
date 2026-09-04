import sys
import argparse
import requests
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from rag.ingestion import IngestionService
from rag.vectorstore import vector_store

def ingest_github_user(username: str, token: str = None):
    print(f"Fetching public repositories for GitHub user: {username}...")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching repos from GitHub: {response.status_code} - {response.text}")
        return

    repos = response.json()
    print(f"Found {len(repos)} repositories.")

    ingested_count = 0
    for repo in repos:
        name = repo.get("name", "")
        desc = repo.get("description") or "No description provided."
        lang = repo.get("language") or "Code"
        topics = repo.get("topics") or []
        html_url = repo.get("html_url", "")
        technologies = [lang] + topics

        highlights = [
            f"Stars: {repo.get('stargazers_count', 0)}, Forks: {repo.get('forks_count', 0)}",
            f"Primary Language: {lang}",
            f"Repository Description: {desc}"
        ]

        # Ingest as project
        IngestionService.ingest_project_item(
            name=name,
            description=desc,
            highlights=highlights,
            technologies=technologies,
            link=html_url
        )
        ingested_count += 1

    print(f"Successfully ingested {ingested_count} repositories from GitHub into ChromaDB.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest GitHub profile repositories into Resume Knowledge Base")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--token", help="Optional GitHub personal access token", default=None)
    args = parser.parse_args()
    ingest_github_user(args.username, args.token)
