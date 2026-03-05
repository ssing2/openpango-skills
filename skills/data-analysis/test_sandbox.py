#!/usr/bin/env python3
"""
test_sandbox.py - Test suite for data analysis sandbox
"""

import json
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(__file__))

from sandbox import DataSandbox, CodeAnalyzer


def test_safe_imports():
    """Test that safe imports are allowed."""
    analyzer = CodeAnalyzer()
    code = "import pandas as pd\nimport numpy as np"
    violations = analyzer.check(code)
    assert len(violations) == 0, f"Unexpected violations: {violations}"
    print("✅ test_safe_imports passed")


def test_unsafe_imports():
    """Test that unsafe imports are blocked."""
    analyzer = CodeAnalyzer()
    code = "import os\nimport subprocess"
    violations = analyzer.check(code)
    assert len(violations) > 0, "Should have violations"
    assert any("os" in v for v in violations), "Should block os import"
    print("✅ test_unsafe_imports passed")


def test_dangerous_calls():
    """Test that dangerous function calls are blocked."""
    analyzer = CodeAnalyzer()
    code = "os.system('ls')"
    violations = analyzer.check(code)
    assert len(violations) > 0, "Should have violations"
    print("✅ test_dangerous_calls passed")


def test_execute_safe_code():
    """Test executing safe code."""
    sandbox = DataSandbox()
    code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
print(df.sum())
"""
    result = sandbox.execute(code, timeout=10)
    assert result["success"], f"Execution failed: {result.get('error')}"
    assert "3" in result["stdout"], f"Unexpected output: {result['stdout']}"
    print("✅ test_execute_safe_code passed")
    sandbox.cleanup()


def test_execute_unsafe_code():
    """Test that unsafe code is rejected."""
    sandbox = DataSandbox()
    code = "import os; os.system('ls')"
    result = sandbox.execute(code, timeout=10)
    assert not result["success"], "Should fail"
    assert "violations" in result, "Should have violations"
    assert len(result["violations"]) > 0, "Should have specific violations"
    print("✅ test_execute_unsafe_code passed")
    sandbox.cleanup()


def test_timeout():
    """Test that timeout is enforced."""
    sandbox = DataSandbox()
    code = "while True: pass"
    result = sandbox.execute(code, timeout=2)
    assert not result["success"], "Should timeout"
    assert "timeout" in str(result.get("error", "")).lower(), "Should mention timeout"
    print("✅ test_timeout passed")
    sandbox.cleanup()


def test_matplotlib_chart():
    """Test matplotlib chart generation."""
    sandbox = DataSandbox()
    code = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.plot([1, 2, 3], [1, 4, 9])
plt.savefig('test.png')
"""
    result = sandbox.execute(code, timeout=10)
    assert result["success"], f"Execution failed: {result.get('error')}"
    assert "charts" in result, "Should have charts field"
    assert len(result["charts"]) > 0, "Should generate at least one chart"
    assert result["charts"][0]["filename"] == "test.png", "Chart filename mismatch"
    print("✅ test_matplotlib_chart passed")
    sandbox.cleanup()


def test_file_not_found():
    """Test loading non-existent file."""
    sandbox = DataSandbox()
    result = sandbox.load_file("/nonexistent/file.csv")
    assert not result["success"], "Should fail"
    assert "not found" in result["error"], "Should mention file not found"
    print("✅ test_file_not_found passed")
    sandbox.cleanup()


def run_all_tests():
    """Run all tests."""
    tests = [
        test_safe_imports,
        test_unsafe_imports,
        test_dangerous_calls,
        test_execute_safe_code,
        test_execute_unsafe_code,
        test_timeout,
        test_matplotlib_chart,
        test_file_not_found,
    ]

    print(f"Running {len(tests)} tests...")
    print("=" * 50)

    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed.append(test.__name__)

    print("=" * 50)
    if failed:
        print(f"\n❌ {len(failed)} tests failed:")
        for name in failed:
            print(f"  - {name}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(tests)} tests passed!")


if __name__ == "__main__":
    run_all_tests()
