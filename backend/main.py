from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
from dotenv import load_dotenv
import os

from config import MONGODB_URI, MONGODB_DB
import db

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB on startup
    try:
        print(f"Attempting to connect to MongoDB at {MONGODB_URI}...")
        # We explicitly initialize the db client here to test the connection
        client = db.get_client()
        # Ping the database to ensure connection is alive
        await client.admin.command('ping')
        print(f"Successfully connected to MongoDB Database: {MONGODB_DB}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("Please ensure your MongoDB server is running (e.g. through Docker or local installation).")
    
    yield
    
    # Cleanup on shutdown
    if db._client is not None:
        db._client.close()
        print("MongoDB connection closed.")

app = FastAPI(
    title="LiveDoc AI API", 
    description="API for LiveDoc AI documentation generation tool",
    lifespan=lifespan
)

# Configure CORS so our local frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from middleware import TenantMiddleware
from auth import router as auth_router
from repositories import router as repositories_router
from analysis_results import router as analysis_results_router
from secure_analysis import router as secure_analysis_router

app.add_middleware(TenantMiddleware)

# Register all routers
app.include_router(auth_router)
app.include_router(repositories_router)
app.include_router(analysis_results_router)
app.include_router(secure_analysis_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to LiveDoc AI API"}

from services.github_service import GitHubService
from services.parser_service import ParserService
from services.ai_service import AIService
from pydantic import BaseModel
import asyncio
import os
import httpx

github_service = GitHubService()
parser_service = ParserService()
ai_service = AIService()

class AnalyzeRequest(BaseModel):
    repo_urls: list[str]


class TriggerUpdateRequest(BaseModel):
    repo_urls: list[str]
    api_key: str


class CommitHistoryRequest(BaseModel):
    repo_urls: list[str]

# Helper functions for the core analysis logic so they can be reused by background tasks
from fastapi import BackgroundTasks, HTTPException

async def _analyze_and_store(repo_urls: list[str], tenant_id: str = None):
    try:
        codebase_analysis = []
        all_repo_files = await asyncio.gather(
            *[github_service.fetch_repo_contents(url) for url in repo_urls],
            return_exceptions=True
        )
        for repo_url, files in zip(repo_urls, all_repo_files):
            if isinstance(files, Exception) or not files: continue
            for file in files:
                try:
                    raw_code = await github_service.fetch_file_content(file["download_url"])
                    parsed_data = parser_service.parse_file(file["name"], raw_code)
                    parsed_data["source_repo"] = repo_url
                    codebase_analysis.append(parsed_data)
                except Exception as e:
                    pass
        if not codebase_analysis: return
        repos_context_string = ", ".join(repo_urls)
        documentation = await ai_service.generate_documentation(codebase_analysis, repos_context_string)
        docs_collection = db.get_generated_docs_collection()
        doc_entry = {
            "tenant_id": tenant_id,
            "repo_urls": repo_urls,
            "documentation": documentation,
            "created_at": datetime.utcnow()
        }
        await docs_collection.insert_one(doc_entry)
    except Exception as e:
        import traceback
        traceback.print_exc()

async def _fetch_and_store_history(repo_urls: list[str], tenant_id: str = None):
    try:
        all_repo_commits = await asyncio.gather(
            *[github_service.fetch_all_commits(url) for url in repo_urls],
            return_exceptions=True
        )
        formatted_commits_for_ai = []
        commit_history_structured = []
        for repo_url, commits in zip(repo_urls, all_repo_commits):
            if isinstance(commits, Exception) or not commits: continue
            repo_name = repo_url.rstrip('/').split('/')[-1]
            for item in commits:
                try:
                    commit = item.get("commit", {})
                    message = commit.get("message")
                    if not isinstance(message, str) or not message.strip(): continue
                    author_info = commit.get("author") or {}
                    author_name = author_info.get("name") or (item.get("author") or {}).get("login") or "Unknown"
                    date_str = author_info.get("date") or commit.get("committer", {}).get("date") or "Unknown date"
                    message_clean = message.strip()
                    formatted_commits_for_ai.append(f"[{repo_name}] {date_str} - {author_name}: {message_clean}")
                    commit_history_structured.append({
                        "repo": repo_name, "date": date_str, "author": author_name, "message": message_clean
                    })
                except (KeyError, TypeError): continue

        commit_history_structured.sort(key=lambda x: x.get("date", ""), reverse=True)
        repos_context_string = ", ".join(repo_urls)
        summary = await ai_service.summarize_commits(repos_context_string, formatted_commits_for_ai)
        commit_collection = db.get_commit_history_collection()
        commit_entry = {
            "tenant_id": tenant_id,
            "repo_urls": repo_urls,
            "commit_summary": summary,
            "commit_history": commit_history_structured,
            "created_at": datetime.utcnow()
        }
        await commit_collection.insert_one(commit_entry)
    except Exception as e:
        import traceback
        traceback.print_exc()


@app.post("/analyze")
async def analyze_repo(payload: AnalyzeRequest, request: Request):
    """Real-time blocking endpoint for the UI dashboard."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not payload.repo_urls:
        return {"status": "error", "message": "At least one repository URL must be provided."}
    
    # We call the helper but wait for it to finish because the UI needs the response instantly
    try:
        # We rewrite the helper logic here specifically so we can return the exact data map to the UI.
        codebase_analysis = []
        all_repo_files = await asyncio.gather(
            *[github_service.fetch_repo_contents(url) for url in payload.repo_urls],
            return_exceptions=True
        )
        for repo_url, files in zip(payload.repo_urls, all_repo_files):
            if isinstance(files, Exception) or not files: continue
            for file in files:
                try:
                    raw_code = await github_service.fetch_file_content(file["download_url"])
                    parsed_data = parser_service.parse_file(file["name"], raw_code)
                    parsed_data["source_repo"] = repo_url
                    codebase_analysis.append(parsed_data)
                except Exception as e: pass
        if not codebase_analysis:
            return {"status": "error", "message": "No supported source files could be parsed."}
            
        repos_context_string = ", ".join(payload.repo_urls)
        documentation = await ai_service.generate_documentation(codebase_analysis, repos_context_string)
        docs_collection = db.get_generated_docs_collection()
        doc_entry = {
            "tenant_id": tenant_id, "repo_urls": payload.repo_urls, "documentation": documentation, "created_at": datetime.utcnow()
        }
        await docs_collection.insert_one(doc_entry)
        return {"status": "success", "message": "Documentation generated successfully", "data": {"markdown": documentation}}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/commit-history")
async def get_commit_history(payload: CommitHistoryRequest, request: Request):
    """Real-time blocking endpoint for the UI dashboard."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not payload.repo_urls:
        return {"commit_summary": "Error: At least one repository URL must be provided."}
    try:
        all_repo_commits = await asyncio.gather(
            *[github_service.fetch_all_commits(url) for url in payload.repo_urls],
            return_exceptions=True
        )
        formatted_commits_for_ai = []
        commit_history_structured = []
        fetch_errors = []
        for repo_url, commits in zip(payload.repo_urls, all_repo_commits):
            if isinstance(commits, Exception):
                fetch_errors.append(f"{repo_url}: {str(commits)}")
                continue
            if not commits:
                continue
            repo_name = repo_url.rstrip('/').split('/')[-1]
            for item in commits:
                try:
                    commit = item.get("commit", {})
                    message = commit.get("message")
                    if not isinstance(message, str) or not message.strip(): continue
                    author_info = commit.get("author") or {}
                    author_name = author_info.get("name") or (item.get("author") or {}).get("login") or "Unknown"
                    date_str = author_info.get("date") or commit.get("committer", {}).get("date") or "Unknown date"
                    message_clean = message.strip()
                    formatted_commits_for_ai.append(f"[{repo_name}] {date_str} - {author_name}: {message_clean}")
                    commit_history_structured.append({"repo": repo_name, "date": date_str, "author": author_name, "message": message_clean})
                except (KeyError, TypeError): continue

        if not commit_history_structured and fetch_errors:
            return {
                "commit_summary": "Unable to fetch commits from GitHub. Check GITHUB_API_KEY validity or GitHub API rate limits.",
                "commit_history": [],
                "errors": fetch_errors,
            }

        commit_history_structured.sort(key=lambda x: x.get("date", ""), reverse=True)
        repos_context_string = ", ".join(payload.repo_urls)
        summary = await ai_service.summarize_commits(repos_context_string, formatted_commits_for_ai)
        commit_collection = db.get_commit_history_collection()
        commit_entry = {
            "tenant_id": tenant_id, "repo_urls": payload.repo_urls, "commit_summary": summary, "commit_history": commit_history_structured, "created_at": datetime.utcnow()
        }
        await commit_collection.insert_one(commit_entry)
        return {"commit_summary": summary, "commit_history": commit_history_structured}
    except Exception as e:
        return {"commit_summary": f"Server Error: {str(e)}"}


@app.post("/api/trigger-update")
async def trigger_update(payload: TriggerUpdateRequest, background_tasks: BackgroundTasks):
    """
    Called by GitHub Actions to silently trigger a background re-analysis of the repositories.
    It returns a 202 Accepted immediately so the GitHub Action completes successfully,
    while pushing the heavy AI operations to the background.
    """
    # Simple security mechanism
    EXPECTED_API_KEY = os.getenv("GITHUB_ACTION_SECRET", "super-secret-default-key")
    if payload.api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key provided by GitHub Action.")

    if not payload.repo_urls:
         raise HTTPException(status_code=400, detail="Repository URLs required.")

    # We do not have a tenant_id from GitHub Actions (unless passed in payload), 
    # so we assign it to a "system" scope or null.
    tenant_id = "agent_automated_workflow"

    print(f"⚡ GitHub Action triggered background update for: {payload.repo_urls}")

    # Add both the Code Analysis and Commit History generation to the background processing queue
    background_tasks.add_task(_analyze_and_store, payload.repo_urls, tenant_id)
    background_tasks.add_task(_fetch_and_store_history, payload.repo_urls, tenant_id)

    return {
        "status": "success", 
        "message": "Background analysis successfully queued. LiveDoc will be updated shortly."
    }

# To run the app use: uvicorn main:app --reload
