import asyncio
import signal
import os
from core.client import TelegramClient
from core.downloader import Downloader
from core.metadata import MetadataManager
from utils.display import tui

async def test_smart_resume():
    """
    Test Phase 4: Smart Resume & Metadata Tracking
    - Scans chat and identifies existing vs new files
    - Downloads only new files
    - Tracks metadata in JSON file
    - Verifies resume capability
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
    tui.print_info("Testing Smart Resume & Metadata Tracking (Phase 4)")

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
        chat_id = selected_chat.id

        tui.print_success(f"Selected chat for testing: {chat_name}")

        # Test 1: Initial scan with existing file detection
        tui.print_info("\n=== Test 1: Scan with Existing File Detection ===")
        file_list, count, total_size, chat_title, existing_count, new_count = await downloader.scan_chat(
            chat_id,
            limit=15,
            media_types=['photo'],
            check_existing=True
        )

        # Show summary
        tui.print_info("\n=== Scan Summary ===")
        total_mb = total_size / (1024 ** 2)
        tui.console.print(f"[bold]Total Files: {count}[/]")
        tui.console.print(f"[green]Existing: {existing_count}[/]")
        tui.console.print(f"[white]New: {new_count}[/]")
        tui.console.print(f"[bold]Total Size: {total_mb:.2f} MB[/]")

        # Test 2: Check MetadataManager
        tui.print_info("\n=== Test 2: MetadataManager Check ===")
        metadata = MetadataManager(chat_id)
        stats = metadata.get_stats()
        tui.console.print(f"Downloaded: {stats['downloaded']}")
        tui.console.print(f"Failed: {stats['failed']}")
        tui.console.print(f"Skipped: {stats['skipped']}")
        tui.console.print(f"Total tracked: {stats['total']}")

        # Check if metadata file exists
        metadata_file = os.path.join("downloads", f"{chat_id}_history.json")
        if os.path.exists(metadata_file):
            file_size = os.path.getsize(metadata_file)
            tui.print_success(f"✔ Metadata file exists: {metadata_file} ({file_size} bytes)")
        else:
            tui.print_info(f"Metadata file will be created on first download: {metadata_file}")

        # Test 3: Download with smart resume
        if new_count > 0:
            tui.print_info("\n=== Test 3: Download with Smart Resume ===")
            proceed = await tui.ask_confirm(f"Download {new_count} new files? (Will skip {existing_count} existing)")

            if proceed:
                await downloader.download_from_chat(
                    chat_id,
                    limit=15,
                    media_types=['photo'],
                    use_metadata=True
                )

                # Verify metadata was updated
                metadata.load_history()
                new_stats = metadata.get_stats()
                tui.print_info("\n=== Updated Metadata Stats ===")
                tui.console.print(f"Downloaded: {new_stats['downloaded']}")
                tui.console.print(f"Failed: {new_stats['failed']}")
                tui.console.print(f"Total tracked: {new_stats['total']}")

                # Show first few entries
                tui.print_info("\n=== Sample Metadata Entries ===")
                for i, (filename, data) in enumerate(metadata.history.items()):
                    if i >= 3:
                        break
                    size_mb = data.get('size', 0) / (1024 * 1024)
                    status = data.get('status', 'unknown')
                    tui.console.print(f"  {filename} - {size_mb:.2f} MB ({status})")

                if len(metadata.history) > 3:
                    tui.console.print(f"  ... and {len(metadata.history) - 3} more entries")
            else:
                tui.print_info("Download skipped")
        else:
            tui.print_info("No new files to download. All files already exist!")

        # Test 4: Second scan should show all as existing
        if new_count > 0:
            tui.print_info("\n=== Test 4: Re-scan (Verify Smart Resume) ===")
            file_list2, count2, total_size2, chat_title2, existing_count2, new_count2 = await downloader.scan_chat(
                chat_id,
                limit=15,
                media_types=['photo'],
                check_existing=True
            )

            tui.console.print(f"[bold]Re-scan Results:[/]")
            tui.console.print(f"Total Files: {count2}")
            tui.console.print(f"[green]Existing: {existing_count2}[/]")
            tui.console.print(f"[white]New: {new_count2}[/]")

            if new_count2 == 0 and existing_count2 > 0:
                tui.print_success("✔ Smart resume working! All files marked as existing")
            else:
                tui.print_info(f"Still {new_count2} new files (may be normal if some downloads failed)")

        tui.print_success("\n✔ Phase 4 test completed!")

    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client_wrapper.stop()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SMART RESUME & METADATA TRACKING TEST (Phase 4)")
    print("="*60)
    print("This test will:")
    print("1. Scan chat and identify existing vs new files")
    print("2. Download only new files (skip existing)")
    print("3. Track downloads in metadata JSON file")
    print("4. Verify resume capability on re-scan")
    print("="*60 + "\n")

    asyncio.run(test_smart_resume())
