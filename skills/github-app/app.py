"""
GitHub App Native Integration for OpenPango Skills
Webhook receiver and task dispatcher for CI/CD automation

Author: XiaoXinXin (OpenClaw AI Agent)
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import hmac
import hashlib
import json
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenPango GitHub App", version="1.0.0")

# Configuration (will be moved to config.py)
GITHUB_APP_SECRET = "your_webhook_secret_here"  # TODO: Load from env
GITHUB_APP_ID = "your_app_id_here"  # TODO: Load from env


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature for security
    
    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
    
    Returns:
        bool: True if signature is valid
    """
    if not signature:
        return False
    
    expected_signature = hmac.new(
        GITHUB_APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint for GitHub events
    
    Handles:
    - Pull request events (opened, synchronized)
    - Issue comment events (for @openpango commands)
    - Push events (for branch protection)
    """
    # Get raw body for signature verification
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    # Verify webhook signature
    if not verify_webhook_signature(payload, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse event type
    event_type = request.headers.get("X-GitHub-Event")
    if not event_type:
        raise HTTPException(status_code=400, detail="Missing event type")
    
    # Parse payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info(f"Received {event_type} event")
    
    # Route event to appropriate handler
    if event_type == "pull_request":
        background_tasks.add_task(handle_pull_request, data)
    elif event_type == "issue_comment":
        background_tasks.add_task(handle_issue_comment, data)
    elif event_type == "push":
        background_tasks.add_task(handle_push, data)
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    return JSONResponse(
        status_code=200,
        content={"status": "received", "event": event_type}
    )


async def handle_pull_request(data: Dict[str, Any]):
    """
    Handle pull request events
    
    When a PR is opened or updated:
    1. Fetch the diff
    2. Parse changed files
    3. Dispatch code review task to OpenClaw
    """
    action = data.get("action")
    pr = data.get("pull_request", {})
    
    if action not in ["opened", "synchronize", "reopened"]:
        logger.info(f"Skipping PR action: {action}")
        return
    
    pr_number = pr.get("number")
    repo = data.get("repository", {})
    repo_full_name = repo.get("full_name")
    
    logger.info(f"Processing PR #{pr_number} in {repo_full_name}")
    
    # TODO: Implement PR diff fetching and review dispatch
    # from .services.pr_reviewer import dispatch_code_review
    # await dispatch_code_review(repo_full_name, pr_number)
    
    logger.info(f"PR #{pr_number} review task dispatched")


async def handle_issue_comment(data: Dict[str, Any]):
    """
    Handle issue comment events
    
    Look for @openpango commands in comments:
    - @openpango fix this bug
    - @openpango review this PR
    - @openpango implement feature X
    """
    comment = data.get("comment", {})
    comment_body = comment.get("body", "")
    
    # Check if comment mentions @openpango
    if "@openpango" not in comment_body.lower():
        return
    
    issue = data.get("issue", {})
    repo = data.get("repository", {})
    
    logger.info(f"Found @openpango command in issue #{issue.get('number')}")
    
    # TODO: Parse command and dispatch task
    # from .services.issue_handler import parse_and_dispatch
    # await parse_and_dispatch(comment_body, issue, repo)
    
    logger.info("Issue command processed")


async def handle_push(data: Dict[str, Any]):
    """
    Handle push events
    
    Ensure no direct pushes to protected branches (main, master)
    """
    ref = data.get("ref", "")
    repo = data.get("repository", {})
    
    # Check if pushing to protected branch
    if ref in ["refs/heads/main", "refs/heads/master"]:
        logger.warning(f"Direct push to {ref} detected in {repo.get('full_name')}")
        # TODO: Implement branch protection check
        # This should never happen if GitHub App permissions are set correctly
    
    logger.info(f"Push event to {ref} processed")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "openpango-github-app"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OpenPango GitHub App",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
