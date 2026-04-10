from __future__ import annotations

import json
import re
from typing import Any, Dict

import requests

from src.core.config import DEFAULT_OLLAMA_MODEL, OLLAMA_BASE_URL


class LLMService:
    def __init__(self, model: str = DEFAULT_OLLAMA_MODEL, base_url: str = OLLAMA_BASE_URL) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _ollama_chat(self, system_prompt: str, user_prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"].strip()

    def detect_intent(self, transcript: str) -> Dict[str, Any]:
        system_prompt = (
            "Classify the user request into one of these intents: "
            "create_file, write_code, summarize_text, general_chat. "
            "Return strict JSON with keys: intent, file_name, folder_name, content, summary_target, "
            "code_instruction, language, confidence."
        )
        try:
            raw = self._ollama_chat(system_prompt, transcript)
            parsed = json.loads(raw)
            if parsed.get("intent") in {
                "create_file",
                "write_code",
                "summarize_text",
                "general_chat",
            }:
                return parsed
        except Exception:
            pass

        return self._heuristic_intent(transcript)

    def _heuristic_intent(self, transcript: str) -> Dict[str, Any]:
        text = transcript.lower()

        if "summarize" in text or "summary" in text:
            return {
                "intent": "summarize_text",
                "summary_target": transcript,
                "confidence": 0.6,
            }

        if any(k in text for k in ["create file", "make file", "new file", "create folder", "new folder"]):
            return {
                "intent": "create_file",
                "file_name": self._extract_filename(transcript),
                "folder_name": self._extract_foldername(transcript),
                "confidence": 0.55,
            }

        if any(k in text for k in ["write code", "python file", "javascript file", "function", "class"]):
            return {
                "intent": "write_code",
                "file_name": self._extract_filename(transcript),
                "code_instruction": transcript,
                "language": self._extract_language(transcript),
                "confidence": 0.55,
            }

        return {
            "intent": "general_chat",
            "content": transcript,
            "confidence": 0.5,
        }

    @staticmethod
    def _extract_filename(text: str) -> str:
        match = re.search(r"([\w\-]+\.[a-zA-Z0-9]+)", text)
        if match:
            return match.group(1)
        if "python" in text.lower():
            return "generated.py"
        if "javascript" in text.lower() or "js" in text.lower():
            return "generated.js"
        return "note.txt"

    @staticmethod
    def _extract_foldername(text: str) -> str:
        match = re.search(r"folder\s+named\s+([\w\-]+)", text, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def _extract_language(text: str) -> str:
        lowered = text.lower()
        if "python" in lowered:
            return "python"
        if "javascript" in lowered or "js" in lowered:
            return "javascript"
        if "typescript" in lowered:
            return "typescript"
        return "text"

    def generate_code(self, instruction: str, language: str = "python") -> str:
        system_prompt = (
            "Generate only code and no markdown fences. "
            f"Language: {language}. Keep it concise and runnable."
        )
        try:
            return self._ollama_chat(system_prompt, instruction)
        except Exception:
            return self._fallback_code(instruction, language)

    def summarize(self, text: str) -> str:
        system_prompt = "Summarize the text in 3-5 bullet points."
        try:
            return self._ollama_chat(system_prompt, text)
        except Exception:
            clipped = text[:500]
            return f"Summary (fallback): {clipped}"

    def chat(self, text: str) -> str:
        system_prompt = "You are a helpful local assistant. Keep answers short and clear."
        try:
            return self._ollama_chat(system_prompt, text)
        except Exception:
            return "I could not reach Ollama. Please start Ollama or ask a file/summarization command."

    @staticmethod
    def _fallback_code(instruction: str, language: str) -> str:
        if language == "python":
            return (
                "def retry(func, attempts=3):\n"
                "    last_error = None\n"
                "    for _ in range(attempts):\n"
                "        try:\n"
                "            return func()\n"
                "        except Exception as exc:\n"
                "            last_error = exc\n"
                "    raise last_error\n"
            )
        if language in {"javascript", "typescript"}:
            return (
                "function retry(fn, attempts = 3) {\n"
                "  let lastError;\n"
                "  for (let i = 0; i < attempts; i += 1) {\n"
                "    try { return fn(); } catch (e) { lastError = e; }\n"
                "  }\n"
                "  throw lastError;\n"
                "}\n"
            )
        return f"# Could not generate {language} code for: {instruction}"
