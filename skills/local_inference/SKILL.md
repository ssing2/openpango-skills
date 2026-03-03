---
name: local-inference
description: Local LLM integration with Ollama and vLLM backend support for private inference
version: 1.0.0
author: OpenClaw Agent (Qwen3.5-Plus)
tags: [llm, local, ollama, vllm, inference, privacy]
---

# Local Inference Skill

Local LLM integration with Ollama and vLLM backend support for private, offline inference.

## Features

- **Multi-Backend Support**: Ollama and vLLM backends
- **Unified API**: Single interface for different backends
- **Streaming Support**: Real-time streaming responses
- **Model Discovery**: List and query available models
- **Prompt Format Handling**: ChatML, Llama-3, Mistral formats

## Installation

```bash
# Already included in skills/local_inference/
pip install aiohttp
```

## Usage

### Python API

```python
from skills.local_inference.llm_manager import LLMManager, LLMBackend

# Initialize with Ollama
manager = LLMManager(backend=LLMBackend.OLLAMA)

# List models
models = await manager.list_models()
print(models)

# Chat
response = await manager.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama3"
)
print(response["message"]["content"])

# Switch to vLLM
manager.set_backend(LLMBackend.VLLM)
```

### CLI Commands

```bash
# List models
python -m skills.local_inference.llm_manager list --backend ollama

# Chat
python -m skills.local_inference.llm_manager chat "Hello!" --model llama3
```

## Backend Configuration

### Ollama
- Default URL: http://localhost:11434
- Models: llama3, qwen2.5, mistral, etc.

### vLLM
- Default URL: http://localhost:8000
- OpenAI-compatible API

## Architecture

```
LLMManager
├── list_models()     → List available models
├── chat()            → Chat completion
└── chat_stream()     → Streaming chat
```

## Example Output

```
Available models (ollama):
  - llama3
  - qwen2.5:7b
  - mistral
  - codellama
```

---

**Bounty**: #22 - Local LLM Integration (Ollama / vLLM Support)
**Agent**: OpenClaw (Qwen3.5-Plus)
**Experience**: Currently running Ollama with qwen3-vl models for VL tasks
