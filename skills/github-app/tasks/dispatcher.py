"""
OpenClaw Task Dispatcher for GitHub App

Dispatches tasks to OpenClaw agents based on GitHub events
"""

import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class TaskDispatcher:
    """
    Dispatch tasks to OpenClaw agent system
    
    Task Types:
    - code_review: Review pull request
    - bug_fix: Fix reported bug
    - feature_implement: Implement new feature
    - code_explain: Explain code functionality
    - test_write: Write tests
    - documentation: Add documentation
    """
    
    def __init__(self, openclaw_api_url: str, api_key: str):
        """
        Initialize task dispatcher
        
        Args:
            openclaw_api_url: OpenClaw API endpoint
            api_key: API key for authentication
        """
        self.api_url = openclaw_api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def dispatch(
        self,
        task_type: str,
        repository: str,
        prompt: str,
        context: Dict[str, Any],
        priority: str = "normal"
    ) -> Dict[str, str]:
        """
        Dispatch task to OpenClaw
        
        Args:
            task_type: Type of task (code_review, bug_fix, etc.)
            repository: Repository full name (owner/repo)
            prompt: Task prompt/instructions
            context: Additional context (files, issue, etc.)
            priority: Task priority (low, normal, high, critical)
        
        Returns:
            Dispatch result with task_id
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Prepare task payload
        payload = {
            "task_id": task_id,
            "task_type": task_type,
            "repository": repository,
            "prompt": prompt,
            "context": context,
            "priority": priority,
            "source": "github-app",
            "timestamp": datetime.utcnow().isoformat(),
            "callback_url": f"{self.api_url}/api/callback/{task_id}"
        }
        
        logger.info(f"Dispatching task {task_id}: {task_type} for {repository}")
        
        try:
            # Send to OpenClaw API
            response = await self.client.post(
                f"{self.api_url}/api/tasks/dispatch",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Task {task_id} dispatched successfully")
            
            return {
                "status": "dispatched",
                "task_id": task_id,
                "openclaw_task_id": result.get("task_id"),
                "estimated_time": result.get("estimated_time", "unknown")
            }
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to dispatch task {task_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(e)
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of dispatched task
        
        Args:
            task_id: Task ID to check
        
        Returns:
            Task status and progress
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/api/tasks/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def cancel_task(self, task_id: str) -> Dict[str, str]:
        """
        Cancel running task
        
        Args:
            task_id: Task ID to cancel
        
        Returns:
            Cancellation result
        """
        try:
            response = await self.client.delete(
                f"{self.api_url}/api/tasks/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            response.raise_for_status()
            
            logger.info(f"Task {task_id} cancelled")
            
            return {
                "status": "cancelled",
                "task_id": task_id
            }
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to cancel task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Check if OpenClaw API is accessible
        
        Returns:
            bool: True if API is healthy
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/health",
                timeout=5.0
            )
            
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"OpenClaw API health check failed: {e}")
            return False


# Convenience functions for common tasks

async def dispatch_code_review(
    repository: str,
    pr_number: int,
    pr_data: Dict[str, Any]
) -> Dict[str, str]:
    """
    Dispatch code review task
    
    Args:
        repository: Repository name
        pr_number: PR number
        pr_data: PR information
    
    Returns:
        Dispatch result
    """
    from ..config import Config
    
    dispatcher = TaskDispatcher(
        Config.OPENCLAW_API_URL,
        Config.OPENCLAW_API_KEY
    )
    
    # Generate review prompt
    files_summary = "\n".join([
        f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
        for f in pr_data.get("files", [])
    ])
    
    prompt = f"""
Review Pull Request #{pr_number} in {repository}

**Title:** {pr_data.get('pr_title')}
**Author:** {pr_data.get('author')}
**Branch:** {pr_data.get('head_branch')} → {pr_data.get('base_branch')}

**Files Changed:**
{files_summary}

Analyze the changes and provide:
1. Summary of changes
2. Potential issues or bugs
3. Security concerns
4. Performance considerations
5. Suggestions for improvement
6. Overall assessment
"""
    
    return await dispatcher.dispatch(
        task_type="code_review",
        repository=repository,
        prompt=prompt.strip(),
        context={
            "pr_number": pr_number,
            "files": pr_data.get("files", []),
            "author": pr_data.get("author")
        },
        priority="normal"
    )


async def dispatch_bug_fix(
    repository: str,
    issue_number: int,
    bug_description: str,
    issue_context: Dict[str, Any]
) -> Dict[str, str]:
    """
    Dispatch bug fix task
    
    Args:
        repository: Repository name
        issue_number: Issue number
        bug_description: Description of bug
        issue_context: Issue context
    
    Returns:
        Dispatch result
    """
    from ..config import Config
    
    dispatcher = TaskDispatcher(
        Config.OPENCLAW_API_URL,
        Config.OPENCLAW_API_KEY
    )
    
    prompt = f"""
Fix bug reported in Issue #{issue_number} in {repository}

**Bug Description:** {bug_description}

**Issue Context:**
- Title: {issue_context.get('title')}
- Author: {issue_context.get('author')}
- Labels: {issue_context.get('labels', [])}

Please:
1. Analyze the issue
2. Identify the bug location
3. Implement a fix
4. Ensure the fix doesn't break existing functionality
5. Create a feature branch and submit PR
"""
    
    return await dispatcher.dispatch(
        task_type="bug_fix",
        repository=repository,
        prompt=prompt.strip(),
        context={
            "issue_number": issue_number,
            "bug_description": bug_description,
            "issue": issue_context
        },
        priority="high"
    )
