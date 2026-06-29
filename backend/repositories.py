from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from db import get_repositories_collection
from services.github_service import GitHubService


router = APIRouter()

github_service = GitHubService()


class AnalyzeRepoRequest(BaseModel):
    repo_url: HttpUrl


@router.post("/analyze-repo")
async def analyze_repo_for_tenant(payload: AnalyzeRepoRequest, request: Request):
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Parse owner and repo_name from the URL using the existing GitHubService logic
    try:
        owner, repo_name = github_service._parse_repo_url(str(payload.repo_url))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    repositories = get_repositories_collection()

    doc = {
        "tenant_id": tenant_id,
        "repo_url": str(payload.repo_url),
        "owner": owner,
        "repo_name": repo_name,
        "created_at": datetime.utcnow(),
    }

    result = await repositories.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "tenant_id": tenant_id,
        "repo_url": doc["repo_url"],
        "owner": owner,
        "repo_name": repo_name,
        "created_at": doc["created_at"].isoformat() + "Z",
    }
