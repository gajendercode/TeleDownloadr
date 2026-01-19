import asyncio
import signal
from core.client import TelegramClient
from core.downloader import Downloader
from utils.display import tui

async def test_scan_preview():
    """
    Test the scan & preview feature before downloading.
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
    tui.print_info("Testing Scan & Preview feature")

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
        dialogs, choices = await downloader.list_dialogs(limit=10)

        if not dialogs or len(dialogs) < 1:
            tui.print_error("No chats available.")
            return

        # Use the first chat for testing
        selected_chat = dialogs[0]
        chat_name = selected_chat.title or selected_chat.first_name or str(selected_chat.id)

        tui.print_success(f"Selected chat for testing: {chat_name}")

        # Scan Phase
        tui.print_info("\n=== Scanning Phase ===")
        file_list, count, total_size, chat_title = await downloader.scan_chat(
            selected_chat.id,
            limit=10,  # Test with limited messages
            media_types=['photo']  # Photos only for faster testing
        )

        # Show summary
        tui.print_info("\n=== Scan Summary ===")
        total_gb = total_size / (1024 ** 3)
        tui.console.print(f"[bold]Found {count} files. Total Size: ~{total_gb:.2f} GB[/]")

        # Ask if user wants to save scan results
        if count > 0:
            save_scan = await tui.ask_confirm("Save scan results to file?")

            if save_scan:
                import re
                import os
                # Sanitize chat title for filename
                sanitized_title = re.sub(r'[^\w\s-]', '', chat_title)
                sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title).strip('_')
                if not sanitized_title:
                    sanitized_title = "Unknown_Chat"

                filename = f"{sanitized_title}_{selected_chat.id}.txt"

                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Scan Results for {chat_title} ({selected_chat.id})\n")
                        f.write("=" * 60 + "\n")
                        f.write(f"Total Files: {count}\n")
                        f.write(f"Total Size: {total_gb:.2f} GB\n")
                        f.write("=" * 60 + "\n\n")

                        for file_info in file_list:
                            try:
                                size_mb = file_info.get('size', 0) / (1024 * 1024)
                                date_str = file_info.get('date', 'Unknown')
                                file_type = file_info.get('type', 'Unknown')
                                file_name = file_info.get('filename', 'Unknown')
                                f.write(f"[{date_str}] [{file_type}] {file_name} ({size_mb:.2f} MB)\n")
                            except:
                                continue

                    if os.path.exists(filename) and os.path.getsize(filename) > 0:
                        tui.print_success(f"Saved metadata to {filename}")
                    else:
                        tui.print_error(f"Failed to create {filename}")
                except Exception as e:
                    tui.print_error(f"Failed to save {filename}: {e}")

        # Ask for confirmation
        proceed = await tui.ask_confirm("Proceed with download?")

        if proceed:
            tui.print_info("\n=== Download Phase ===")
            await downloader.download_from_chat(
                selected_chat.id,
                limit=10,
                media_types=['photo']
            )
        else:
            tui.print_info("Download cancelled by user.")

        tui.print_success("\nTest completed!")

    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client_wrapper.stop()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SCAN & PREVIEW TEST")
    print("="*60)
    print("This test will scan a chat and show file preview.")
    print("You can then choose whether to proceed with download.")
    print("="*60 + "\n")

    asyncio.run(test_scan_preview())
