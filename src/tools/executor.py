from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from src.core.config import OUTPUT_DIR


class ActionExecutor:
    def __init__(self, output_dir: Path = OUTPUT_DIR) -> None:
        self.output_dir = output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, relative_path: str) -> Path:
        target = (self.output_dir / relative_path).resolve()
        if not str(target).startswith(str(self.output_dir)):
            raise ValueError("Unsafe path blocked. Writes are restricted to output/.")
        return target

    def create_file_or_folder(self, file_name: str = "", folder_name: str = "") -> Tuple[str, str]:
        if folder_name:
            folder = self._safe_path(folder_name)
            folder.mkdir(parents=True, exist_ok=True)
            return "Created folder", str(folder)

        target = self._safe_path(file_name or "new_file.txt")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch(exist_ok=True)
        return "Created file", str(target)

    def write_code(self, file_name: str, code: str) -> Tuple[str, str]:
        target = self._safe_path(file_name or "generated.py")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code, encoding="utf-8")
        return "Wrote code", str(target)

    def execute(
        self,
        intent_payload: Dict,
        llm_service,
        require_confirmation: bool,
        confirmed: bool,
    ) -> Dict[str, str]:
        intent = intent_payload.get("intent", "general_chat")

        if intent in {"create_file", "write_code"} and require_confirmation and not confirmed:
            return {
                "action": "Confirmation required",
                "result": "Please check 'I confirm file/folder execution now' to run this file operation.",
            }

        if intent == "create_file":
            action, path = self.create_file_or_folder(
                file_name=intent_payload.get("file_name", "new_file.txt"),
                folder_name=intent_payload.get("folder_name", ""),
            )
            return {"action": action, "result": f"Success: {path}"}

        if intent == "write_code":
            language = intent_payload.get("language", "python")
            instruction = intent_payload.get("code_instruction") or intent_payload.get("content") or ""
            code = llm_service.generate_code(instruction=instruction, language=language)
            action, path = self.write_code(intent_payload.get("file_name", "generated.py"), code)
            return {"action": action, "result": f"Success: {path}\n\n{code}"}

        if intent == "summarize_text":
            target = intent_payload.get("summary_target") or intent_payload.get("content") or ""
            summary = llm_service.summarize(target)
            return {"action": "Summarized text", "result": summary}

        reply = llm_service.chat(intent_payload.get("content", ""))
        return {"action": "General chat", "result": reply}
