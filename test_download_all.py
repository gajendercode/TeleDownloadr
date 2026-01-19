import asyncio
import random
import signal
from core.client import TelegramClient
from core.downloader import Downloader
from utils.display import tui

async def test_download_all():
    """
    Test the "Download All" feature with a single chat.
    Tests both limited and unlimited (limit=0) message fetching.
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
    tui.print_info("Testing 'Download All' feature")

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

        if not dialogs or len(dialogs) < 1:
            tui.print_error(f"No chats available.")
            return

        # Select a random chat for testing
        selected_chat = random.choice(dialogs)
        chat_name = selected_chat.title or selected_chat.first_name or str(selected_chat.id)

        tui.print_success(f"Selected chat for testing: {chat_name} ({selected_chat.id})")

        # Test 1: Download with limit=50 (videos only)
        tui.print_info("\n--- Test 1: Download last 50 videos ---")
        config_limited = {
            'chat_id': selected_chat.id,
            'limit': 50,
            'media_types': ['video']
        }

        await downloader.download_from_chat(
            config_limited['chat_id'],
            limit=config_limited['limit'],
            media_types=config_limited['media_types']
        )

        # Ask user if they want to test unlimited download
        tui.print_info("\n--- Test 2: Download ALL messages (limit=0) ---")
        tui.print_info("WARNING: This will attempt to download all media from the chat history.")
        tui.print_info("This can take a VERY long time for chats with thousands of messages.")

        proceed = await tui.ask_confirm("Do you want to proceed with unlimited download test?")

        if proceed:
            # Test 2: Download all with limit=0 (photos only to be faster)
            tui.print_info("Starting unlimited download test (photos only)...")
            config_unlimited = {
                'chat_id': selected_chat.id,
                'limit': 0,  # 0 means ALL messages
                'media_types': ['photo']
            }

            await downloader.download_from_chat(
                config_unlimited['chat_id'],
                limit=config_unlimited['limit'],
                media_types=config_unlimited['media_types']
            )
        else:
            tui.print_info("Skipped unlimited download test.")

        tui.print_success("\nAll tests completed!")

    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client_wrapper.stop()

if __name__ == "__main__":
    asyncio.run(test_download_all())
