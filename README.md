# Room Wizard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python: 3.8](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/) [![Database: SQLite](https://img.shields.io/badge/Database-SQLite-blue.svg)](https://www.sqlite.org/index.html)

## Setup

• Rename `default.env` to `.env` and add your token.  
• Rename `database/default_db.db` to `database/room_wizard_db.db`.  
• Change all custom emojis in `resources/emojis.py` to something the bot can see in your servers.  
• Change `DEVGUILDS` in `resources/emojis.py` to the servers you want to test the bot in. Dev commands will be registered in these. If you set debug mode on in the `.env`, all commands will be registered in these.  

## Required intents

• guilds  
• messages  
• reactions  

## Required permissions

• Manage Roles  
• Manage Channels  
• Read Message History  
• Manage Messages  
• `applications.commands` scope
