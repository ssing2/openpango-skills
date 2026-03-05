"""
Tests for GitHub App Safety Checker
"""

import pytest
from services.safety import SafetyChecker, PermissionLevel


class TestSafetyChecker:
    """Test safety and permission checks"""
    
    def setup_method(self):
        """Create fresh safety checker for each test"""
        self.checker = SafetyChecker()
    
    def test_protected_branch_detection(self):
        """Test detection of protected branches"""
        assert self.checker.is_protected_branch("main") is True
        assert self.checker.is_protected_branch("master") is True
        assert self.checker.is_protected_branch("develop") is True
        assert self.checker.is_protected_branch("feature-branch") is False
        assert self.checker.is_protected_branch("bugfix-123") is False
    
    def test_sensitive_repo_detection(self):
        """Test detection of sensitive repositories"""
        assert self.checker.is_sensitive_repo("openpango/openpango-skills") is True
        assert self.checker.is_sensitive_repo("other/repo") is False
    
    def test_push_to_protected_branch_denied(self):
        """Test that push to protected branch is denied"""
        allowed, reason = self.checker.can_push_to_branch(
            "owner/repo",
            "main",
            force=False
        )
        
        assert allowed is False
        assert "protected" in reason.lower()
    
    def test_force_push_denied(self):
        """Test that force push is always denied"""
        allowed, reason = self.checker.can_push_to_branch(
            "owner/repo",
            "feature-branch",
            force=True
        )
        
        assert allowed is False
        assert "force" in reason.lower()
    
    def test_push_to_feature_branch_allowed(self):
        """Test that push to feature branch is allowed"""
        allowed, reason = self.checker.can_push_to_branch(
            "owner/repo",
            "feature-test-123",
            force=False
        )
        
        assert allowed is True
        assert "allowed" in reason.lower()
    
    def test_branch_name_generation(self):
        """Test feature branch name generation"""
        branch = self.checker.generate_branch_name(
            "main",
            "fix bug",
            123
        )
        
        assert branch.startswith("openpango/")
        assert "fix" in branch
        assert "123" in branch
        assert len(branch) < 50  # Reasonable length
    
    def test_audit_logging(self):
        """Test audit log functionality"""
        # Perform some action
        self.checker.can_push_to_branch("test/repo", "main", force=False)
        
        # Check audit log
        log = self.checker.get_audit_log(limit=10)
        
        assert len(log) > 0
        assert "action" in log[0]
        assert "timestamp" in log[0]
        assert "repository" in log[0]
    
    def test_concurrent_operation_limit(self):
        """Test concurrent operation limits"""
        # Simulate concurrent operations
        original_ops = self.checker.current_ops
        self.checker.current_ops = self.checker.MAX_CONCURRENT_OPS
        
        allowed, reason = self.checker.can_push_to_branch(
            "owner/repo",
            "feature-branch",
            force=False
        )
        
        assert allowed is False
        assert "concurrent" in reason.lower()
        
        # Reset
        self.checker.current_ops = original_ops


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
