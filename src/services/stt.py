from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.config import DEFAULT_STT_MODEL


@dataclass
class STTResult:
    text: str
    model_used: str


class SpeechToTextEngine:
    def __init__(self, model_id: str = DEFAULT_STT_MODEL) -> None:
        self.model_id = model_id
        self._pipeline = None

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline

        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "STT dependencies are missing. Install requirements to use audio transcription."
            ) from exc

        device = 0 if torch.cuda.is_available() else -1
        self._pipeline = pipeline(
            task="automatic-speech-recognition",
            model=self.model_id,
            device=device,
        )
        return self._pipeline

    def transcribe(self, audio_path: str) -> STTResult:
        if not audio_path:
            raise ValueError("No audio input provided.")

        transcriber = self._load_pipeline()
        result = transcriber(audio_path)
        text = (result.get("text") if isinstance(result, dict) else str(result)).strip()
        if not text:
            text = ""
        return STTResult(text=text, model_used=self.model_id)
