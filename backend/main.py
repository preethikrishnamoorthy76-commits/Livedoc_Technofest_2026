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


class ArchitectureDiffRequest(BaseModel):
    repo_urls: list[str]


class RepoHealthRequest(BaseModel):
    repo_urls: list[str]


class SecurityRiskRequest(BaseModel):
    repo_urls: list[str]


def _normalize_repo_urls(repo_urls: list[str]) -> list[str]:
    if not repo_urls:
        raise ValueError("At least one repository URL must be provided.")

    normalized = []
    seen = set()
    for raw_url in repo_urls:
        if not isinstance(raw_url, str):
            continue
        cleaned = raw_url.strip().replace("?utm_source=chatgpt.com", "").strip('/');
        if not cleaned:
            continue
        if "github.com" not in cleaned.lower():
            continue
        if cleaned.lower().startswith("http://"):
            cleaned = "https://" + cleaned.split("//", 1)[1]
        if cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            normalized.append(cleaned)

    if not normalized:
        raise ValueError("No valid GitHub repository URLs were provided. Use one URL per line.")

    return normalized


<<<<<<< HEAD
async def _get_latest_commit_shas(repo_urls: list[str]) -> dict[str, str | None]:
    results = await asyncio.gather(
        *[github_service.fetch_recent_commits(url, limit=1) for url in repo_urls],
        return_exceptions=True,
    )
    latest_shas = {}
    for repo_url, commits in zip(repo_urls, results):
        if isinstance(commits, Exception) or not commits:
            latest_shas[repo_url] = None
            continue
        latest_shas[repo_url] = commits[0].get("sha") if isinstance(commits[0], dict) else None
    return latest_shas


=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
def _classify_repo_path(path: str) -> str:
    lowered = path.lower()
    if any(token in lowered for token in ["frontend", "ui", "components", "templates", "public"]):
        return "frontend"
    if any(token in lowered for token in ["backend", "api", "server", "routes", "controllers", "services", "middleware", "models"]):
        return "backend"
    if any(token in lowered for token in ["tests", "test", "spec", "e2e"]):
        return "tests"
    if any(token in lowered for token in ["config", "settings", "infra", "deploy", "docker", "kubernetes", "env"]):
        return "config"
    if any(token in lowered for token in ["docs", "readme", "documentation"]):
        return "docs"
    return "other"


def _build_repo_architecture_snapshot(repo_url: str, files: list[dict]) -> dict:
    category_counts: dict[str, int] = {}
    folders: set[str] = set()
    file_names: list[str] = []

    for file in files or []:
        path = str(file.get("path", "")).strip()
        if not path:
            continue
        file_names.append(path)
        cat = _classify_repo_path(path)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if "/" in path:
            folders.add(path.split("/", 1)[0])
        else:
            folders.add(path)

    return {
        "repo": repo_url,
        "total_files": len(file_names),
        "categories": category_counts,
        "top_folders": sorted(folders)[:10],
        "sample_files": file_names[:10],
    }


async def _get_architecture_diff(repo_urls: list[str]) -> dict:
    normalized = _normalize_repo_urls(repo_urls)
    all_repo_files = await asyncio.gather(
        *[github_service.fetch_repo_contents(url) for url in normalized],
        return_exceptions=True,
    )

    repo_snapshots = []
    for repo_url, files in zip(normalized, all_repo_files):
        if isinstance(files, Exception) or not files:
            repo_snapshots.append({
                "repo": repo_url,
                "total_files": 0,
                "categories": {},
                "top_folders": [],
                "sample_files": [],
                "notes": "No supported files were found in this repository.",
            })
            continue
        repo_snapshots.append(_build_repo_architecture_snapshot(repo_url, files))

    if not repo_snapshots:
        raise ValueError("No repository structure could be analyzed.")

<<<<<<< HEAD
    valid_categories = [set(s.get("categories", {}).keys()) for s in repo_snapshots if s.get("categories")]
    common_categories = set.intersection(*valid_categories) if valid_categories else set()
=======
    common_categories = set.intersection(*(set(snapshot.get("categories", {}).keys()) for snapshot in repo_snapshots if snapshot.get("categories")))
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
    baseline = repo_snapshots[0].get("categories", {})
    drift_items = []
    for snapshot in repo_snapshots:
        current = snapshot.get("categories", {})
        missing = sorted(set(baseline.keys()) - set(current.keys()))
        extra = sorted(set(current.keys()) - set(baseline.keys()))
        if missing or extra:
            drift_items.append({
                "repo": snapshot.get("repo"),
                "missing_from_baseline": missing,
                "extra_vs_baseline": extra,
            })

<<<<<<< HEAD
    ai_report = await ai_service.generate_architecture_drift_analysis(repo_snapshots, drift_items)

=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
    return {
        "status": "success",
        "repo_count": len(normalized),
        "common_categories": sorted(common_categories),
        "baseline_repo": normalized[0],
        "snapshots": repo_snapshots,
        "drift": drift_items,
<<<<<<< HEAD
        "ai_report": ai_report,
=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
        "summary": (
            f"Compared {len(normalized)} repositories to detect architecture drift. "
            f"Common structural categories: {', '.join(sorted(common_categories)) if common_categories else 'none'}"
        ),
    }


def _score_repo_health(repo_url: str, file_count: int, commit_count: int, latest_commit_date: str | None) -> dict:
    score = 40

    if file_count > 0:
        score += min(25, file_count * 0.35)
    else:
        score -= 30

    if commit_count >= 20:
        score += 20
    elif commit_count >= 8:
        score += 12
    elif commit_count >= 3:
        score += 6
    elif commit_count == 0:
        score -= 25

    if latest_commit_date:
        try:
            parsed = datetime.fromisoformat(latest_commit_date.replace("Z", "+00:00"))
            age_days = (datetime.utcnow() - parsed.replace(tzinfo=None)).total_seconds() / 86400
            if age_days <= 30:
                score += 20
            elif age_days <= 180:
                score += 10
            else:
                score -= 10
        except Exception:
            pass

    if file_count == 0:
        score -= 15

    score = max(0, min(100, int(round(score))))

    if score >= 80:
        label = "Healthy"
    elif score >= 60:
        label = "Stable"
    elif score >= 40:
        label = "Watchlist"
    else:
        label = "Critical"

    return {
        "repo": repo_url,
        "score": score,
        "label": label,
        "file_count": file_count,
        "commit_count": commit_count,
        "latest_commit_date": latest_commit_date,
        "health_factors": {
            "structure": "good" if file_count > 0 else "weak",
            "activity": "high" if commit_count >= 8 else "medium" if commit_count > 0 else "low",
            "maintenance": "active" if latest_commit_date else "unknown",
        },
    }


async def _get_repo_health(repo_urls: list[str]) -> dict:
    normalized = _normalize_repo_urls(repo_urls)

    all_repo_files = await asyncio.gather(
        *[github_service.fetch_repo_contents(url) for url in normalized],
        return_exceptions=True,
    )
    all_repo_commits = await asyncio.gather(
        *[github_service.fetch_all_commits(url, per_page=50, max_pages=2) for url in normalized],
        return_exceptions=True,
    )

    reports = []
    for repo_url, files, commits in zip(normalized, all_repo_files, all_repo_commits):
        file_count = len(files) if isinstance(files, list) else 0
        commit_count = len(commits) if isinstance(commits, list) else 0
        latest_commit_date = None

        if isinstance(commits, list) and commits:
            for item in commits:
                commit_obj = item.get("commit", {}) if isinstance(item, dict) else {}
                author = commit_obj.get("author") or {}
                date_value = author.get("date") or commit_obj.get("committer", {}).get("date")
                if date_value:
                    latest_commit_date = date_value
                    break

        reports.append(_score_repo_health(repo_url, file_count, commit_count, latest_commit_date))

    avg_score = round(sum(item["score"] for item in reports) / len(reports)) if reports else 0
<<<<<<< HEAD
    ai_report = await ai_service.generate_repo_health_analysis(reports, avg_score)

=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
    return {
        "status": "success",
        "repo_count": len(normalized),
        "overall_score": avg_score,
        "summary": f"Average repository health score across {len(normalized)} repositories: {avg_score}/100.",
<<<<<<< HEAD
        "ai_report": ai_report,
=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
        "reports": reports,
    }


def _score_security_risk(repo_url: str, file_count: int, commit_count: int, latest_commit_date: str | None) -> dict:
    score = 20
    findings = []

    if file_count == 0:
        score += 30
        findings.append("No supported source files found; repository may be empty or inaccessible.")
    elif file_count < 50:
        score += 10
        findings.append("Repository is small and may have limited coverage or maturity.")
    else:
        score -= 10

    if commit_count == 0:
        score += 25
        findings.append("No recent commit activity detected; maintenance signal is weak.")
    elif commit_count < 5:
        score += 12
        findings.append("Low commit activity may indicate stalled maintenance.")
    else:
        score -= 8

    if latest_commit_date:
        try:
            parsed = datetime.fromisoformat(latest_commit_date.replace("Z", "+00:00"))
            age_days = (datetime.utcnow() - parsed.replace(tzinfo=None)).total_seconds() / 86400
            if age_days > 180:
                score += 18
                findings.append("Repository has not been updated recently; risk of stale dependencies or issues.")
            elif age_days > 90:
                score += 8
                findings.append("Maintenance has slowed; monitor for security drift.")
            else:
                score -= 10
        except Exception:
            pass

    if file_count > 2000:
        score -= 8
        findings.append("Large repository size can increase operational complexity and review overhead.")

    score = max(0, min(100, int(round(score))))
    if score >= 75:
        label = "High Risk"
    elif score >= 45:
        label = "Medium Risk"
    else:
        label = "Low Risk"

    return {
        "repo": repo_url,
        "risk_score": score,
        "label": label,
        "file_count": file_count,
        "commit_count": commit_count,
        "latest_commit_date": latest_commit_date,
        "findings": findings or ["No major security-risk indicators detected from repository metadata."],
    }


async def _get_security_risk(repo_urls: list[str]) -> dict:
    normalized = _normalize_repo_urls(repo_urls)

    all_repo_files = await asyncio.gather(
        *[github_service.fetch_repo_contents(url) for url in normalized],
        return_exceptions=True,
    )
    all_repo_commits = await asyncio.gather(
        *[github_service.fetch_all_commits(url, per_page=50, max_pages=2) for url in normalized],
        return_exceptions=True,
    )

    reports = []
    for repo_url, files, commits in zip(normalized, all_repo_files, all_repo_commits):
        file_count = len(files) if isinstance(files, list) else 0
        commit_count = len(commits) if isinstance(commits, list) else 0
        latest_commit_date = None

        if isinstance(commits, list) and commits:
            for item in commits:
                commit_obj = item.get("commit", {}) if isinstance(item, dict) else {}
                author = commit_obj.get("author") or {}
                date_value = author.get("date") or commit_obj.get("committer", {}).get("date")
                if date_value:
                    latest_commit_date = date_value
                    break

        reports.append(_score_security_risk(repo_url, file_count, commit_count, latest_commit_date))

    avg_risk = round(sum(item["risk_score"] for item in reports) / len(reports)) if reports else 0
<<<<<<< HEAD
    ai_report = await ai_service.generate_security_risk_analysis(reports, avg_risk)

=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
    return {
        "status": "success",
        "repo_count": len(normalized),
        "overall_risk_score": avg_risk,
        "summary": f"Average security risk score across {len(normalized)} repositories: {avg_risk}/100.",
<<<<<<< HEAD
        "ai_report": ai_report,
=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
        "reports": reports,
    }

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
<<<<<<< HEAD
        latest_commit_shas = await _get_latest_commit_shas(repo_urls)
=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
        docs_collection = db.get_generated_docs_collection()
        doc_entry = {
            "tenant_id": tenant_id,
            "repo_urls": repo_urls,
            "documentation": documentation,
<<<<<<< HEAD
            "created_at": datetime.utcnow(),
            "latest_commit_shas": latest_commit_shas,
=======
            "created_at": datetime.utcnow()
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
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
    try:
        repo_urls = _normalize_repo_urls(payload.repo_urls)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    try:
        codebase_analysis = []
        all_repo_files = await asyncio.gather(
            *[github_service.fetch_repo_contents(url) for url in repo_urls],
            return_exceptions=True
        )
        for repo_url, files in zip(repo_urls, all_repo_files):
            if isinstance(files, Exception) or not files: continue
<<<<<<< HEAD
            files_to_process = files[:25]
            download_tasks = [github_service.fetch_file_content(f["download_url"]) for f in files_to_process if f.get("download_url")]
            raw_codes = await asyncio.gather(*download_tasks, return_exceptions=True)
            for file, raw_code in zip(files_to_process, raw_codes):
                if isinstance(raw_code, Exception) or not raw_code or not isinstance(raw_code, str):
                    continue
                try:
                    parsed_data = parser_service.parse_file(file["name"], raw_code)
                    parsed_data["source_repo"] = repo_url
                    codebase_analysis.append(parsed_data)
                except Exception as e:
                    pass
=======
            for file in files:
                try:
                    raw_code = await github_service.fetch_file_content(file["download_url"])
                    parsed_data = parser_service.parse_file(file["name"], raw_code)
                    parsed_data["source_repo"] = repo_url
                    codebase_analysis.append(parsed_data)
                except Exception as e: pass
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
        if not codebase_analysis:
            return {"status": "error", "message": "No supported source files could be parsed from the provided repositories."}
            
        repos_context_string = ", ".join(repo_urls)
        documentation = await ai_service.generate_documentation(codebase_analysis, repos_context_string)
<<<<<<< HEAD
        latest_commit_shas = await _get_latest_commit_shas(repo_urls)
        docs_collection = db.get_generated_docs_collection()
        doc_entry = {
            "tenant_id": tenant_id, "repo_urls": repo_urls, "documentation": documentation,
            "created_at": datetime.utcnow(), "latest_commit_shas": latest_commit_shas
=======
        docs_collection = db.get_generated_docs_collection()
        doc_entry = {
            "tenant_id": tenant_id, "repo_urls": repo_urls, "documentation": documentation, "created_at": datetime.utcnow()
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
        }
        await docs_collection.insert_one(doc_entry)
        return {"status": "success", "message": "Documentation generated successfully", "data": {"markdown": documentation}}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/architecture-diff")
async def architecture_diff(payload: ArchitectureDiffRequest, request: Request):
    """Compare multiple repositories and summarize structural drift between them."""
    try:
        result = await _get_architecture_diff(payload.repo_urls)
        return {"status": "success", "data": result}
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(exc)}


@app.post("/repo-health")
async def repo_health(payload: RepoHealthRequest, request: Request):
    """Rate repository health across activity, structure, and maintenance signals."""
    try:
        result = await _get_repo_health(payload.repo_urls)
        return {"status": "success", "data": result}
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(exc)}


@app.post("/security-risk")
async def security_risk(payload: SecurityRiskRequest, request: Request):
    """Estimate repository security risk based on maintenance and structural signals."""
    try:
        result = await _get_security_risk(payload.repo_urls)
        return {"status": "success", "data": result}
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(exc)}


@app.post("/commit-history")
async def get_commit_history(payload: CommitHistoryRequest, request: Request):
    """Real-time blocking endpoint for the UI dashboard."""
    tenant_id = getattr(request.state, "tenant_id", None)
    try:
        repo_urls = _normalize_repo_urls(payload.repo_urls)
    except ValueError as e:
        return {"commit_summary": f"Error: {str(e)}"}
    try:
        all_repo_commits = await asyncio.gather(
            *[github_service.fetch_all_commits(url) for url in repo_urls],
            return_exceptions=True
        )
        formatted_commits_for_ai = []
        commit_history_structured = []
        fetch_errors = []
        for repo_url, commits in zip(repo_urls, all_repo_commits):
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
        repos_context_string = ", ".join(repo_urls)
        summary = await ai_service.summarize_commits(repos_context_string, formatted_commits_for_ai)
        commit_collection = db.get_commit_history_collection()
        commit_entry = {
            "tenant_id": tenant_id, "repo_urls": repo_urls, "commit_summary": summary, "commit_history": commit_history_structured, "created_at": datetime.utcnow()
        }
        await commit_collection.insert_one(commit_entry)
        return {"commit_summary": summary, "commit_history": commit_history_structured}
    except Exception as e:
        return {"commit_summary": f"Server Error: {str(e)}"}


<<<<<<< HEAD
@app.post("/commit-status")
async def get_commit_status(payload: CommitHistoryRequest, request: Request):
    tenant_id = getattr(request.state, "tenant_id", None)
    try:
        repo_urls = _normalize_repo_urls(payload.repo_urls)
        docs_collection = db.get_generated_docs_collection()
        latest_doc = await docs_collection.find_one(
            {"tenant_id": tenant_id, "repo_urls": repo_urls},
            sort=[("created_at", -1)],
        )
        current_shas = await _get_latest_commit_shas(repo_urls)

        if latest_doc is None or "latest_commit_shas" not in latest_doc:
            return {"status": "no_baseline", "message": "Generate documentation once to start tracking commits."}
        baseline_shas = latest_doc.get("latest_commit_shas", {})
        if all(sha is None for sha in baseline_shas.values()) and all(sha is None for sha in current_shas.values()):
            return {"status": "no_commits", "message": "No commits found for the selected repositories."}
        if any(current_shas.get(url) != baseline_shas.get(url) for url in repo_urls):
            return {"status": "new_commit", "message": "A new commit happened after the last document generation."}
        return {"status": "unchanged", "message": "No new commits since the last document generation."}
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


=======
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
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
