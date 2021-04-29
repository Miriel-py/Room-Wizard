# global_data.py

import os

# Get bot directory
bot_dir = os.path.dirname(__file__)

# Databases
dbfile = os.path.join(bot_dir, 'database/pinbot_db.db')

# Prefix
default_prefix = 'pinbot '

# Embed color
color = 0xB93239

# Set default footer
async def default_footer(prefix):
    footer = 'Just pinning things.'
    
    return footer

# Error log file
log_dir = os.path.join(bot_dir, 'logs/')
logfile = os.path.join(log_dir, 'discord.log')