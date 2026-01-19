# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TeleDownloadr is a Python-based CLI application for downloading media (videos, photos, documents) from Telegram chats and channels using the Pyrogram library. It operates as a user client (not a bot) to access private chats and channels the user belongs to.

## Prerequisites

Before running the application, you must:
1. Obtain Telegram API credentials from https://my.telegram.org (API development tools section)
2. Create a `.env` file with `API_ID` and `API_HASH` from your Telegram app registration
3. The first run will prompt for phone number and OTP to create a session file (`my_account.session`)

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The application will:
- Display an interactive CLI menu
- Allow selecting chats from a list or entering chat ID/username manually
- Configure download settings per chat (message limit, media type filter)
- Download media in parallel from multiple selected chats

## Architecture

### Core Components

**Authentication Flow ([core/client.py](core/client.py))**
- `TelegramClient` wraps Pyrogram's Client
- Manages session lifecycle (start/stop)
- Session file persists login state across runs
- Uses user client mode (not bot) to access private content

**Download Engine ([core/downloader.py](core/downloader.py))**
- `Downloader` class handles all download operations
- Key methods:
  - `download_from_chat()`: Fetches history and downloads media from a single chat
  - `download_multiple_chats()`: Parallel downloads using asyncio.gather()
  - `download_media()`: Single message download with retry logic (3 attempts)
  - `list_dialogs()`: Lists recent chats for selection
- Progress tracking integrated with Rich progress bars
- File deduplication: skips already downloaded files by comparing file size
- Automatic filename generation based on media type and message ID

**Configuration ([config/settings.py](config/settings.py))**
- Loads API credentials from `.env` using python-dotenv
- Sets `DOWNLOAD_DIR` to `./downloads` (auto-created if missing)
- All downloaded files are saved to the downloads directory with original or generated filenames

**UI Layer ([utils/display.py](utils/display.py))**
- `TUI` class wraps Rich Console and Questionary for interactive CLI
- Progress bars show per-chat and per-file download progress with transfer speed
- Methods for user prompts: `ask_choice()`, `ask_checkbox()`, `ask_text()`, `ask_confirm()`

### Data Flow

1. User selects action in [main.py](main.py) (list chats or manual entry)
2. If listing: `Downloader.list_dialogs()` fetches recent chats
3. User configures each selected chat (message limit, media type filter)
4. `Downloader.download_multiple_chats()` creates parallel tasks
5. Each task calls `download_from_chat()` which:
   - Fetches message history via `client.get_chat_history()`
   - Filters by media type if specified
   - Downloads each message's media with retry logic
6. Progress updates displayed in real-time via Rich progress bars

### Async Architecture

- Built entirely on Python's asyncio
- Pyrogram client methods are async by nature
- Parallel downloads achieved with `asyncio.gather()` in `download_multiple_chats()`
- Main loop in [main.py](main.py) uses `asyncio.run()`

## Key Implementation Details

**Media Type Filtering**
- Supported filters: "All", "Videos Only", "Photos Only"
- Internally uses Pyrogram's `message.media.value` enum
- Media types: video, photo, document, audio, animation, voice, video_note, sticker

**Retry Logic**
- 3 retry attempts per file with 5-second delays
- Partial downloads are cleaned up on final failure
- Progress bar shows retry count and error messages

**File Naming Strategy**
- Prefers original filename from Telegram metadata
- Falls back to generated names: `{media_type}_{message_id}.{ext}`
- Examples: `video_12345.mp4`, `photo_67890.jpg`, `doc_11111`

**Session Management**
- Session file (`my_account.session`) stored in project root
- Contains encrypted authentication state
- Allows reusing login across runs without re-authentication
- Never commit session files to version control

## Environment Variables

Required in `.env`:
- `API_ID`: Telegram API ID (integer)
- `API_HASH`: Telegram API hash (string)
- `BOT_TOKEN`: Optional, not used in current user client implementation

## Dependencies

Core libraries:
- `Pyrogram==2.0.106`: Telegram MTProto API client
- `TgCrypto==1.2.5`: Accelerates Pyrogram encryption (recommended)
- `questionary==2.1.1`: Interactive CLI prompts
- `rich`: Terminal formatting and progress bars
- `python-dotenv`: Environment variable management
- `tqdm`: Progress bar library (indirect dependency)

See [requirements.txt](requirements.txt) for full dependency list.
