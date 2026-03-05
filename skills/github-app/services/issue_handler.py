"""
Issue Command Handler for OpenPango GitHub App

Parses @openpango commands in issue comments and dispatches tasks
"""

import logging
import re
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CommandType(str, Enum):
    """Supported @openpango commands"""
    FIX = "fix"
    REVIEW = "review"
    IMPLEMENT = "implement"
    EXPLAIN = "explain"
    TEST = "test"
    DOCUMENT = "document"


class IssueCommandParser:
    """
    Parse and route @openpango commands from issue comments
    
    Example commands:
    - @openpango fix this bug
    - @openpango review this PR
    - @openpango implement feature X
    - @openpango explain this code
    - @openpango write tests for this
    - @openpango document this function
    """
    
    # Command patterns
    COMMAND_PATTERNS = {
        CommandType.FIX: r"@openpango\s+fix\s+(.+)",
        CommandType.REVIEW: r"@openpango\s+review\s+(.+)",
        CommandType.IMPLEMENT: r"@openpango\s+implement\s+(.+)",
        CommandType.EXPLAIN: r"@openpango\s+explain\s+(.+)",
        CommandType.TEST: r"@openpango\s+(?:write\s+)?tests?\s+(?:for\s+)?(.+)",
        CommandType.DOCUMENT: r"@openpango\s+document\s+(.+)",
    }
    
    @classmethod
    def parse(cls, comment_body: str) -> Optional[tuple]:
        """
        Parse @openpango command from comment
        
        Args:
            comment_body: Full comment text
        
        Returns:
            Tuple of (CommandType, command_args) or None
        """
        comment_lower = comment_body.lower().strip()
        
        for command_type, pattern in cls.COMMAND_PATTERNS.items():
            match = re.search(pattern, comment_lower, re.IGNORECASE)
            if match:
                command_args = match.group(1).strip()
                logger.info(f"Parsed command: {command_type.value} - {command_args}")
                return (command_type, command_args)
        
        return None
    
    @classmethod
    def is_valid_command(cls, comment_body: str) -> bool:
        """Check if comment contains valid @openpango command"""
        return cls.parse(comment_body) is not None


class IssueHandler:
    """
    Handle issue commands and dispatch tasks to OpenClaw
    
    Workflow:
    1. Parse command from comment
    2. Fetch issue context
    3. Clone repository
    4. Execute task
    5. Create PR with changes
    """
    
    def __init__(self, github_client, openclaw_api_url: str):
        self.github = github_client
        self.openclaw_api_url = openclaw_api_url
    
    async def handle_command(
        self,
        command_type: CommandType,
        command_args: str,
        issue: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Handle parsed command and dispatch task
        
        Args:
            command_type: Type of command (fix, implement, etc.)
            command_args: Command arguments
            issue: Issue data
            repository: Repository data
        
        Returns:
            Task result
        """
        logger.info(f"Handling {command_type.value} command for issue #{issue['number']}")
        
        # Route to appropriate handler
        handlers = {
            CommandType.FIX: self._handle_fix,
            CommandType.REVIEW: self._handle_review,
            CommandType.IMPLEMENT: self._handle_implement,
            CommandType.EXPLAIN: self._handle_explain,
            CommandType.TEST: self._handle_test,
            CommandType.DOCUMENT: self._handle_document,
        }
        
        handler = handlers.get(command_type)
        if not handler:
            return {"status": "error", "message": f"Unknown command: {command_type.value}"}
        
        return await handler(command_args, issue, repository)
    
    async def _handle_fix(
        self,
        bug_description: str,
        issue: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle fix command"""
        logger.info(f"Fixing bug: {bug_description}")
        
        # TODO: Implement bug fix workflow
        # 1. Clone repository
        # 2. Analyze issue context
        # 3. Identify bug location
        # 4. Generate fix
        # 5. Test fix
        # 6. Create PR
        
        return {
            "status": "dispatched",
            "task": "fix_bug",
            "issue_number": issue["number"],
            "description": bug_description
        }
    
    async def _handle_review(
        self,
        review_target: str,
        issue: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle review command"""
        logger.info(f"Reviewing: {review_target}")
        
        # TODO: Implement review workflow
        
        return {
            "status": "dispatched",
            "task": "review_code",
            "target": review_target
        }
    
    async def _handle_implement(
        self,
        feature_description: str,
        issue: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle implement command"""
        logger.info(f"Implementing feature: {feature_description}")
        
        # TODO: Implement feature workflow
        
        return {
            "status": "dispatched",
            "task": "implement_feature",
            "feature": feature_description
        }
    
    async def _handle_explain(
        self,
        code_target: str,
        issue: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle explain command"""
        logger.info(f"Explaining: {code_target}")
        
        # TODO: Implement explanation workflow
        
        return {
            "status": "dispatched",
            "task": "explain_code",
            "target": code_target
        }
    
    async def _handle_test(
        self,
        test_target: str,
        issue: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle test command"""
        logger.info(f"Writing tests for: {test_target}")
        
        # TODO: Implement test writing workflow
        
        return {
            "status": "dispatched",
            "task": "write_tests",
            "target": test_target
        }
    
    async def _handle_document(
        self,
        doc_target: str,
        issue: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle document command"""
        logger.info(f"Documenting: {doc_target}")
        
        # TODO: Implement documentation workflow
        
        return {
            "status": "dispatched",
            "task": "document_code",
            "target": doc_target
        }


async def parse_and_dispatch(
    comment_body: str,
    issue: Dict[str, Any],
    repository: Dict[str, Any],
    github_client,
    openclaw_api_url: str
) -> Optional[Dict[str, str]]:
    """
    Parse command from comment and dispatch to handler
    
    Args:
        comment_body: Comment text
        issue: Issue data
        repository: Repository data
        github_client: GitHub API client
        openclaw_api_url: OpenClaw API endpoint
    
    Returns:
        Task result or None if no valid command
    """
    # Parse command
    parsed = IssueCommandParser.parse(comment_body)
    if not parsed:
        logger.info("No valid @openpango command found")
        return None
    
    command_type, command_args = parsed
    
    # Create handler
    handler = IssueHandler(github_client, openclaw_api_url)
    
    # Dispatch command
    return await handler.handle_command(
        command_type,
        command_args,
        issue,
        repository
    )
