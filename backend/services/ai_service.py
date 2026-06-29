import google.generativeai as genai
import os
import json
from typing import Any, Dict, List, Optional


class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        genai.configure(api_key=api_key)
        # Using Gemini 2.5 Flash as requested, prefixed with models/
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')

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
Your output MUST format beautifully in Markdown.

CRITICAL for Mermaid.js (version 11.12.3 compatibility):
- You MUST include **two** separate Mermaid diagrams:
    1) A **Cross-Repo Core Architecture flowchart** showing how the main repositories, components, and files of the project interact. If multiple repositories were provided, emphasize how they communicate with each other.
    2) A **Request Lifecycle Sequence Diagram** that traces an end-to-end flow across the system.
- Every diagram MUST be provided as a fenced code block in pure Mermaid syntax, like this:

```mermaid
flowchart LR
    ...
```

- INSIDE the ```mermaid fenced code block you MUST NOT place any prose, titles, sentences, or markdown – ONLY valid Mermaid syntax.
- CRITICAL for Node text: Since file names now include bracketed repository names like [frontend-repo], you MUST wrap all node display text in double quotes to prevent syntax errors. Example:
    Correct: nodeID["[frontend-repo] main.js"]
    Wrong: nodeID[[frontend-repo] main.js]
- Put any headings or explanations OUTSIDE the ```mermaid block as normal markdown.

Your final output should be 100% pure markdown that can be directly passed to marked.js (no outer "```" wrapping the entire response).
Structure:
1. # System Overview (Merged Summary)
2. ## Cross-Repo Architecture Diagram (Mermaid)
3. ## End-to-End Sequence (Mermaid)
4. ## Repository Breakdown & File Layout
5. ## Key Functions / APIs
"""

        response = self.model.generate_content(prompt)
        return response.text

    async def generate_structured_analysis(
        self,
        repo_url: str,
        repository_structure: List[Dict[str, Any]],
        commit_history_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a structured JSON analysis for a repository.

        Security:
        - Callers MUST only pass summarized metadata in `repository_structure`.
        - Raw source code contents must NOT be included in the metadata.
        """

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

        response = self.model.generate_content(prompt)
        raw_text = (response.text or "").strip()

        # Best-effort: try to parse the response as JSON directly.
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            # If the model accidentally wraps JSON in code fences or adds extra text,
            # attempt a simple fallback by stripping common fence markers.
            cleaned = raw_text.strip()
            if cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned.strip("`")
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
