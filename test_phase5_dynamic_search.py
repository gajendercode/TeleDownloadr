import asyncio
import signal
from teledownloadr.core.client import TelegramClient
from teledownloadr.core.downloader import Downloader
from teledownloadr.utils.display import tui

async def test_dynamic_search():
    """
    Test Phase 5: Dynamic Chat Search
    - Fetches large number of chats (500+)
    - Demonstrates search-enabled checkbox
    - User can type to filter chats in real-time
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
    tui.print_info("Testing Dynamic Chat Search (Phase 5)")

    # Initialize Client
    client_wrapper = TelegramClient()
    try:
        app = await client_wrapper.start()
    except Exception as e:
        tui.print_error(f"Failed to start client: {e}")
        return

    downloader = Downloader(app, shutdown_event=shutdown_event)

    try:
        # Test 1: Fetch large chat list
        tui.print_info("\n=== Test 1: Fetching Large Chat List ===")
        tui.print_info("Fetching 500 most recent chats for search testing...")

        dialogs, choices = await downloader.list_dialogs(limit=500)

        if not dialogs or len(dialogs) < 1:
            tui.print_error("No chats available.")
            return

        tui.print_success(f"✔ Loaded {len(dialogs)} chats")

        # Test 2: Demonstrate search functionality
        tui.print_info("\n=== Test 2: Search-Enabled Chat Selection ===")
        tui.print_info("Instructions for the next prompt:")
        tui.console.print("  • [bold cyan]Type any text[/] to filter/search chats")
        tui.console.print("  • [bold cyan]Arrow keys[/] to navigate")
        tui.console.print("  • [bold cyan]Space[/] to select/deselect")
        tui.console.print("  • [bold cyan]Enter[/] to confirm selection")
        tui.print_info("\nTry searching for:")
        tui.console.print("  • A chat name keyword")
        tui.console.print("  • Part of a username")
        tui.console.print("  • Any text that appears in chat titles")

        selections = await tui.ask_checkbox(
            "\nSelect chats to download from:",
            choices=choices,
            instruction="(Type to search/filter, Space to select, Enter to confirm)",
            use_shortcuts=False  # Disable shortcuts to enable search
        )

        if not selections:
            tui.print_info("No chats selected. Test ended.")
            return

        tui.print_success(f"\n✔ You selected {len(selections)} chat(s):")
        for i, sel in enumerate(selections, 1):
            tui.console.print(f"  {i}. {sel}")

        # Test 3: Optional - proceed with scan
        proceed = await tui.ask_confirm("\nProceed with scanning selected chats?")

        if proceed:
            # Extract IDs
            targets = []
            for sel in selections:
                index = choices.index(sel)
                targets.append(dialogs[index].id)

            # Quick scan (limit 5 messages per chat for speed)
            tui.print_info("\n=== Quick Scan (5 messages per chat) ===")
            for chat_id in targets:
                try:
                    file_list, count, total_size, chat_title, existing, new = await downloader.scan_chat(
                        chat_id,
                        limit=5,
                        media_types=None,
                        check_existing=True
                    )

                    if count > 0:
                        tui.console.print(f"\n[bold]{chat_title}:[/] {count} files ({existing} existing, {new} new)")
                    else:
                        tui.console.print(f"\n[bold]{chat_title}:[/] No media in last 5 messages")

                except Exception as e:
                    tui.print_error(f"Error scanning {chat_id}: {str(e)[:50]}")
                    continue

        tui.print_success("\n✔ Phase 5 test completed!")

    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client_wrapper.stop()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DYNAMIC CHAT SEARCH TEST (Phase 5)")
    print("="*60)
    print("This test will:")
    print("1. Fetch 500 recent chats")
    print("2. Demonstrate search-enabled chat selection")
    print("3. Let you type to filter chats in real-time")
    print("4. Show how search improves usability with many chats")
    print("="*60 + "\n")

    asyncio.run(test_dynamic_search())
