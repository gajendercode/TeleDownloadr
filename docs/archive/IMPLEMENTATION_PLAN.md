# Telegram Media Downloader - Implementation Plan

## 1. Project Overview
A Python-based application to download videos and other media from Telegram chats and channels using the Telegram API.

## 2. Technology Stack
- **Language**: Python 3.9+
- **Core Library**: `Pyrogram` (Recommended for speed and modern async support) or `Telethon`.
- **Environment**: `venv` for dependency management.
- **Utilities**: `tqdm` (for progress bars), `python-dotenv` (for security).

## 3. Architecture Design

### 3.1. Directory Structure
```
TeleDownloadr/
├── config/
│   └── settings.py       # Configuration loader (API keys, paths)
├── core/
│   ├── client.py         # Telegram Client initialization
│   ├── downloader.py     # Media download logic with progress tracking
│   └── filters.py        # Logic to filter specific media types (Video, Image)
├── utils/
│   ├── display.py        # CLI UI helpers (banners, progress bars)
│   └── file_manager.py   # File naming and directory management
├── .env                  # Secrets (API_ID, API_HASH) - NOT COMMITTED
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

### 3.2. Key Modules

#### **A. Configuration (`config/`)**
- Loads `API_ID` and `API_HASH` from environment variables.
- Defines default download directories.

#### **B. Authentication (`core/client.py`)**
- Handles the connection to Telegram servers.
- Manages the session file (so you don't have to log in every time).
- **Mode**: User Client (acts as you) is required to download from chats you are part of. Bot Client is limited to public channels or chats where the bot is added. **We will use User Client.**

#### **C. Downloader Engine (`core/downloader.py`)**
- **Input**: Chat ID/Username, Message ID range, or "Last N messages".
- **Process**:
    1. Iterate through history.
    2. Check if message contains media.
    3. Apply filters (e.g., "Video only").
    4. Download with a progress bar.
- **Concurrency**: Use `asyncio` to handle downloads efficiently (though Telegram limits concurrent downloads per connection).

#### **D. User Interface (`main.py`)**
- A clean Command Line Interface (CLI).
- Prompts user for:
    1. Target Channel/Chat.
    2. Number of posts to check or specific link.
    3. Media type preference.

## 4. Prerequisites
To use the Telegram API, you must obtain developer credentials:
1. Log in to [my.telegram.org](https://my.telegram.org).
2. Go to **API development tools**.
3. Create a new application to get your `App api_id` and `App api_hash`.

## 5. Step-by-Step Implementation Guide

### Phase 1: Setup
1. Initialize project and git.
2. Create virtual environment.
3. Install `pyrogram` and `tgcrypto` (for faster download speeds).

### Phase 2: Core Connectivity
1. Create `config.py` to read `.env`.
2. Create `client.py` to establish a session.
3. Verify login works (print "Logged in as [User]").

### Phase 3: Message Retrieval
1. Implement function to fetch history from a chat.
2. Print message details to debug.

### Phase 4: Downloading
1. Implement `download_media` method.
2. Add `tqdm` progress bar integration.
3. Handle file naming (use caption or date if filename is missing).

### Phase 5: Polish
1. Add CLI menu.
2. Add error handling (FloodWait, connection errors).

## 6. Future Enhancements
- **Web UI**: A local web interface using FastAPI + React.
- **Auto-Download**: Monitor a channel and auto-download new media in real-time.
