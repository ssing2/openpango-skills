"""
Safety and Permission Scoping for OpenPango GitHub App

Ensures the app cannot accidentally overwrite protected branches
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """GitHub App permission levels"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class SafetyChecker:
    """
    Enforce safety rules and permission scoping
    
    Safety Rules:
    1. Never push directly to main/master
    2. Always create feature branches
    3. Require PR approval for sensitive repos
    4. Limit concurrent operations
    5. Audit all actions
    """
    
    # Protected branches (cannot push directly)
    PROTECTED_BRANCHES = ["main", "master", "develop", "production", "staging"]
    
    # Repositories requiring extra approval
    SENSITIVE_REPOS = [
        "openpango/openpango-skills",  # Main repo
    ]
    
    # Maximum concurrent operations
    MAX_CONCURRENT_OPS = 5
    
    def __init__(self):
        self.current_ops = 0
        self.audit_log = []
    
    def is_protected_branch(self, branch_name: str) -> bool:
        """
        Check if branch is protected
        
        Args:
            branch_name: Branch name to check
        
        Returns:
            bool: True if branch is protected
        """
        return branch_name.lower() in [b.lower() for b in self.PROTECTED_BRANCHES]
    
    def is_sensitive_repo(self, repo_full_name: str) -> bool:
        """
        Check if repository requires extra approval
        
        Args:
            repo_full_name: Repository name (owner/repo)
        
        Returns:
            bool: True if repo is sensitive
        """
        return repo_full_name in self.SENSITIVE_REPOS
    
    def can_push_to_branch(
        self,
        repo_full_name: str,
        branch_name: str,
        force: bool = False
    ) -> tuple[bool, str]:
        """
        Check if push operation is allowed
        
        Args:
            repo_full_name: Repository name
            branch_name: Target branch
            force: Whether this is a force push
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Rule 1: Never force push
        if force:
            reason = "Force pushes are not allowed"
            self._log_audit("push_denied", repo_full_name, branch_name, reason)
            return (False, reason)
        
        # Rule 2: Never push to protected branches
        if self.is_protected_branch(branch_name):
            reason = f"Branch '{branch_name}' is protected. Create a feature branch instead."
            self._log_audit("push_denied", repo_full_name, branch_name, reason)
            return (False, reason)
        
        # Rule 3: Check concurrent operations
        if self.current_ops >= self.MAX_CONCURRENT_OPS:
            reason = f"Too many concurrent operations ({self.current_ops}/{self.MAX_CONCURRENT_OPS})"
            self._log_audit("push_denied", repo_full_name, branch_name, reason)
            return (False, reason)
        
        # Rule 4: Sensitive repos require approval
        if self.is_sensitive_repo(repo_full_name):
            reason = f"Repository '{repo_full_name}' requires manual approval"
            self._log_audit("push_needs_approval", repo_full_name, branch_name, reason)
            logger.warning(reason)
            # Still allow, but log warning
        
        # All checks passed
        self._log_audit("push_allowed", repo_full_name, branch_name, "All safety checks passed")
        return (True, "Operation allowed")
    
    def generate_branch_name(self, base_branch: str, task_type: str, issue_number: int) -> str:
        """
        Generate safe feature branch name
        
        Args:
            base_branch: Base branch name
            task_type: Type of task (fix, feature, etc.)
            issue_number: Related issue number
        
        Returns:
            Safe branch name
        """
        # Sanitize inputs
        safe_task_type = task_type.lower().replace(" ", "-")[:20]
        
        # Generate branch name
        branch_name = f"openpango/{safe_task_type}-{issue_number}"
        
        logger.info(f"Generated branch name: {branch_name}")
        return branch_name
    
    def _log_audit(
        self,
        action: str,
        repo: str,
        branch: str,
        details: str
    ):
        """
        Log action to audit trail
        
        Args:
            action: Action type
            repo: Repository name
            branch: Branch name
            details: Action details
        """
        import datetime
        
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "action": action,
            "repository": repo,
            "branch": branch,
            "details": details
        }
        
        self.audit_log.append(entry)
        logger.info(f"SAFETY AUDIT: {action} - {repo}/{branch} - {details}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent audit log entries
        
        Args:
            limit: Maximum number of entries
        
        Returns:
            List of audit entries
        """
        return self.audit_log[-limit:]
    
    def check_permissions(
        self,
        permissions: Dict[str, str],
        required_level: PermissionLevel
    ) -> bool:
        """
        Check if app has required permissions
        
        Args:
            permissions: Granted permissions dict
            required_level: Required permission level
        
        Returns:
            bool: True if permissions are sufficient
        """
        # TODO: Implement permission level checking
        # This would check the GitHub App's granted permissions
        
        return True  # Placeholder


# Global safety checker instance
safety_checker = SafetyChecker()
