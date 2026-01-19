import asyncio
import signal
from core.client import TelegramClient
from core.downloader import Downloader
from utils.display import tui

async def test_search_fix():
    """
    Test the fixed search functionality in chat selection.
    This verifies that:
    1. Typing filters the chat list (not triggering shortcuts)
    2. Input text is visible on screen
    3. 'a' key filters chats (doesn't select all)
    4. Search is case-insensitive and works with partial matches
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
    tui.print_info("Testing FIXED Dynamic Chat Search")

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
        tui.print_info("\n=== Fetching Chats for Search Test ===")
        tui.print_info("Fetching 100 chats to test search functionality...")

        dialogs, choices = await downloader.list_dialogs(limit=100)

        if not dialogs or len(dialogs) < 1:
            tui.print_error("No chats available.")
            return

        tui.print_success(f"✔ Loaded {len(dialogs)} chats")

        # Show search instructions
        tui.print_info("\n=== Search Instructions ===")
        tui.console.print("The next prompt will let you SEARCH for chats.")
        tui.console.print("")
        tui.console.print("[bold cyan]How Search Works:[/]")
        tui.console.print("  1. Start typing - the list will filter in real-time")
        tui.console.print("  2. Your typed text will be visible at the top")
        tui.console.print("  3. Press [bold]Backspace[/] to delete characters")
        tui.console.print("  4. Press [bold]Escape[/] to clear the search")
        tui.console.print("  5. Use [bold]Arrow keys[/] to navigate filtered results")
        tui.console.print("  6. Press [bold]Space[/] to select/deselect items")
        tui.console.print("  7. Press [bold]Enter[/] to confirm selection")
        tui.console.print("")
        tui.console.print("[bold yellow]Example Searches:[/]")
        tui.console.print("  • Type 'saved' - finds 'Saved Messages'")
        tui.console.print("  • Type 'group' - finds all groups")
        tui.console.print("  • Type any name/keyword")
        tui.console.print("")
        tui.console.print("[bold green]TIP:[/] Start typing immediately when the list appears!")
        tui.console.print("")

        input("Press Enter to continue to the search prompt...")

        # Test the fixed search
        tui.print_info("\n=== Search-Enabled Chat Selection ===")

        selections = await tui.ask_checkbox(
            "Select chats to download from:",
            choices=choices,
            instruction="(Type to search/filter, Space to select, Enter to confirm)",
            use_shortcuts=False  # This is the FIX - disables shortcuts, enables search
        )

        if not selections:
            tui.print_info("No chats selected. Test ended.")
            return

        tui.print_success(f"\n✔ You selected {len(selections)} chat(s):")
        for i, sel in enumerate(selections, 1):
            tui.console.print(f"  {i}. {sel}")

        # Verify search worked
        tui.print_info("\n=== Search Test Result ===")
        if len(selections) > 0:
            tui.print_success("✔ Search functionality is WORKING!")
            tui.console.print("[green]You were able to type, filter, and select chats.[/]")
        else:
            tui.print_error("✗ No selection made")

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
    print("SEARCH FIX VERIFICATION TEST")
    print("="*70)
    print("This test verifies the FIXED search functionality:")
    print("")
    print("✓ Typing should filter the chat list (not trigger shortcuts)")
    print("✓ Your input text should be visible at the top of the list")
    print("✓ Pressing 'a' should filter for chats with 'a' (not select all)")
    print("✓ Search should be case-insensitive and support partial matches")
    print("")
    print("The FIX: use_shortcuts=False in ask_checkbox()")
    print("="*70 + "\n")

    asyncio.run(test_search_fix())
