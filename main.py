# main.py is the entry point for the whole project.
# Keep this file small: it just imports the bot runner and starts it.
from cryptid_bot.bot import run_bot


# This check means "only start the bot when this file is run directly."
# It prevents the bot from starting accidentally if another file imports main.py.
if __name__ == "__main__":
    run_bot()
