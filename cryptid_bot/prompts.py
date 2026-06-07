from pathlib import Path


# This points to the folder where the text prompt templates live.
# Path(__file__).parent means "the folder this Python file is inside."
PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    # Convert a prompt name like "cryptid_creator" into:
    # cryptid_bot/prompts/cryptid_creator.txt
    path = PROMPT_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")

    # Read the prompt file and remove extra blank space at the beginning/end.
    return path.read_text(encoding="utf-8").strip()
