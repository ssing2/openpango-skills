"""
Local LLM Integration
 Ollama and vLLM backend support for local inference
"""

import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any, AsyncIterator
from enum import Enum


class LLMBackend(Enum):
    OLLAMA = "ollama"
    VLLM = "vllm"


class LLMManager:
    """
    Local LLM manager with Ollama and vLLM backend support.
    """
    
    def __init__(
        self,
        backend: LLMBackend = LLMBackend.OLLAMA,
        ollama_url: str = "http://localhost:11434",
        vllm_url: str = "http://localhost:8000"
    ):
        self.backend = backend
        self.ollama_url = ollama_url
        self.vllm_url = vllm_url
    
    def set_backend(self, backend: LLMBackend):
        """Switch between Ollama and vLLM backends."""
        self.backend = backend
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        if self.backend == LLMBackend.OLLAMA:
            return await self._list_ollama_models()
        else:
            return await self._list_vllm_models()
    
    async def _list_ollama_models(self) -> List[Dict[str, Any]]:
        """List Ollama models."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.ollama_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("models", [])
                return []
    
    async def _list_vllm_models(self) -> List[Dict[str, Any]]:
        """List vLLM models."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.vllm_url}/v1/models") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [])
                return []
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3",
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            temperature: Sampling temperature
            stream: Enable streaming responses
        
        Returns:
            Response dict with 'content' and metadata
        """
        if self.backend == LLMBackend.OLLAMA:
            return await self._ollama_chat(messages, model, temperature, stream)
        else:
            return await self._vllm_chat(messages, model, temperature, stream)
    
    async def _ollama_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        stream: bool
    ) -> Dict[str, Any]:
        """Ollama chat completion."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_url}/api/chat",
                json=payload
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"HTTP {resp.status}"}
    
    async def _vllm_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        stream: bool
    ) -> Dict[str, Any]:
        """vLLM chat completion (OpenAI-compatible)."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.vllm_url}/v1/chat/completions",
                json=payload
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"HTTP {resp.status}"}
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3",
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Stream chat responses."""
        if self.backend == LLMBackend.OLLAMA:
            async for chunk in self._ollama_stream(messages, model, temperature):
                yield chunk
        else:
            async for chunk in self._vllm_stream(messages, model, temperature):
                yield chunk
    
    async def _ollama_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> AsyncIterator[str]:
        """Ollama streaming."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_url}/api/chat",
                json=payload
            ) as resp:
                async for line in resp.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data:
                                yield data["message"].get("content", "")
                        except:
                            pass
    
    async def _vllm_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> AsyncIterator[str]:
        """vLLM streaming."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.vllm_url}/v1/chat/completions",
                json=payload
            ) as resp:
                async for line in resp.content:
                    if line and line.startswith(b"data: "):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data:
                                content = data["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                        except:
                            pass


# CLI Interface
async def main():
    """CLI for local LLM operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local LLM Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # list models
    subparsers.add_parser("list", help="List available models")
    
    # chat
    chat_parser = subparsers.add_parser("chat", help="Send chat message")
    chat_parser.add_argument("prompt", help="Prompt to send")
    chat_parser.add_argument("--model", default="llama3", help="Model name")
    chat_parser.add_argument("--backend", default="ollama", choices=["ollama", "vllm"])
    
    args = parser.parse_args()
    
    manager = LLMManager(
        backend=LLMBackend.OLLAMA if args.backend == "ollama" else LLMBackend.VLLM
    )
    
    if args.command == "list":
        models = await manager.list_models()
        print(f"Available models ({args.backend}):")
        for m in models:
            name = m.get("name", m.get("id", "unknown"))
            print(f"  - {name}")
    
    elif args.command == "chat":
        messages = [{"role": "user", "content": args.prompt}]
        response = await manager.chat(messages, model=args.model)
        
        if "message" in response:
            print(response["message"].get("content", ""))
        elif "choices" in response:
            print(response["choices"][0].get("message", {}).get("content", ""))
        else:
            print(f"Error: {response}")


if __name__ == "__main__":
    asyncio.run(main())
