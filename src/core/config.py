from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "output"

DEFAULT_STT_MODEL = "openai/whisper-small"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
