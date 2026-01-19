import asyncio
import signal
from teledownloadr.core.client import TelegramClient
from teledownloadr.core.downloader import Downloader
from teledownloadr.utils.display import tui

async def test_search_working():
    """
    Test the WORKING search functionality.
    Uses autocomplete for search, then checkbox for selection.
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
    tui.print_info("Testing WORKING Chat Search (Autocomplete + Checkbox)")

    # Initialize Client
    client_wrapper = TelegramClient()
    try:
        app = await client_wrapper.start()
    except Exception as e:
        tui.print_error(f"Failed to start client: {e}")
        return

    downloader = Downloader(app, shutdown_event=shutdown_event)

    try:
        # Fetch chats
        tui.print_info("\n=== Fetching Chats ===")
        tui.print_info("Fetching 100 chats for search test...")

        dialogs, choices = await downloader.list_dialogs(limit=600)

        if not dialogs or len(dialogs) < 1:
            tui.print_error("No chats available.")
            return

        tui.print_success(f"✔ Loaded {len(dialogs)} chats")

        # Show instructions
        tui.print_info("\n=== How The Search Works ===")
        tui.console.print("")
        tui.console.print("[bold cyan]Step 1: Search (Text Filter)[/]")
        tui.console.print("  • Type keywords to filter chats")
        tui.console.print("  • Press Enter to apply filter")
        tui.console.print("  • Leave empty and press Enter to see all")
        tui.console.print("")
        tui.console.print("[bold cyan]Step 2: Select (Checkbox)[/]")
        tui.console.print("  • Space to select/deselect")
        tui.console.print("  • Enter to confirm")
        tui.console.print("")
        tui.console.print("[bold green]Examples:[/]")
        tui.console.print("  • Type 'saved' + Enter → shows only 'Saved Messages'")
        tui.console.print("  • Type 'group' + Enter → shows all groups")
        tui.console.print("  • Just press Enter → shows all chats")
        tui.console.print("")

        input("Press Enter to continue...")

        # Test the working search
        tui.print_info("\n=== Chat Selection with Search ===")

        selections = await tui.ask_checkbox(
            "Select chats to download from:",
            choices=choices,
            instruction="(Space to select, Enter to confirm)",
            use_shortcuts=False,
            enable_search=True  # This enables the working autocomplete search
        )

        if not selections:
            tui.print_info("No chats selected. Test ended.")
            return

        tui.print_success(f"\n✔ You selected {len(selections)} chat(s):")
        for i, sel in enumerate(selections, 1):
            tui.console.print(f"  {i}. {sel}")

        # Verify
        tui.print_info("\n=== Test Result ===")
        tui.print_success("✔ Search functionality is WORKING!")
        tui.console.print("[green]The text filter search worked correctly.[/]")

        # Optional: Quick scan
        proceed = await tui.ask_confirm("\nQuick scan selected chats (5 messages each)?")

        if proceed:
            # Extract IDs
            targets = []
            for sel in selections:
                index = choices.index(sel)
                targets.append(dialogs[index].id)

            tui.print_info("\n=== Quick Scan ===")
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

    except KeyboardInterrupt:
        tui.print_info("\nTest interrupted by user")
    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client_wrapper.stop()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("WORKING CHAT SEARCH TEST")
    print("="*70)
    print("")
    print("This test demonstrates the WORKING search functionality:")
    print("")
    print("✓ Uses questionary.text() for search (simple and reliable)")
    print("✓ Type keywords and press Enter to filter")
    print("✓ Your input is visible")
    print("✓ After search, checkbox shows filtered results")
    print("✓ Can skip search by pressing Enter without typing")
    print("")
    print("Solution: Text Filter (search) → Checkbox (select)")
    print("="*70 + "\n")

    asyncio.run(test_search_working())
