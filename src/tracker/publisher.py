"""GitHub Discussions publisher for AI Regulation Tracker."""

from __future__ import annotations

import httpx
from datetime import date


def get_issue_number(token: str, repo: str = "brianpelow/ai-regulation-tracker") -> int:
    """Get next issue number by counting existing discussions."""
    try:
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 1) { totalCount }
          }
        }
        """
        owner, name = repo.split("/")
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query, "variables": {"owner": owner, "repo": name}},
            )
            if r.status_code == 200:
                data = r.json()
                count = data.get("data", {}).get("repository", {}).get("discussions", {}).get("totalCount", 0)
                return count + 1
    except Exception as e:
        print(f"[publisher] get_issue_number failed: {e}")
    return 1


def get_repo_id_and_category(token: str, repo: str = "brianpelow/ai-regulation-tracker") -> tuple[str | None, str | None]:
    """Get repo node ID and announcement category ID."""
    try:
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            id
            discussionCategories(first: 10) {
              nodes { id name slug }
            }
          }
        }
        """
        owner, name = repo.split("/")
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query, "variables": {"owner": owner, "repo": name}},
            )
            if r.status_code == 200:
                data = r.json().get("data", {}).get("repository", {})
                repo_id = data.get("id")
                categories = data.get("discussionCategories", {}).get("nodes", [])
                category_id = None
                for cat in categories:
                    if cat.get("slug") in ("announcements", "general"):
                        category_id = cat.get("id")
                        break
                return repo_id, category_id
    except Exception as e:
        print(f"[publisher] get_repo_id_and_category failed: {e}")
    return None, None


def publish(digest: str, issue_number: int, token: str, repo: str = "brianpelow/ai-regulation-tracker") -> bool:
    """Publish digest as a GitHub Discussion."""
    today = date.today()
    title = f"AI Regulation Tracker -- {today.strftime('%B %d, %Y')} -- Issue #{issue_number}"

    repo_id, category_id = get_repo_id_and_category(token, repo)
    if not repo_id or not category_id:
        print("[publisher] Could not get repo or category ID")
        return False

    try:
        mutation = """
        mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
          createDiscussion(input: {
            repositoryId: $repoId
            categoryId: $categoryId
            title: $title
            body: $body
          }) {
            discussion { url }
          }
        }
        """
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "query": mutation,
                    "variables": {
                        "repoId": repo_id,
                        "categoryId": category_id,
                        "title": title,
                        "body": digest,
                    }
                },
            )
            if r.status_code == 200:
                data = r.json()
                if "errors" not in data:
                    url = data["data"]["createDiscussion"]["discussion"]["url"]
                    print(f"[publisher] Published: {url}")
                    return True
                else:
                    print(f"[publisher] GraphQL errors: {data['errors']}")
    except Exception as e:
        print(f"[publisher] publish failed: {e}")
    return False