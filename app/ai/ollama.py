import json

import httpx
from typing import Optional


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format: Optional[str] = None,
    ) -> str:
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system is not None:
            body["system"] = system
        if format is not None:
            body["format"] = format

        resp = await self._client.post(f"{self.base_url}/api/generate", json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["response"]

    async def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> dict:
        text = await self.generate(prompt, system=system, format="json")
        return json.loads(text)

    async def check_available(self) -> bool:
        try:
            resp = await self._client.get(f"{self.base_url}/api/tags")
            return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def is_model_available(self, model: Optional[str] = None) -> bool:
        target = model or self.model
        try:
            resp = await self._client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            return any(m.get("name") == target for m in models)
        except httpx.RequestError:
            return False

    def set_model(self, model: str) -> None:
        self.model = model
