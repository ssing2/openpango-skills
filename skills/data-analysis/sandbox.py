#!/usr/bin/env python3
"""
sandbox.py - Secure Jupyter-like Data Analysis Sandbox

Provides an isolated execution environment for running pandas/numpy/matplotlib
code safely, similar to Jupyter notebooks but with sandboxing protections.

Usage:
    python sandbox.py execute --code "df.groupby('category').sum()"
    python sandbox.py file --input data.csv --script analysis.py
"""

import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List


class SandboxError(Exception):
    """Sandbox execution error."""
    pass


class CodeAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST for dangerous operations."""

    DANGEROUS_CALLS = {
        'open', 'compile', 'eval', 'exec', 'getattr', 'setattr', 'delattr',
        '__import__', 'exit', 'quit',
        'os.system', 'os.open', 'os.fdopen',
        'subprocess.run', 'subprocess.call',
        'subprocess.Popen', 'subprocess.check_output',
    }

    def __init__(self):
        self.violations = []
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.DANGEROUS_CALLS:
                self.violations.append(f"Dangerous call: {node.func.id}")
        self.generic_visit(node)

    def check(self, code: str) -> List[str]:
        """Return list of security violations."""
        self.violations = []
        self.imports = set()

        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            self.violations.append(f"Syntax error: {e}")

        return self.violations


class DataSandbox:
    """
    Secure execution sandbox for data analysis.

    Features:
    - AST-based code analysis
    - Restricted imports
    - Resource limits
    - Temporary workspace
    - Chart encoding
    """

    SAFE_IMPORTS = {
        'pandas', 'numpy', 'matplotlib', 'matplotlib.pyplot',
        'seaborn', 'scipy', 'sklearn', 'json', 'csv',
        'io', 'base64', 'datetime', 'math', 'random'
    }

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path(tempfile.mkdtemp(prefix="data_sandbox_"))
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _validate_code(self, code: str) -> List[str]:
        """
        Validate code for security issues.

        Returns:
            List of violations (empty if safe)
        """
        analyzer = CodeAnalyzer()
        violations = analyzer.check(code)

        # Check imports
        for imp in analyzer.imports:
            root = imp.split('.')[0]
            if root not in self.SAFE_IMPORTS:
                violations.append(f"Unsafe import: {imp}")

        return violations

    def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute code in sandboxed subprocess.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            Result dict with stdout, stderr, charts, etc.
        """
        # Security check
        violations = self._validate_code(code)
        if violations:
            return {
                "success": False,
                "violations": violations,
                "error": "Code validation failed"
            }

        # Write code to file
        code_file = self.workspace / "user_code.py"
        code_file.write_text(code)

        # Build execution script
        exec_script = f"""
import sys
import io
import base64

# Capture output
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()

try:
    # Safe imports
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # Execute user code
    with open('{code_file}', 'r') as f:
        exec(f.read())

except Exception as e:
    import traceback
    print(f"Error: {{e}}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)
finally:
    # Get output
    stdout_val = sys.stdout.getvalue()
    stderr_val = sys.stderr.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
"""

        # Write exec script
        exec_file = self.workspace / "exec_sandbox.py"
        exec_file.write_text(exec_script)

        # Execute in subprocess
        try:
            result = subprocess.run(
                [sys.executable, str(exec_file)],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'MPLBACKEND': 'Agg'}
            )

            # Check for generated charts
            charts = self._extract_charts()

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "charts": charts,
                "workspace": str(self.workspace)
            }

        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "error": "Execution timeout",
                "timeout": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_charts(self) -> List[Dict[str, str]]:
        """
        Extract base64-encoded charts from workspace.

        Returns:
            List of {filename, base64_data}
        """
        charts = []

        for file in self.workspace.glob("*.png"):
            try:
                data = file.read_bytes()
                b64 = base64.b64encode(data).decode('ascii')
                charts.append({
                    "filename": file.name,
                    "base64": b64,
                    "size": len(data)
                })
            except:
                pass

        return charts

    def load_file(self, file_path: str, format: str = 'csv') -> Dict[str, Any]:
        """
        Load a data file into workspace.

        Args:
            file_path: Path to data file
            format: File format (csv, json, excel)

        Returns:
            Load result
        """
        src = Path(file_path)
        if not src.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        dest = self.workspace / src.name

        try:
            import shutil
            shutil.copy(src, dest)
            return {
                "success": True,
                "workspace_path": str(dest),
                "size": dest.stat().st_size
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def cleanup(self):
        """Clean up workspace."""
        import shutil
        try:
            shutil.rmtree(self.workspace)
        except:
            pass


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Data Analysis Sandbox - Secure Jupyter-like execution"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # execute command
    exec_p = subparsers.add_parser("execute", help="Execute code")
    exec_p.add_argument("--code", required=True, help="Python code to execute")
    exec_p.add_argument("--timeout", type=int, default=30, help="Timeout (seconds)")

    # file command
    file_p = subparsers.add_parser("file", help="Execute script on file")
    file_p.add_argument("--input", required=True, help="Input data file")
    file_p.add_argument("--script", required=True, help="Analysis script")
    file_p.add_argument("--format", default="csv", help="File format (csv, json, excel)")

    args = parser.parse_args()

    sandbox = DataSandbox()

    try:
        if args.command == "execute":
            result = sandbox.execute(args.code, args.timeout)
            print(json.dumps(result, indent=2))

        elif args.command == "file":
            # Load file
            load_result = sandbox.load_file(args.input, args.format)
            if not load_result["success"]:
                print(json.dumps(load_result, indent=2))
                sys.exit(1)

            # Read and execute script
            with open(args.script, "r") as f:
                script_code = f.read()

            result = sandbox.execute(script_code, timeout=60)
            result["file_loaded"] = load_result
            print(json.dumps(result, indent=2))

    finally:
        # Keep workspace for debugging
        # sandbox.cleanup()
        pass


if __name__ == "__main__":
    main()
