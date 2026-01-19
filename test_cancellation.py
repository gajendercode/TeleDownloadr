import asyncio
import signal
from core.client import TelegramClient
from core.downloader import Downloader
from utils.display import tui

async def test_cancellation():
    """
    Test the graceful shutdown/cancellation feature.
    This test downloads from a chat with limit=0 (all messages) to ensure
    we have time to test Ctrl+C cancellation.
    """
    shutdown_event = asyncio.Event()

    # Get the current event loop
    loop = asyncio.get_running_loop()

    # Define signal handler
    def handle_shutdown():
        print("\n\n🛑 Shutdown signal received! Cancelling downloads...")
        shutdown_event.set()

    # Register signal handlers (asyncio-aware)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)

    tui.print_banner()
    tui.print_info("Testing graceful shutdown with Ctrl+C")
    tui.print_info("Press Ctrl+C at any time to test cancellation")

    # Initialize Client
    client_wrapper = TelegramClient()
    try:
        app = await client_wrapper.start()
    except Exception as e:
        tui.print_error(f"Failed to start client: {e}")
        return

    downloader = Downloader(app, shutdown_event=shutdown_event)

    try:
        # Fetch a chat with significant history
        tui.print_info("Fetching chats...")
        dialogs, choices = await downloader.list_dialogs(limit=10)

        if not dialogs:
            tui.print_error("No chats found")
            return

        # Use the first chat
        selected_chat = dialogs[0]
        chat_name = selected_chat.title or selected_chat.first_name or str(selected_chat.id)

        tui.print_success(f"Using chat: {chat_name}")
        tui.print_info("Starting download with limit=0 (all messages)")
        tui.print_info("You can press Ctrl+C anytime to cancel")

        # Download all photos from this chat
        config = {
            'chat_id': selected_chat.id,
            'limit': 0,  # All messages - this will take a long time
            'media_types': ['photo']  # Photos are usually faster to download
        }

        await downloader.download_from_chat(
            config['chat_id'],
            limit=config['limit'],
            media_types=config['media_types']
        )

        tui.print_success("Download completed (or you didn't press Ctrl+C)")

    except KeyboardInterrupt:
        tui.print_info("\nKeyboardInterrupt caught")
        shutdown_event.set()
    except Exception as e:
        tui.print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if shutdown_event.is_set():
            tui.print_info("Cleaning up after cancellation...")
        await client_wrapper.stop()
        tui.print_success("Test completed. Goodbye!")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CANCELLATION TEST")
    print("="*60)
    print("This test will download ALL photos from a chat.")
    print("Press Ctrl+C at any time to test graceful shutdown.")
    print("="*60 + "\n")

    asyncio.run(test_cancellation())
