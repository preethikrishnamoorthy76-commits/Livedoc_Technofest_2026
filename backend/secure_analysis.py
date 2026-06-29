from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from db import get_repositories_collection, get_analysis_results_collection
from services.github_service import GitHubService


router = APIRouter()

github_service = GitHubService()


class SecureAnalyzeRequest(BaseModel):
    repo_url: HttpUrl


class SecureAnalysisResponse(BaseModel):
    id: str
    tenant_id: str
    repo_id: str
    project_overview: Optional[str]
    architecture_flow: Optional[str]
    dependency_graph: Optional[str]
    commit_summary: Optional[str]
    risk_analysis: List[str]
    created_at: datetime


@router.post("/secure-analyze", response_model=SecureAnalysisResponse)
async def secure_analyze_repository(payload: SecureAnalyzeRequest, request: Request):
    """Analyze a GitHub repository securely for the authenticated tenant.

    - Uses GitHub REST API (via httpx) with a personal access token.
    - Fetches repository structure and commit history.
    - Does not persist raw source code; only stores summarized analysis in MongoDB.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    repo_url_str = str(payload.repo_url)

    # Derive basic metadata from the URL.
    try:
        owner, repo_name = github_service._parse_repo_url(repo_url_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Fetch repository structure (list of files) without storing raw contents.
    files = await github_service.fetch_repo_contents(repo_url_str)
    file_count = len(files)

    # Fetch commit history (limited pages) and build a high-level summary.
    commits = await github_service.fetch_all_commits(repo_url_str, per_page=50, max_pages=1)
    total_commits = len(commits)

    latest_commit_message: Optional[str] = None
    latest_commit_date: Optional[str] = None
    if commits:
        latest = commits[0]
        commit_obj = latest.get("commit", {})
        latest_commit_message = str(commit_obj.get("message", "")).strip() or None
        author_info = commit_obj.get("author") or {}
        latest_commit_date = author_info.get("date") or commit_obj.get("committer", {}).get("date")

    commit_summary_lines: List[str] = [
        f"Total commits analyzed: {total_commits}",
    ]
    if latest_commit_date or latest_commit_message:
        commit_summary_lines.append("Latest commit:")
        if latest_commit_date:
            commit_summary_lines.append(f"- Date: {latest_commit_date}")
        if latest_commit_message:
            commit_summary_lines.append(f"- Message: {latest_commit_message}")

    commit_summary = "\n".join(commit_summary_lines)

    # Simple heuristic-based risk analysis without storing raw code.
    risks: List[str] = []
    if total_commits == 0:
        risks.append("Repository has no commit history (empty or inaccessible).")
    elif total_commits < 5:
        risks.append("Very low commit activity (fewer than 5 commits).")
    if file_count == 0:
        risks.append("No supported source files found at repository root.")

    # Minimal project overview and architecture description without persisting code.
    project_overview = (
        f"Repository {owner}/{repo_name} analyzed for tenant {tenant_id}. "
        f"Found {file_count} tracked source files and {total_commits} commits (sampled)."
    )

    architecture_flow = (
        "High-level architecture inferred from repository root only. "
        "Detailed code contents are processed transiently and not stored."
    )

    # Very simple Mermaid-style dependency graph relating repo, files, and commits.
    dependency_graph = (
        "graph LR\n"
        f"  repo[{owner}/{repo_name}] --> files[Files: {file_count}]\n"
        f"  repo --> commits[Commits: {total_commits}]\n"
    )

    # Ensure repository metadata exists for this tenant and URL, and get repo_id.
    repositories = get_repositories_collection()

    existing_repo = await repositories.find_one({
        "tenant_id": tenant_id,
        "repo_url": repo_url_str,
    })

    if existing_repo is None:
        repo_doc = {
            "tenant_id": tenant_id,
            "repo_url": repo_url_str,
            "owner": owner,
            "repo_name": repo_name,
            "created_at": datetime.utcnow(),
        }
        insert_result = await repositories.insert_one(repo_doc)
        repo_id = str(insert_result.inserted_id)
    else:
        repo_id = str(existing_repo["_id"])

    analysis_collection = get_analysis_results_collection()

    analysis_doc = {
        "tenant_id": tenant_id,
        "repo_id": repo_id,
        "project_overview": project_overview,
        "architecture_flow": architecture_flow,
        "dependency_graph": dependency_graph,
        "commit_summary": commit_summary,
        "risk_analysis": risks,
        "created_at": datetime.utcnow(),
    }

    analysis_result = await analysis_collection.insert_one(analysis_doc)

    return SecureAnalysisResponse(
        id=str(analysis_result.inserted_id),
        tenant_id=tenant_id,
        repo_id=repo_id,
        project_overview=project_overview,
        architecture_flow=architecture_flow,
        dependency_graph=dependency_graph,
        commit_summary=commit_summary,
        risk_analysis=risks,
        created_at=analysis_doc["created_at"],
    )
