import logging
import os
from threading import Thread


from flask import Flask, jsonify


# This small Flask app is optional. Some hosting platforms expect a web server
# or health check endpoint even when the main program is a Discord bot.
app = Flask(__name__)


@app.route('/')
def home():
    # Basic browser-friendly check.
    return 'discord bot ok', 200


@app.route('/health')
def health():
    # JSON health endpoint for uptime monitors or hosting platforms.
    return jsonify(status="ok", service="discord-bot"), 200


def run():
    # Hide noisy Flask request logs so the Discord bot logs are easier to read.
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    # Hosting platforms often provide PORT. If not, use 8000 locally.
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    # Start Flask in a background thread so it does not block the Discord bot.
    t = Thread(target=run, daemon=True)
    t.start()
