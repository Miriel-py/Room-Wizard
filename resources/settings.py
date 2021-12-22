# global_data.py

import os

from dotenv import load_dotenv

# Read the bot token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE')

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BOT_DIR, 'database/room_wizard_db.db')
LOG_FILE = os.path.join(BOT_DIR, 'logs/discord.log')

DEV_GUILDS = [730115558766411857]

# Embed color
EMBED_COLOR = 0x6C48A7
DEFAULT_FOOTER = 'Just pinning things.'