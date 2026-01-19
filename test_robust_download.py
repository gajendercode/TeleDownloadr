import asyncio
import os
import signal
from teledownloadr.core.client import TelegramClient
from teledownloadr.core.downloader import Downloader
from teledownloadr.utils.display import tui

# Configuration for Robustness Test
CHAT_ID = -1001955847750 # Paid Group
LIMIT = 5500             # Target slightly more than 5000 to cover all
MEDIA_TYPES = None       # All media

async def main():
    tui.print_info("🚀 Starting Robustness Stress Test (Phase 13)")
    tui.print_info(f"Target Chat: {CHAT_ID}")
    tui.print_info(f"Limit: {LIMIT} messages")
    tui.print_info("Goal: Verify stability and periodic metadata saving.")

    # simple signal handler for cleaner Ctrl+C in this standalone test
    shutdown_event = asyncio.Event()
    def signal_handler():
        tui.print_info("\n🛑 Ctrl+C received. Initiating graceful shutdown...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler in the same way, but we are on Mac
        pass

    client_wrapper = TelegramClient()
    client = await client_wrapper.start()

    if not client:
        tui.print_error("Failed to start client.")
        return

    downloader = Downloader(client, shutdown_event=shutdown_event)

    try:
        tui.print_info("\n=== Step 1: Scanning (to check existing count) ===")
        # We scan first to see baseline
        file_list, count, size, title, existing, new = await downloader.scan_chat(
            str(CHAT_ID), 
            limit=LIMIT, 
            check_existing=True
        )
        tui.print_success(f"Scan complete. Found {count} files. ({existing} existing, {new} new)")
        
        tui.print_info("\n=== Step 2: Starting Robust Download ===")
        tui.print_info("Monitor the 'existing' count increasing in metadata if you stop and restart.")
        
        # Use metadata=True to enable smart resume and periodic saving
        await downloader.download_from_chat(
            str(CHAT_ID),
            limit=LIMIT,
            media_types=MEDIA_TYPES,
            use_metadata=True
        )

        tui.print_success("\n✅ Robustness Test Completed Successfully!")

    except asyncio.CancelledError:
        tui.print_info("\n⚠ Task Cancelled.")
    except Exception as e:
        tui.print_error(f"\n❌ Test Failed: {e}")
    finally:
        await client_wrapper.stop()
        tui.print_info("Client disconnected.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
