from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from db import get_analysis_results_collection


router = APIRouter()


class AnalysisResult(BaseModel):
    id: str = Field(alias="_id")
    tenant_id: str
    repo_id: str
    project_overview: Optional[str] = None
    architecture_flow: Optional[str] = None
    dependency_graph: Optional[str] = None
    commit_summary: Optional[str] = None
    risk_analysis: List[str] = []
    created_at: datetime

    class Config:
        populate_by_name = True


@router.get("/analysis/{repo_id}", response_model=List[AnalysisResult])
async def get_analysis_for_repo(repo_id: str, request: Request):
    """Return all analysis results for the given repo_id, scoped to the current tenant."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    collection = get_analysis_results_collection()

    cursor = collection.find({"tenant_id": tenant_id, "repo_id": repo_id})
    results = []
    async for doc in cursor:
        # Ensure _id is converted to string for the response model
        doc["_id"] = str(doc["_id"])
        results.append(doc)

    # Even if empty, this only returns documents for the caller's tenant,
    # satisfying "Users can only retrieve analysis results for their tenant".
    return results
