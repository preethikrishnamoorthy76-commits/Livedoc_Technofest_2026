import httpx
import os
import base64
import io
import zipfile
from urllib.parse import urlparse

class GitHubService:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_API_KEY")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"

        self.supported_extensions = ['.py', '.js', '.ts', '.html', '.css', '.go', '.java', '.cpp']

    async def _get_json(self, client: httpx.AsyncClient, url: str) -> dict | list:
        response = await client.get(url, headers=self.headers)

        if response.status_code in (401, 403) and "Authorization" in self.headers:
            fallback_headers = dict(self.headers)
            fallback_headers.pop("Authorization", None)
            response = await client.get(url, headers=fallback_headers)

        response.raise_for_status()
        return response.json()

    async def _download_archive(self, client: httpx.AsyncClient, owner: str, repo: str) -> tuple[str, bytes]:
        branch_candidates = ["main", "master", "trunk", "develop"]

        for branch in branch_candidates:
            archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
            response = await client.get(archive_url, follow_redirects=True)
            if response.status_code == 200 and response.content:
                return branch, response.content

        raise ValueError("Unable to download repository archive from GitHub")
            
    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        # Handle https://github.com/owner/repo
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
        raise ValueError("Invalid GitHub URL format. Use https://github.com/owner/repo")

    async def fetch_repo_contents(self, repo_url: str) -> list[dict]:
        owner, repo = self._parse_repo_url(repo_url)

        async with httpx.AsyncClient() as client:
            try:
                repo_url_api = f"https://api.github.com/repos/{owner}/{repo}"
                repo_data = await self._get_json(client, repo_url_api)
                default_branch = repo_data.get("default_branch", "main")

                branch_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{default_branch}"
                branch_data = await self._get_json(client, branch_url)
                tree_sha = (
                    branch_data.get("commit", {})
                    .get("commit", {})
                    .get("tree", {})
                    .get("sha")
                )
                if not tree_sha:
                    raise ValueError("Missing tree sha")

                tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
                tree_data = await self._get_json(client, tree_url)
                tree_items = tree_data.get("tree", []) if isinstance(tree_data, dict) else []

                files = []
                for item in tree_items:
                    if item.get("type") != "blob":
                        continue

                    path = item.get("path", "")
                    ext = os.path.splitext(path)[1]
                    if ext not in self.supported_extensions:
                        continue

                    files.append({
                        "name": os.path.basename(path),
                        "path": path,
                        "download_url": item.get("url"),
                    })

                if files:
                    return files
            except Exception:
                pass

            branch, archive_content = await self._download_archive(client, owner, repo)
            archive = zipfile.ZipFile(io.BytesIO(archive_content))

            files = []
            for member in archive.infolist():
                if member.is_dir():
                    continue

                relative_path = member.filename.split('/', 1)[1] if '/' in member.filename else member.filename
                ext = os.path.splitext(relative_path)[1]
                if ext not in self.supported_extensions:
                    continue

                files.append({
                    "name": os.path.basename(relative_path),
                    "path": relative_path,
                    "download_url": f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{relative_path}",
                })

            return files

    async def fetch_file_content(self, download_url: str) -> str:
        async with httpx.AsyncClient() as client:
            if "raw.githubusercontent.com" in download_url:
                response = await client.get(download_url)
                response.raise_for_status()
                return response.text

            data = await self._get_json(client, download_url)
            content = data.get("content", "")
            encoding = data.get("encoding")

            if encoding == "base64" and content:
                return base64.b64decode(content).decode("utf-8", errors="replace")

            return response.text

    async def fetch_recent_commits(self, repo_url: str, limit: int = 20) -> list[dict]:
        """Fetch recent commits for a repository using the GitHub Commits API.

        Returns the raw commit JSON objects (caller can extract messages, authors, etc.).
        """
        owner, repo = self._parse_repo_url(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page={limit}"

        async with httpx.AsyncClient() as client:
            data = await self._get_json(client, api_url)
            return data if isinstance(data, list) else []

    async def fetch_all_commits(self, repo_url: str, per_page: int = 100, max_pages: int = 10) -> list[dict]:
        """Fetch commit history from the beginning using GitHub's paginated Commits API.

        This walks result pages until there are no more commits or max_pages is reached,
        to avoid unbounded requests on very large repositories.
        """
        owner, repo = self._parse_repo_url(repo_url)

        all_commits: list[dict] = []

        async with httpx.AsyncClient() as client:
            for page in range(1, max_pages + 1):
                api_url = (
                    f"https://api.github.com/repos/{owner}/{repo}/commits"
                    f"?per_page={per_page}&page={page}"
                )
                data = await self._get_json(client, api_url)
                batch = data if isinstance(data, list) else []
                if not batch:
                    break

                all_commits.extend(batch)

                # If we received fewer than per_page items, there are no more pages.
                if len(batch) < per_page:
                    break

        return all_commits
