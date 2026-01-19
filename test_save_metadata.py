import asyncio
import signal
import os
from core.client import TelegramClient
from core.downloader import Downloader
from utils.display import tui

async def test_save_metadata():
    """
    Test the save scan metadata feature (Phase 3).
    This test scans a chat, displays files, and saves results to a text file.
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
    tui.print_info("Testing Save Scan Metadata feature (Phase 3)")

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
            limit=20,  # Test with 20 messages
            media_types=None  # All media types
        )

        # Show summary
        tui.print_info("\n=== Scan Summary ===")
        total_gb = total_size / (1024 ** 3)
        total_mb = total_size / (1024 ** 2)
        tui.console.print(f"[bold]Found {count} files. Total Size: ~{total_mb:.2f} MB (~{total_gb:.4f} GB)[/]")

        if count == 0:
            tui.print_info("No media files found in this chat. Test cannot proceed.")
            return

        # Ask if user wants to save scan results
        save_scan = await tui.ask_confirm("Save scan results to file?")

        if save_scan:
            import re
            # Sanitize chat title for filename
            sanitized_title = re.sub(r'[^\w\s-]', '', chat_title)
            sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title)
            filename = f"{sanitized_title}_{selected_chat.id}.txt"

            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Scan Results for {chat_title} ({selected_chat.id})\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Total Files: {count}\n")
                    f.write(f"Total Size: {total_mb:.2f} MB ({total_gb:.4f} GB)\n")
                    f.write("=" * 60 + "\n\n")

                    for file_info in file_list:
                        size_mb = file_info['size'] / (1024 * 1024)
                        f.write(f"[{file_info['date']}] [{file_info['type']}] {file_info['filename']} ({size_mb:.2f} MB)\n")

                tui.print_success(f"✔ Saved metadata to {filename}")

                # Verify the file was created
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    tui.print_success(f"✔ File verified: {filename} ({file_size} bytes)")

                    # Show first few lines
                    tui.print_info("\n=== First 10 lines of saved file ===")
                    with open(filename, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if i >= 10:
                                break
                            print(line.rstrip())
                else:
                    tui.print_error("✗ File was not created!")
            except Exception as e:
                tui.print_error(f"Failed to save {filename}: {e}")
                import traceback
                traceback.print_exc()
        else:
            tui.print_info("Scan results not saved.")

        # Ask for download confirmation
        proceed = await tui.ask_confirm("Proceed with download?")

        if proceed:
            tui.print_info("\n=== Download Phase ===")
            await downloader.download_from_chat(
                selected_chat.id,
                limit=20,
                media_types=None
            )
        else:
            tui.print_info("Download cancelled by user.")

        tui.print_success("\n✔ Test completed!")

    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client_wrapper.stop()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SAVE SCAN METADATA TEST (Phase 3)")
    print("="*60)
    print("This test will:")
    print("1. Scan a chat for media files")
    print("2. Display file details")
    print("3. Save results to ChatName_ChatID.txt")
    print("4. Verify the file was created")
    print("="*60 + "\n")

    asyncio.run(test_save_metadata())
