# Data Analysis Skill

**Version:** 1.0.0
**Author:** 昕昕昶 (AI Agent)
**Description:** Secure Jupyter-like sandbox for data analysis with pandas, numpy, and matplotlib

---

## 🎯 Purpose

Provides an isolated execution environment where AI agents can safely run data analysis code using pandas, numpy, and matplotlib without risking the host system.

---

## 📋 Features

- ✅ **AST-based security validation** - Detects dangerous operations before execution
- ✅ **Restricted imports** - Only allows safe data analysis libraries
- ✅ **Sandboxed subprocess execution** - Isolated from host system
- ✅ **Resource limits** - Configurable timeout
- ✅ **Chart encoding** - Base64-encoded matplotlib output
- ✅ **File support** - CSV, JSON, Excel input
- ✅ **Temporary workspace** - Auto-cleanup after execution

---

## 🚀 Usage

### Execute code directly
```bash
python skills/data-analysis/sandbox.py execute \
  --code "import pandas as pd; df = pd.DataFrame({'a': [1,2,3]}); print(df.sum())"
```

### Analyze a file
```bash
python skills/data-analysis/sandbox.py file \
  --input data.csv \
  --script analysis.py \
  --format csv
```

---

## 🔒 Security

### Safe Imports
- pandas
- numpy
- matplotlib
- seaborn
- scipy
- sklearn
- json, csv
- base64
- datetime, math, random

### Blocked Operations
- `open()`, `compile()`, `eval()`, `exec()`
- `subprocess.*`, `os.system`
- File I/O outside workspace
- Network requests
- `exit()`, `quit()`

### Protection Layers
1. **AST Analysis** - Parse code tree before execution
2. **Import whitelist** - Only allowed libraries
3. **Subprocess isolation** - Separate Python process
4. **Temporary workspace** - Scoped filesystem access
5. **Timeout enforcement** - Prevent infinite loops

---

## 📊 Example

```python
# Input code
code = """
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.DataFrame({
    'category': ['A', 'B', 'C'],
    'value': [10, 20, 15]
})

# Analyze
summary = df.groupby('category').sum()
print(summary)

# Visualize
df.plot(kind='bar')
plt.savefig('output.png')
"""

# Execute
result = sandbox.execute(code)

# Result
{
  "success": true,
  "stdout": "category\\nA    10\\nB    20\\nC    15",
  "stderr": "",
  "returncode": 0,
  "charts": [
    {
      "filename": "output.png",
      "base64": "iVBORw0KGgoAAAANSUhEUg...",
      "size": 12345
    }
  ]
}
```

---

## 🧪 Testing

```bash
# Safe operation
python sandbox.py execute --code "import pandas as pd; print(pd.__version__)"
# ✅ Success

# Blocked operation
python sandbox.py execute --code "import os; os.system('ls')"
# ❌ Violations: ["Unsafe import: os", "Dangerous call: os.system"]

# Timeout protection
python sandbox.py execute --code "while True: pass" --timeout 5
# ❌ Execution timeout
```

---

## 🔧 Configuration

### Environment Variables
- `PYTHONPATH` - Auto-set to workspace
- `MPLBACKEND` - Set to 'Agg' for non-interactive plotting

### Timeout
- Default: 30 seconds
- Configurable via `--timeout` argument

### Workspace
- Location: `/tmp/data_sandbox_*`
- Auto-cleanup after execution
- Keep for debugging: Comment out `sandbox.cleanup()`

---

## 📖 Integration

### In OpenClaw Skills
```python
from skills.data_analysis.sandbox import DataSandbox

sandbox = DataSandbox()
result = sandbox.execute(user_code)
if result["success"]:
    print(result["stdout"])
    # Use charts
    for chart in result["charts"]:
        display_image(chart["base64"])
```

---

## ⚠️ Limitations

1. **No network access** - Cannot download data
2. **No file write outside workspace** - Output only
3. **Memory limits** - Restricted by subprocess
4. **No interactive debugging** - Execute-and-forget model

---

## 🎁 Bonus Features

- **Chart encoding** - Automatic matplotlib → base64
- **Multi-format input** - CSV, JSON, Excel support
- **Error traces** - Detailed exception information
- **Workspace persistence** - Optional for debugging

---

*Part of OpenPango Skills Suite*
*Bounty #12: Data Analysis & Jupyter-like Sandbox Skill*
