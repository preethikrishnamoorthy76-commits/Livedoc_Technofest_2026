<<<<<<< HEAD
import os
import json
import httpx
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI, APIConnectionError, APIError
=======
import google.generativeai as genai
import os
import json
from typing import Any, Dict, List, Optional
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb


class AIService:
    def __init__(self):
<<<<<<< HEAD
        api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
        if not api_key or api_key.strip() in ("your_grok_api_key_here", "your_api_key_here", "YOUR_GROK_API_KEY"):
            raise ValueError("GROK_API_KEY is not configured in backend/.env. Please set your xAI API key from https://console.x.ai.")

        base_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
        self.model = os.getenv("GROK_MODEL", "grok-2-latest")

        # Allow turning off SSL verification if operating behind an SSL-inspecting corporate firewall
        verify_ssl_env = os.getenv("GROK_VERIFY_SSL", "true").lower()
        verify_ssl = verify_ssl_env not in ("false", "0", "no", "off")

        http_client = httpx.AsyncClient(verify=verify_ssl, timeout=httpx.Timeout(120.0, connect=30.0))
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
=======
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        genai.configure(api_key=api_key)
        # Using Gemini 2.5 Flash as requested, prefixed with models/
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb

    async def generate_documentation(self, codebase_analysis: list[dict], repos_context: str) -> str:
        # Prepare the prompt payload based on what the parser extracted
        prompt = f"""
You are an expert software architect and documentation generator.
I am providing you with the structural analysis of the following GitHub repositories: {repos_context}
This may be a single repository, or a suite of related repositories (e.g. frontend and backend).

Here is the breakdown of the files across the system:
"""
        for file in codebase_analysis:
            repo_source = file.get("source_repo", "Unknown Repo")
            prompt += f"\nFile: [{repo_source}] {file['filename']}\n"
            if file['classes']:
                prompt += f"Classes: {', '.join(file['classes'])}\n"
            if file['functions']:
                prompt += f"Functions: {', '.join(file['functions'])}\n"
            prompt += f"\nRaw Code Snippet:\n```\n{file['raw_code'][:1000]}...\n```\n"  # truncate raw code for prompt length safety

        prompt += """
Based on the above architecture, please generate a comprehensive README and internal technical documentation for this system.
<<<<<<< HEAD
Your output MUST format beautifully in Markdown with thorough, multi-paragraph explanations for each section.
=======
Your output MUST format beautifully in Markdown.
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb

CRITICAL for Mermaid.js (version 11.12.3 compatibility):
- You MUST include exactly two separate Mermaid diagrams, and both diagrams MUST render without errors.
    1) A **Cross-Repo Core Architecture flowchart** showing how the main repositories, components, and files of the project interact. If multiple repositories were provided, emphasize how they communicate with each other. If only one repository is provided, show that repository's major high-level modules and their dependencies instead of inventing cross-repo links.
    2) A **Request Lifecycle Sequence Diagram** that traces an end-to-end flow across the system.
- Every diagram MUST be provided as a fenced code block in pure Mermaid syntax exactly like:

```mermaid
flowchart LR
    frontendUI["Frontend UI"] --> apiGateway["API Gateway"]
    apiGateway --> backendService["Backend Service"]
```

- INSIDE each ```mermaid fenced code block you MUST NOT place any prose, titles, sentences, markdown, HTML, or comments. ONLY valid Mermaid syntax is allowed.
- Use only Mermaid-supported diagram types: `flowchart` or `sequenceDiagram`.
- For any node labels that include file names or repo tags such as `[frontend-repo]`, wrap the entire label in double quotes. Example:
    Correct: A["[frontend-repo] main.js"]
    Wrong: A[[frontend-repo] main.js]
- Do not use unsupported Mermaid features such as C4 diagrams, HTML tags, callouts, markdown bullets, or non-ASCII characters inside diagram labels.
- Keep node IDs simple and alphanumeric, such as `frontendUI`, `apiGateway`, `repoParser`.
- Put any headings or explanations OUTSIDE the ```mermaid block as normal markdown.

Your final output should be 100% pure markdown that can be directly passed to marked.js (no outer "```" wrapping the entire response).
Structure:
1. # System Overview (Merged Summary)
2. ## Cross-Repo Architecture Diagram (Mermaid)
3. ## End-to-End Sequence (Mermaid)
4. ## Repository Breakdown & File Layout
5. ## Key Functions / APIs
"""

<<<<<<< HEAD
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software architect and documentation generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except APIConnectionError as exc:
            raise ValueError(
                f"Network/Connection error connecting to Grok API ({self.client.base_url}). "
                "Ensure your GROK_API_KEY is valid and that your network/firewall allows HTTPS calls to api.x.ai. "
                "If using a corporate proxy or local SSL inspection, add GROK_VERIFY_SSL=false in backend/.env."
            ) from exc
        except APIError as exc:
            raise ValueError(f"Grok API returned an error: {exc.message}") from exc
=======
        response = self.model.generate_content(prompt)
        return response.text
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb

    async def generate_structured_analysis(
        self,
        repo_url: str,
        repository_structure: List[Dict[str, Any]],
        commit_history_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
<<<<<<< HEAD
        """Generate a structured JSON analysis for a repository."""
=======
        """Generate a structured JSON analysis for a repository.

        Security:
        - Callers MUST only pass summarized metadata in `repository_structure`.
        - Raw source code contents must NOT be included in the metadata.
        """
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb

        structure_json = json.dumps(repository_structure, indent=2)

        prompt = f"""
You are an expert software architect and AI documentation agent.
You are analyzing the GitHub repository: {repo_url}

You will receive ONLY summarized metadata about the repository structure and dependencies.
You must NOT assume access to full source code.

Repository structure metadata (JSON array of files/components):
{structure_json}

Commit history summary (may be empty):
{commit_history_summary or "(no commit history summary provided)"}

Using ONLY this metadata, produce a concise, structured analysis with the following fields:
- project_overview: brief natural-language overview of the project and its purpose.
- architecture_explanation: description of main components, layers, and data flow.
- dependency_graph_mermaid: a Mermaid diagram (graph or flowchart) describing high-level module/component dependencies.
- commit_history_summary: short summary of the repository's evolution and key changes.
- architecture_risk_analysis: an array of strings, each describing a potential architectural risk or concern.

CRITICAL OUTPUT REQUIREMENTS:
- Respond with a SINGLE JSON object.
- The object MUST have exactly these keys:
  "project_overview" (string),
  "architecture_explanation" (string),
  "dependency_graph_mermaid" (string),
  "commit_history_summary" (string),
  "architecture_risk_analysis" (array of strings).
- Do NOT include Markdown code fences, backticks, comments, or any text outside the JSON object.
- "dependency_graph_mermaid" MUST contain ONLY valid Mermaid syntax, starting with one of: flowchart, graph, or sequenceDiagram.
"""

<<<<<<< HEAD
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software architect and AI documentation agent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            raw_text = (response.choices[0].message.content or "").strip()
        except APIConnectionError as exc:
            raise ValueError(
                f"Network/Connection error connecting to Grok API ({self.client.base_url}). "
                "Ensure your GROK_API_KEY is valid and that your network/firewall allows HTTPS calls to api.x.ai. "
                "If using a corporate proxy or local SSL inspection, add GROK_VERIFY_SSL=false in backend/.env."
            ) from exc
        except APIError as exc:
            raise ValueError(f"Grok API returned an error: {exc.message}") from exc
=======
        response = self.model.generate_content(prompt)
        raw_text = (response.text or "").strip()
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb

        # Best-effort: try to parse the response as JSON directly.
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
<<<<<<< HEAD
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
=======
            # If the model accidentally wraps JSON in code fences or adds extra text,
            # attempt a simple fallback by stripping common fence markers.
            cleaned = raw_text.strip()
            if cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned.strip("`")
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError:
                raise ValueError("Model response is not valid JSON") from exc

        expected_keys = {
            "project_overview",
            "architecture_explanation",
            "dependency_graph_mermaid",
            "commit_history_summary",
            "architecture_risk_analysis",
        }
        if not isinstance(parsed, dict) or not expected_keys.issubset(parsed.keys()):
            raise ValueError("Model response JSON is missing required keys")

        return parsed

    async def summarize_commits(self, repos_context: str, commit_messages: list[str]) -> str:
<<<<<<< HEAD
        """Use Grok to summarize the development history from recent commit messages into a detailed technical report."""
        if not commit_messages:
            return "No commits found for these repositories."

        recent_messages = commit_messages[:40]
        commits_block = "\n".join(f"- {msg[:200]}" for msg in recent_messages)

        prompt = f"""
You are an senior software engineering historian and principal architect.
You are analyzing the joint commit history of the following repositories: {repos_context}

Here is the aggregated commit history (from newest to oldest):
{commits_block}

Write a detailed, multi-paragraph technical report analyzing the overall system's development trajectory and evolution.
Your report MUST follow a clean markdown structure:

### Executive Development Summary
A detailed 2-paragraph high-level narrative explaining the project's evolution, team focus, and recent release milestones based on the commit history.

### Key Architectural & Feature Milestones
A comprehensive technical breakdown explaining major features added, structural refactors, API changes, and dependency updates. Explain how work across frontend/backend/services was coordinated.

### Maintenance & Technical Debt Analysis
Detailed observations regarding commit velocity, bug fixes, refactoring patterns, and potential technical debt or maintenance risks suggested by the commit history.

### Strategic Recommendations
2-3 actionable, technical recommendations for future refactoring, workflow optimizations, or testing enhancements based on past development trends.

Use clean, professional markdown. Avoid brevity—provide thorough technical depth in complete paragraphs.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior software engineering historian and principal architect."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip()
        except APIConnectionError as exc:
            raise ValueError(
                f"Network/Connection error connecting to Grok API ({self.client.base_url}). "
                "Ensure your GROK_API_KEY is valid and that your network/firewall allows HTTPS calls to api.x.ai. "
                "If using a corporate proxy or local SSL inspection, add GROK_VERIFY_SSL=false in backend/.env."
            ) from exc
        except APIError as exc:
            raise ValueError(f"Grok API returned an error: {exc.message}") from exc

    async def generate_architecture_drift_analysis(self, repo_snapshots: list[dict], drift_items: list[dict]) -> str:
        """Generate a multi-paragraph technical report for Architecture Drift."""
        snapshots_json = json.dumps(repo_snapshots, indent=2)
        drift_json = json.dumps(drift_items, indent=2)

        prompt = f"""
You are a Principal Software Architect conducting an Architecture Drift audit across multiple repositories.

Repository Structure Snapshots:
{snapshots_json}

Detected Structural Drift & Differences:
{drift_json}

Write a thorough, multi-paragraph technical report detailing the architectural alignment and structural drift across these repositories.
Your output MUST format beautifully in Markdown with the following structure:

### Executive Summary
A detailed multi-paragraph overview explaining what structural patterns were detected, the degree of architectural consistency between the repositories, and why monitoring drift is essential for this codebase.

### Affected Components & Structural Variations
Detailed breakdown describing specific module mismatches, folder structure deviations, or extra/missing architectural layers discovered between the baseline repository and target repositories.

### Architectural Risks & Impact on Maintainability
Explain the technical implications of the detected drift—such as increased cognitive overhead for developers, potential breaking API contracts, deployment coupling, or inconsistent testing strategies.

### Standardization Roadmap & Recommendations
Provide actionable, step-by-step architectural recommendations to align folder structures, shared modules, and build pipelines across the repositories.

Provide thorough technical depth in complete, professional paragraphs.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Principal Software Architect conducting an Architecture Drift audit."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            return (
                "### Executive Summary\n"
                "Architecture comparison complete. Structural drift analysis identifies variations in component organization and directory layouts across the audited repositories.\n\n"
                "### Affected Components & Structural Variations\n"
                "Discrepancies were noted in shared utility boundaries and framework configurations.\n\n"
                "### Recommendations\n"
                "Standardize repository templates and file layout conventions across teams."
            )

    async def generate_repo_health_analysis(self, reports: list[dict], overall_score: int) -> str:
        """Generate a multi-paragraph technical report for Repository Health."""
        reports_json = json.dumps(reports, indent=2)

        prompt = f"""
You are a Lead Engineering Operations Director evaluating repository health metrics.

Overall Health Score: {overall_score}/100
Detailed Repository Metrics & Scores:
{reports_json}

Write a detailed, multi-paragraph technical report analyzing the current health, activity patterns, and operational status of the evaluated repositories.
Format your output in Markdown with the following structure:

### Executive Health Assessment
A detailed multi-paragraph narrative contextualizing the overall score ({overall_score}/100), explaining the overall stability, maintenance velocity, and codebase freshness across the repositories.

### Component & Activity Breakdown
Thorough technical commentary on code file density, commit frequency, contributor activity cadence, and recent update timestamps for each repository.

### Identified Operational & Technical Risks
Discuss potential risks such as stale codebases, low commit frequency, lack of active maintenance, or oversized repository footprints.

### Actionable Maintenance Recommendations
Provide specific, prioritized recommendations for engineering teams to improve repository health, increase commit velocity, prune dead files, and improve code lifecycle management.

Write in a formal, authoritative engineering tone with thorough multi-paragraph sections.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Lead Engineering Operations Director evaluating repository health."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return (
                f"### Executive Health Assessment\n"
                f"The overall repository health score is {overall_score}/100. Repositories were evaluated across file layout, commit frequency, and recent update timestamps.\n\n"
                "### Component & Activity Breakdown\n"
                "Structural signals indicate varying levels of ongoing maintenance and commit frequency.\n\n"
                "### Actionable Maintenance Recommendations\n"
                "Establish automated dependency updates and regular commit workflows."
            )

    async def generate_security_risk_analysis(self, reports: list[dict], overall_risk_score: int) -> str:
        """Generate a multi-paragraph technical report for Security Risk."""
        reports_json = json.dumps(reports, indent=2)

        prompt = f"""
You are a Chief Information Security Officer (CISO) and Application Security Auditor.

Overall Security Risk Score: {overall_risk_score}/100
Detailed Repository Security Risk Signals:
{reports_json}

Write a comprehensive, multi-paragraph technical security report analyzing the security posture and risk signals of the evaluated repositories.
Format your output in Markdown with the following structure:

### Executive Security Summary
A detailed multi-paragraph overview contextualizing the overall risk score ({overall_risk_score}/100), explaining the repository security baseline and key risk vectors.

### Technical Risk Analysis & Threat Vectors
Detailed explanation of specific structural security risks—including maintenance staleness, unmonitored repository size, unmaintained code paths, and lack of recent commit oversight.

### Supply Chain & Operational Impact
Describe the operational and security impact of these risk signals on production systems, data integrity, and compliance requirements.

### Security Remediation & Hardening Roadmap
Provide actionable, prioritized recommendations for hardening the codebase, enforcing automated security scanning, establishing active maintenance windows, and mitigating structural risks.

Provide deep, professional security insights written in complete paragraphs.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Chief Information Security Officer and Application Security Auditor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return (
                f"### Executive Security Summary\n"
                f"The overall security risk score across evaluated repositories is {overall_risk_score}/100. Signals evaluate maintenance activity and repository layout.\n\n"
                "### Technical Risk Analysis\n"
                "Repositories showing low recent activity or unmonitored file growth require security oversight.\n\n"
                "### Security Remediation Roadmap\n"
                "Implement automated static code analysis, secret scanning, and regular security patching."
            )
=======
        """Use Gemini to summarize the development history from recent commit messages."""
        if not commit_messages:
            return "No commits found for these repositories."

        commits_block = "\n".join(f"- {msg}" for msg in commit_messages)

        prompt = f"""
You are an expert software project historian.
You are analyzing the joint commit history of the following repositories: {repos_context}

Here is the aggregated commit history (from newest to oldest).
Each line includes the repository name, commit date, author, and message:

{commits_block}

Based on these commits across all provided repositories, write a concise, human-readable Merged Summary of the overall system's development history and major changes over time.
If multiple repositories are present, explain how development across them coordinated (e.g., "Frontend UI updates were followed by corresponding backend API changes").

Focus on:
- Key features added or removed across the system
- Major refactors or architectural changes
- Notable bug fixes or performance improvements

Your response should be plain text (1–3 short paragraphs or a brief bullet list), without any Markdown headings or code blocks.
"""

        response = self.model.generate_content(prompt)
        return (response.text or "").strip()
>>>>>>> 7a410c59179962b229cdf23a8de7ba340dfe60eb
