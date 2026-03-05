"""
PR Code Review Service for OpenPango GitHub App

Fetches PR diffs and dispatches review tasks to OpenClaw agents
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from github import Github  # PyGithub library

logger = logging.getLogger(__name__)


class PRReviewer:
    """
    Fetch and analyze pull request changes
    
    Workflow:
    1. Fetch PR diff from GitHub API
    2. Parse changed files and hunks
    3. Generate review context
    4. Dispatch to OpenClaw Coder agent
    """
    
    def __init__(self, github_token: str, openclaw_api_url: str):
        """
        Initialize PR reviewer
        
        Args:
            github_token: GitHub API token
            openclaw_api_url: OpenClaw API endpoint
        """
        self.github = Github(github_token)
        self.openclaw_api_url = openclaw_api_url
        self.client = httpx.AsyncClient()
    
    async def fetch_pr_diff(self, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch PR diff from GitHub
        
        Args:
            repo_full_name: Repository name (e.g., "owner/repo")
            pr_number: Pull request number
        
        Returns:
            Dict with files and their changes
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            # Get changed files
            files = pr.get_files()
            
            changes = []
            for file in files:
                changes.append({
                    "filename": file.filename,
                    "status": file.status,  # added, modified, removed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch,  # Diff patch
                    "raw_url": file.raw_url
                })
            
            return {
                "pr_number": pr_number,
                "pr_title": pr.title,
                "pr_body": pr.body,
                "author": pr.user.login,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "files": changes,
                "total_additions": pr.additions,
                "total_deletions": pr.deletions
            }
        
        except Exception as e:
            logger.error(f"Error fetching PR diff: {e}", exc_info=True)
            raise
    
    async def dispatch_code_review(
        self,
        repo_full_name: str,
        pr_number: int,
        review_depth: str = "standard"
    ) -> Dict[str, str]:
        """
        Dispatch code review task to OpenClaw agent
        
        Args:
            repo_full_name: Repository name
            pr_number: Pull request number
            review_depth: "quick", "standard", or "deep"
        
        Returns:
            Task dispatch result
        """
        # Fetch PR diff
        pr_data = await self.fetch_pr_diff(repo_full_name, pr_number)
        
        # Generate review prompt
        review_prompt = self._generate_review_prompt(pr_data, review_depth)
        
        # Dispatch to OpenClaw
        task_payload = {
            "task_type": "code_review",
            "repository": repo_full_name,
            "pr_number": pr_number,
            "prompt": review_prompt,
            "context": {
                "files": pr_data["files"],
                "author": pr_data["author"],
                "title": pr_data["pr_title"]
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.openclaw_api_url}/api/tasks/dispatch",
                json=task_payload,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Code review task dispatched: {result.get('task_id')}")
            
            return {
                "status": "dispatched",
                "task_id": result.get("task_id"),
                "pr_number": pr_number
            }
        
        except Exception as e:
            logger.error(f"Error dispatching review task: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_review_prompt(
        self,
        pr_data: Dict[str, Any],
        depth: str
    ) -> str:
        """
        Generate review prompt for OpenClaw agent
        
        Args:
            pr_data: PR information and changes
            depth: Review depth level
        
        Returns:
            Formatted review prompt
        """
        depth_instructions = {
            "quick": "Focus on critical bugs and security issues only.",
            "standard": "Review for bugs, security, performance, and code quality.",
            "deep": "Comprehensive review including architecture, patterns, and documentation."
        }
        
        files_summary = "\n".join([
            f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in pr_data["files"]
        ])
        
        prompt = f"""
You are reviewing Pull Request #{pr_data['pr_number']} in {pr_data.get('repository', 'the repository')}.

**PR Title:** {pr_data['pr_title']}
**Author:** {pr_data['author']}
**Branch:** {pr_data['head_branch']} → {pr_data['base_branch']}

**Files Changed:**
{files_summary}

**Review Instructions:**
{depth_instructions.get(depth, depth_instructions['standard'])}

Please analyze the changes and provide:
1. Summary of changes
2. Potential issues or bugs
3. Security concerns
4. Performance considerations
5. Suggestions for improvement
6. Overall assessment (approve/request changes/comment)

Focus on actionable feedback that the author can use to improve the code.
"""
        
        return prompt.strip()


async def dispatch_code_review(repo_full_name: str, pr_number: int):
    """
    Convenience function to dispatch code review
    
    Args:
        repo_full_name: Repository name
        pr_number: Pull request number
    """
    from ..config import Config
    
    reviewer = PRReviewer(
        github_token=Config.GITHUB_APP_SECRET,  # TODO: Use proper GitHub App token
        openclaw_api_url=Config.OPENCLAW_API_URL
    )
    
    return await reviewer.dispatch_code_review(repo_full_name, pr_number)
