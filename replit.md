# Overview

This is a Discord bot designed for couples to track daily moods and set personal reminders. The bot uses slash commands for all interactions and supports bilingual functionality (Indonesian and English). It features role-based user identification (Ariel/Hira), mood tracking with emoji-based selections, weekly mood summaries, and personal reminder systems.

# Recent Changes

**October 30, 2025**: Fixed online deployment configuration
- Changed Flask keep-alive server port from 8080 to 5000 (Replit requirement)
- Removed duplicate bot.run() call that was causing startup issues
- Configured workflow to automatically run the bot with proper web server settings
- Bot is now successfully running online with both Discord gateway and Flask server operational

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Framework
- **Discord Bot Framework**: Built using discord.py with the commands extension
- **Command System**: Utilizes Discord's modern slash commands (app_commands) instead of traditional prefix-based commands
- **Cog-based Architecture**: Modular design with separate cogs for different functionalities:
  - `BantuanCog`: Help/guide command handler
  - `LanguageCog`: Language preference management
  - `MoodCog`: Mood tracking and selection interface
  - `ReminderCog`: One-time reminder scheduling

## Data Storage
- **Database**: SQLite via aiosqlite for asynchronous database operations
- **Schema Design**: 
  - `users` table: Stores user roles, personal channel IDs, and language preferences
  - `moods` table: Records daily mood entries with composite primary key (user_id, date)
- **Rationale**: SQLite chosen for simplicity and no external database server requirement; aiosqlite ensures non-blocking database operations

## User Interface Components
- **Interactive Views**: Discord UI components (View, Select, Button) for mood selection
- **Ephemeral Messages**: Privacy-focused responses visible only to the command user
- **Embed Messages**: Rich formatted help messages for better user experience

## Scheduled Tasks
- **Time-based Operations**: Uses discord.ext.tasks for scheduled mood reminders
- **Timezone Handling**: pytz library for Asia/Jakarta timezone support
- **Time Configuration**: Configurable daily reminder at 21:00 WIB

## Localization
- **Bilingual Support**: Indonesian (id) and English (en) language options
- **User-level Preferences**: Language settings stored per user in database
- **Dynamic Language Retrieval**: Bot method `get_user_language()` accessible across cogs

## Reminder System
- **In-memory Storage**: Active reminders stored in dictionary structure during runtime
- **Asynchronous Scheduling**: Uses asyncio.sleep for non-blocking reminder delays
- **Flexible Duration Format**: Supports minutes (m), hours (h), and days (d) notation
- **Design Trade-off**: Reminders lost on bot restart (acceptable for lightweight personal use case)

## Bot Configuration
- **Intents**: Requires message_content, guilds, and members intents
- **Token Management**: Environment variable-based token storage for security
- **Prefix**: "/" prefix set (though slash commands don't use traditional prefixes)

## Web Server Component
- **Flask Integration**: Includes Flask import for potential web server functionality
- **Threading Support**: Allows concurrent web server operation alongside bot
- **Purpose**: Likely for deployment platforms requiring active HTTP endpoints (e.g., Replit)

# External Dependencies

## Discord API
- **discord.py**: Primary framework for Discord bot functionality
- **Version**: Uses modern app_commands API for slash command support
- **Required Bot Permissions**: Send messages, use slash commands, access channel information

## Database
- **aiosqlite**: Asynchronous SQLite3 interface
- **Purpose**: Stores user roles, language preferences, and mood history
- **File**: Local SQLite database file (couple_bot.db)

## Time & Scheduling
- **pytz**: Timezone conversion and handling (Asia/Jakarta timezone)
- **asyncio**: Built-in Python library for asynchronous task scheduling

## Web Framework
- **Flask**: Lightweight WSGI web application framework
- **Threading**: Standard library for concurrent execution
- **Purpose**: Likely for keeping Replit deployment active

## Environment Configuration
- **os.environ**: Environment variable access for sensitive credentials
- **Token Storage**: Discord bot token stored as 'mood_token_bot' environment variable