from typing import Callable, Dict

from .anthropic_adapter import execute as execute_anthropic
from .base import AdapterExecutionError
from .google_adapter import execute as execute_google
from .ollama_adapter import execute as execute_ollama
from .openai_adapter import execute as execute_openai


AdapterFn = Callable[[str, str, str, float, int], str]


ADAPTERS: Dict[str, AdapterFn] = {
    "openai": execute_openai,
    "anthropic": execute_anthropic,
    "google": execute_google,
    "ollama": execute_ollama,
}


def infer_provider(model: str) -> str:
    """Infer provider from model naming conventions."""
    model_lower = (model or "").lower()

    if any(model_lower.startswith(prefix) for prefix in ("gpt", "o1", "o3", "o4", "text-embedding")):
        return "openai"
    if "claude" in model_lower:
        return "anthropic"
    if "gemini" in model_lower or "palm" in model_lower:
        return "google"
    if any(model_lower.startswith(prefix) for prefix in ("llama", "mistral", "qwen", "deepseek")):
        return "ollama"
    return "openai"


def execute_inference(
    provider: str,
    prompt: str,
    model: str,
    api_key: str,
    timeout: float = 30.0,
    max_retries: int = 2,
) -> str:
    """Dispatch to provider adapter. Supports demo mode for showcase."""
    # Demo mode: return simulated responses when no real API key is configured
    if api_key.startswith("sk-demo") or api_key.startswith("mock_") or not api_key:
        import time, random, hashlib
        time.sleep(random.uniform(0.05, 0.2))  # Simulate 50-200ms latency
        seed = hashlib.md5(prompt.encode()).hexdigest()[:8]
        responses = [
            f"Based on the analysis of the given topic, there are several key aspects to consider. "
            f"The concept involves distributed autonomous systems coordinating through market mechanisms. "
            f"[Demo response from {model} — seed:{seed}]",
            f"The research indicates that agent-to-agent economies operate on trust scoring, "
            f"task routing, and escrow-based payment settlement. Each agent contributes compute "
            f"resources in exchange for economic rewards. [Demo response from {model} — seed:{seed}]",
            f"In autonomous agent networks, coordination happens through standardized protocols "
            f"like A2A (Agent-to-Agent) communication. Miners register their capabilities, and "
            f"tasks are routed to the most suitable agent. [Demo response from {model} — seed:{seed}]",
        ]
        return responses[int(seed, 16) % len(responses)]

    adapter = ADAPTERS.get((provider or "").lower())
    if adapter is None:
        raise AdapterExecutionError(f"Unsupported provider: {provider}", retryable=False)

    return adapter(prompt, model, api_key, timeout, max_retries)
