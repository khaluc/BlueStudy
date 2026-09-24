from pathlib import Path


def system_prompt() -> str:
    path = Path(__file__).resolve().parents[2] / 'apps/chat/prompts/system_chat.md'
    return path.read_text(encoding='utf-8')
