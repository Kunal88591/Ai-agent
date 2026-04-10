from __future__ import annotations

from typing import List

import gradio as gr

from src.core.agent import VoiceAgent


agent = VoiceAgent()


def run_pipeline(
    audio_path: str,
    manual_text: str,
    require_confirmation: bool,
    confirmed: bool,
    history: List[List[str]],
):
    try:
        response = agent.handle_audio(
            audio_path=audio_path,
            fallback_text=manual_text,
            require_confirmation=require_confirmation,
            confirmed=confirmed,
        )
    except Exception as exc:
        return "", "error", "Pipeline failed", str(exc), history, history

    history = history or []
    history.append([response.transcription, response.intent, response.action, response.result])

    return (
        response.transcription,
        response.intent,
        response.action,
        response.result,
        history,
        history,
    )


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="NeuroVox Kunal") as demo:
        gr.Markdown("# NeuroVox Kunal")
        gr.Markdown(
            "Voice-controlled local AI agent. Provide audio from microphone/upload, or enter text manually for quick testing. "
            "All file writes are restricted to the output/ folder."
        )

        history_state = gr.State([])

        with gr.Row():
            audio = gr.Audio(
                sources=["microphone", "upload"],
                type="filepath",
                label="Audio Input",
            )
            manual_text = gr.Textbox(
                label="Optional Manual Text (testing fallback)",
                lines=6,
                placeholder="Example: Create a Python file with a retry function.",
            )

        with gr.Row():
            require_confirmation = gr.Checkbox(
                value=True,
                label="Require confirmation before file operations",
            )
            confirmed = gr.Checkbox(
                value=False,
                label="I confirm file/folder execution now",
            )

        run_btn = gr.Button("Run Agent", variant="primary")

        transcription = gr.Textbox(label="Transcribed Text", lines=3)
        intent = gr.Textbox(label="Detected Intent")
        action = gr.Textbox(label="Action Taken")
        result = gr.Textbox(label="Final Output", lines=10)
        history_table = gr.Dataframe(
            headers=["Transcription", "Intent", "Action", "Result"],
            label="Session History",
            wrap=True,
        )

        run_btn.click(
            fn=run_pipeline,
            inputs=[audio, manual_text, require_confirmation, confirmed, history_state],
            outputs=[transcription, intent, action, result, history_table, history_state],
        )

    return demo


def main() -> None:
    demo = build_demo()
    demo.launch()
