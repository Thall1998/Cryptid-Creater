# Cryptid Creation Discord Bot

Discord slash-command bot for creating cryptid characters, origin stories, and sighting reports with AI. Generated stories are posted back to Discord and archived against the Discord account that requested them.

## Setup

1. Create a Discord application and bot in the Discord Developer Portal.
2. Invite the bot to your server with the `applications.commands` scope.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

5. Run the bot:

```bash
python main.py
```

The bot stores archived stories in SQLite by default:

```env
DATABASE_PATH=data/cryptid_stories.sqlite3
```

Make sure that path is on persistent storage in production. If your hosting platform resets the filesystem on deploy or restart, point `DATABASE_PATH` at a mounted volume.

## Commands

- `/cryptid idea tone`
- `/origin name details`
- `/sighting location details`
- `/mycryptids`
- `/cryptidstory story_id`
- `/cryptidhelp`

The creation commands post the generated story in the channel with an archive ID and requester mention. `/mycryptids` and `/cryptidstory` are private responses that only show entries owned by the requesting Discord account.

## Project Layout

- `main.py` starts the bot.
- `server.py` contains the optional keep-alive Flask server.
- `cryptid_bot/bot.py` defines Discord slash commands.
- `cryptid_bot/ai.py` sends prompts to the AI model.
- `cryptid_bot/archive.py` stores generated stories by Discord user ID.
- `cryptid_bot/prompts/` contains editable prompt templates.

Set `KEEP_ALIVE=true` in `.env` if you need the Flask health server to run alongside the Discord bot.

## Render Deployment

For a Render Web Service:

- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Health check path: `/health`

Render provides a `PORT` environment variable for Web Services. When `PORT` is present, the bot automatically starts the Flask keep-alive server so Render can detect an open port.

Required environment variables:

```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
```

If you deploy as a Render Background Worker instead, no open port is required.
