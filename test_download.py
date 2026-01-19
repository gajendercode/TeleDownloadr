import asyncio
import random
import signal
from teledownloadr.core.client import TelegramClient
from teledownloadr.core.downloader import Downloader
from teledownloadr.utils.display import tui

async def test_download():
    """
    Automated test: Download 5 videos from 5 random chats
    """
    shutdown_event = asyncio.Event()

    # Get the current event loop
    loop = asyncio.get_running_loop()

    # Define signal handler
    def handle_shutdown():
        print("\n\n🛑 Test cancelled by user")
        shutdown_event.set()

    # Register signal handlers (asyncio-aware)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)

    tui.print_banner()
    tui.print_info("Starting automated test: 5 videos from 5 random chats")

    # Initialize Client
    client_wrapper = TelegramClient()
    try:
        app = await client_wrapper.start()
    except Exception as e:
        tui.print_error(f"Failed to start client: {e}")
        return

    downloader = Downloader(app, shutdown_event=shutdown_event)

    try:
        # Fetch available chats
        tui.print_info("Fetching available chats...")
        dialogs, choices = await downloader.list_dialogs(limit=50)

        if not dialogs or len(dialogs) < 5:
            tui.print_error(f"Not enough chats available. Found: {len(dialogs)}, need at least 5")
            return

        # Select 5 random chats
        selected_indices = random.sample(range(len(dialogs)), min(5, len(dialogs)))
        selected_chats = [dialogs[i] for i in selected_indices]

        tui.print_success(f"Selected {len(selected_chats)} random chats:")
        for chat in selected_chats:
            chat_name = chat.title or chat.first_name or str(chat.id)
            tui.print_info(f"  - {chat_name} ({chat.id})")

        # Configure downloads for each chat
        configs = []
        for chat in selected_chats:
            chat_name = chat.title or chat.first_name or str(chat.id)
            configs.append({
                'chat_id': chat.id,
                'limit': 50,  # Check last 50 messages to find videos
                'media_types': ['video']  # Only videos
            })
            tui.print_success(f"Configured {chat_name}: 50 messages, videos only")

        # Start downloads
        tui.print_info("Starting parallel downloads...")
        await downloader.download_multiple_chats(configs)

        tui.print_success("Test completed!")

    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client_wrapper.stop()

if __name__ == "__main__":
    asyncio.run(test_download())
