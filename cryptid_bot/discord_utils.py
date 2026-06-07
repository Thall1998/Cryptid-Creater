# Discord normal messages can only contain up to 2,000 characters.
DISCORD_MESSAGE_LIMIT = 2000


def split_discord_message(text: str, limit: int = DISCORD_MESSAGE_LIMIT) -> list[str]:
    # If the text already fits, send it as one message.
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text.strip()

    while remaining:
        # If the leftover text fits, this is the final chunk.
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        # Prefer splitting at a newline so formatted sections stay readable.
        split_at = remaining.rfind("\n", 0, limit)

        # If there is no newline, split at a space so words do not get cut.
        if split_at == -1:
            split_at = remaining.rfind(" ", 0, limit)

        # If there is no good split point, hard-split at the Discord limit.
        if split_at == -1:
            split_at = limit

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    return chunks
