import asyncio
import time
import signal
from teledownloadr.core.client import TelegramClient
from teledownloadr.core.downloader import Downloader
from teledownloadr.utils.display import tui

# Configuration for Speed Test
TEST_CHAT_ID = -1001955847750  # Paid Group
TEST_LIMIT = 200               # More files to really see parallelism
TEST_MEDIA_TYPES = None

async def run_benchmark(concurrency: int, shutdown_event: asyncio.Event):
    tui.print_info(f"\n🚀 Running Benchmark with Concurrency = {concurrency}")
    
    client_wrapper = TelegramClient()
    client = await client_wrapper.start()
    if not client:
        return
    
    downloader = Downloader(client, shutdown_event=shutdown_event)
    
    start_time = time.time()
    
    try:
        # Run download
        await downloader.download_from_chat(
            str(TEST_CHAT_ID),
            limit=TEST_LIMIT,
            media_types=TEST_MEDIA_TYPES,
            use_metadata=True, # Use metadata to skip existing, testing overhead + new downloads
            concurrent_downloads=concurrency
        )
    except asyncio.CancelledError:
        tui.print_info("Benchmark task cancelled.")
    except Exception as e:
        tui.print_error(f"Benchmark error: {e}")
    finally:
        end_time = time.time()
        duration = end_time - start_time
        
        tui.print_success(f"✅ Benchmark Finished (Concurrency {concurrency})")
        tui.print_info(f"Time: {duration:.2f} seconds")
        
        await client_wrapper.stop()

async def main():
    tui.print_info("=== 🏎 TeleDownloadr Speed Benchmark ===")
    tui.print_info("Press Ctrl+C to stop safely.")

    # Setup graceful shutdown
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    
    def signal_handler():
        tui.print_info("\n🛑 Stopping benchmark...")
        shutdown_event.set()
        # Cancel all tasks?
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass # Windows

    try:
        # Run parallel test
        await run_benchmark(concurrency=10, shutdown_event=shutdown_event)
    except asyncio.CancelledError:
        pass
    finally:
        tui.print_info("Exiting...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
