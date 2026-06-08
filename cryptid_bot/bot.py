import asyncio
import logging
from collections.abc import Callable

import discord
from discord import app_commands

from cryptid_bot.ai import AIServiceError, CryptidStoryAI
from cryptid_bot.archive import StoryArchive
from cryptid_bot.config import load_settings
from cryptid_bot.discord_utils import split_discord_message
from server import keep_alive


# CryptidBot is the Discord client.
# It owns the AI helper and the slash command tree.
class CryptidBot(discord.Client):
    def __init__(self, ai: CryptidStoryAI, archive: StoryArchive, sync_commands: bool):
        # Intents control what Discord events the bot is allowed to receive.
        # Slash commands do not need privileged message content intent.
        intents = discord.Intents.default()
        super().__init__(intents=intents)

        # Store the AI helper so commands can call it.
        self.ai = ai
        self.archive = archive

        # Controls whether slash commands are synced to Discord on startup.
        self.sync_commands = sync_commands

        # app_commands.CommandTree is where slash commands are registered.
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        # Discord.py runs setup_hook before the bot becomes fully ready.
        # This is the right place to register and sync slash commands.
        register_commands(self)
        if self.sync_commands:
            await self.tree.sync()

    async def on_ready(self) -> None:
        # This fires after the bot successfully logs in.
        logging.info("Logged in as %s", self.user)


def register_commands(bot: CryptidBot) -> None:
    @bot.tree.command(name="cryptidhelp", description="Show the available cryptid bot commands.")
    async def cryptidhelp(interaction: discord.Interaction):
        await interaction.response.send_message(build_help_text(), ephemeral=True)

    # /cryptid creates a full creature profile from a simple idea.
    @bot.tree.command(name="cryptid", description="Create a cryptid character and lore entry.")
    @app_commands.describe(
        idea="The creature idea, trait, region, or strange behavior.",
        tone="Optional mood, such as swamp horror, field notes, or campfire legend.",
    )
    async def cryptid(interaction: discord.Interaction, idea: str, tone: str | None = None):
        # defer() gives the bot more time to answer.
        # AI requests can take longer than Discord's normal response window.
        await interaction.response.defer(thinking=True)
        try:
            result = await asyncio.to_thread(bot.ai.create_cryptid, idea=idea, tone=tone)
            await save_and_send_story(
                bot=bot,
                interaction=interaction,
                command="cryptid",
                title=extract_title(result, fallback=idea),
                request={"idea": idea, "tone": tone},
                result=result,
            )
        except Exception as exc:
            # Log the full error for debugging, then show a short message in Discord.
            logging.exception("Failed to create cryptid")
            await interaction.followup.send(format_generation_error("cryptid entry", exc), ephemeral=True)

    # /origin writes a legend/backstory for a cryptid the user already has.
    @bot.tree.command(name="origin", description="Write an origin story for a cryptid.")
    @app_commands.describe(
        name="The cryptid name.",
        details="Existing details about the creature.",
    )
    async def origin(interaction: discord.Interaction, name: str, details: str):
        await interaction.response.defer(thinking=True)
        try:
            result = await asyncio.to_thread(bot.ai.create_origin, name=name, details=details)
            await save_and_send_story(
                bot=bot,
                interaction=interaction,
                command="origin",
                title=extract_title(result, fallback=name),
                request={"name": name, "details": details},
                result=result,
            )
        except Exception as exc:
            logging.exception("Failed to create origin story")
            await interaction.followup.send(format_generation_error("origin story", exc), ephemeral=True)

    # /sighting writes a witness report or archive case file.
    @bot.tree.command(name="sighting", description="Write a witness sighting report.")
    @app_commands.describe(
        location="Where the sighting happened.",
        details="What was seen or heard.",
    )
    async def sighting(interaction: discord.Interaction, location: str, details: str):
        await interaction.response.defer(thinking=True)
        try:
            result = await asyncio.to_thread(
                bot.ai.create_sighting,
                location=location,
                details=details,
            )
            await save_and_send_story(
                bot=bot,
                interaction=interaction,
                command="sighting",
                title=extract_title(result, fallback=location),
                request={"location": location, "details": details},
                result=result,
            )
        except Exception as exc:
            logging.exception("Failed to create sighting report")
            await interaction.followup.send(format_generation_error("sighting report", exc), ephemeral=True)

    @bot.tree.command(name="mycryptids", description="Show your recently archived cryptid stories.")
    async def mycryptids(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        records = await asyncio.to_thread(bot.archive.list_user_stories, interaction.user.id)

        if not records:
            await interaction.followup.send("You do not have any archived cryptid stories yet.", ephemeral=True)
            return

        lines = ["Your recent cryptid archive entries:"]
        for record in records:
            lines.append(f"`{record.id}` - {record.command}: {record.title} ({record.created_at})")
        lines.append("Use `/cryptidstory story_id` to reopen one.")
        await interaction.followup.send("\n".join(lines), ephemeral=True)

    @bot.tree.command(name="cryptidstory", description="Reopen one of your archived cryptid stories.")
    @app_commands.describe(story_id="The archive ID shown by /mycryptids.")
    async def cryptidstory(interaction: discord.Interaction, story_id: int):
        await interaction.response.defer(thinking=True, ephemeral=True)
        result = await asyncio.to_thread(
            bot.archive.get_user_story,
            interaction.user.id,
            story_id,
        )

        if result is None:
            await interaction.followup.send("No archived story with that ID belongs to your account.", ephemeral=True)
            return

        await send_chunked(interaction, f"Archive entry `{story_id}` for {interaction.user.mention}\n\n{result}", ephemeral=True)


async def save_and_send_story(
    *,
    bot: CryptidBot,
    interaction: discord.Interaction,
    command: str,
    title: str,
    request: dict[str, str | None],
    result: str,
) -> None:
    story_id = await asyncio.to_thread(
        bot.archive.save_story,
        discord_user_id=interaction.user.id,
        discord_username=display_name(interaction.user),
        command=command,
        title=title,
        request=request,
        response_text=result,
    )
    message = f"Archive entry `{story_id}` for {interaction.user.mention}\n\n{result}"
    await send_chunked(interaction, message)


async def send_chunked(interaction: discord.Interaction, text: str, ephemeral: bool = False) -> None:
    # Send one Discord message per chunk so long AI outputs do not fail.
    for chunk in split_discord_message(text):
        await interaction.followup.send(chunk, ephemeral=ephemeral)


def display_name(user: discord.abc.User) -> str:
    return getattr(user, "display_name", user.name)


def extract_title(text: str, fallback: str) -> str:
    extractors: list[Callable[[str], str | None]] = [
        lambda line: line.removeprefix("Name:").strip() if line.startswith("Name:") else None,
        lambda line: line.removeprefix("Title:").strip() if line.startswith("Title:") else None,
        lambda line: line.removeprefix("Case Number:").strip() if line.startswith("Case Number:") else None,
    ]

    for line in text.splitlines():
        for extractor in extractors:
            title = extractor(line)
            if title:
                return title[:120]

    return fallback.strip()[:120] or "Untitled story"


def format_generation_error(label: str, exc: Exception) -> str:
    if isinstance(exc, AIServiceError):
        detail = str(exc)
    else:
        detail = "An unexpected error happened. The full details were written to the bot logs."
    return f"Could not create a {label}: {detail}"


def build_help_text() -> str:
    return "\n".join(
        [
            "Available cryptid bot commands:",
            "`/cryptid idea tone` - Create a cryptid profile and archive it to your account.",
            "`/origin name details` - Write an origin story and archive it to your account.",
            "`/sighting location details` - Write a sighting report and archive it to your account.",
            "`/mycryptids` - Privately list your recent archived entries.",
            "`/cryptidstory story_id` - Privately reopen one of your archived entries.",
            "`/cryptidhelp` - Show this help message.",
        ]
    )


def run_bot() -> None:
    # Configure basic terminal logging so startup/errors are visible.
    logging.basicConfig(level=logging.INFO)

    # Load .env/settings before creating the bot.
    settings = load_settings()

    # Optional Flask server for hosting platforms that need a health endpoint.
    if settings.keep_alive:
        keep_alive()

    # Create the AI helper and Discord client, then log into Discord.
    ai = CryptidStoryAI(settings)
    archive = StoryArchive(settings.database_path)
    bot = CryptidBot(ai=ai, archive=archive, sync_commands=settings.sync_commands)
    bot.run(settings.discord_token)
