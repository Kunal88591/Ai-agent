from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.services.llm_service import LLMService
from src.services.stt import SpeechToTextEngine
from src.tools.executor import ActionExecutor


@dataclass
class AgentResponse:
    transcription: str
    intent: str
    action: str
    result: str


class VoiceAgent:
    def __init__(self) -> None:
        self.stt = SpeechToTextEngine()
        self.llm = LLMService()
        self.executor = ActionExecutor()

    def handle_audio(
        self,
        audio_path: str,
        fallback_text: str,
        require_confirmation: bool,
        confirmed: bool,
    ) -> AgentResponse:
        if fallback_text and fallback_text.strip():
            transcription = fallback_text.strip()
        else:
            stt_result = self.stt.transcribe(audio_path)
            transcription = stt_result.text

        if not transcription:
            return AgentResponse(
                transcription="",
                intent="unknown",
                action="No action",
                result="Could not transcribe meaningful speech.",
            )

        intent_payload: Dict = self.llm.detect_intent(transcription)
        execution = self.executor.execute(
            intent_payload=intent_payload,
            llm_service=self.llm,
            require_confirmation=require_confirmation,
            confirmed=confirmed,
        )

        return AgentResponse(
            transcription=transcription,
            intent=intent_payload.get("intent", "general_chat"),
            action=execution["action"],
            result=execution["result"],
        )
