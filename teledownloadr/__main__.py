import asyncio
import signal
import re
import os
from teledownloadr.core.client import TelegramClient
from teledownloadr.core.downloader import Downloader
from teledownloadr.utils.display import tui

def save_scan_results_to_file(chat_title: str, chat_id: str, file_list: list, count: int, total_size: int) -> bool:
    """
    Saves scan results to a text file.
    Returns True on success, False on failure.
    Handles all exceptions gracefully.
    """
    try:
        # Sanitize chat title for filename (remove special characters)
        sanitized_title = re.sub(r'[^\w\s-]', '', chat_title)
        sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title).strip('_')

        # Ensure we have a valid filename
        if not sanitized_title:
            sanitized_title = "Unknown_Chat"

        filename = f"{sanitized_title}_{chat_id}.txt"

        # Create file with scan results
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Scan Results for {chat_title} ({chat_id})\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total Files: {count}\n")
            size_gb = total_size / (1024 ** 3)
            size_mb = total_size / (1024 ** 2)
            f.write(f"Total Size: {size_mb:.2f} MB ({size_gb:.4f} GB)\n")
            f.write("=" * 60 + "\n\n")

            for file_info in file_list:
                try:
                    size_mb = file_info.get('size', 0) / (1024 * 1024)
                    date_str = file_info.get('date', 'Unknown')
                    file_type = file_info.get('type', 'Unknown')
                    file_name = file_info.get('filename', 'Unknown')

                    f.write(f"[{date_str}] [{file_type}] {file_name} ({size_mb:.2f} MB)\n")
                except Exception as file_error:
                    # Skip this file if there's an error, but continue with others
                    f.write(f"[Error processing file entry: {str(file_error)[:40]}]\n")
                    continue

        # Verify file was created
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            tui.print_success(f"✔ Saved metadata to {filename}")
            return True
        else:
            tui.print_error(f"✗ Failed to create {filename}")
            return False

    except OSError as e:
        tui.print_error(f"✗ File system error: {str(e)[:50]}")
        return False
    except Exception as e:
        tui.print_error(f"✗ Failed to save scan results: {str(e)[:50]}")
        return False

async def main():
    shutdown_event = asyncio.Event()

    # Get the current event loop
    loop = asyncio.get_running_loop()

    # Define signal handler that works with asyncio
    def handle_shutdown():
        """Handle Ctrl+C and other termination signals"""
        print("\n\n🛑 Shutdown signal received. Cancelling downloads...")
        shutdown_event.set()

    # Register signal handlers for graceful shutdown (asyncio-aware)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)

    tui.print_banner()

    # Initialize Client
    client_wrapper = TelegramClient()
    try:
        app = await client_wrapper.start()
    except Exception as e:
        tui.print_error(f"Failed to start client: {e}")
        return

    downloader = Downloader(app, shutdown_event=shutdown_event)
    
    try:
        while True:
            # Check for shutdown signal
            if shutdown_event.is_set():
                tui.print_info("Shutdown requested. Exiting...")
                break

            dialogs = [] # Initialize here to avoid UnboundLocalError
            action = await tui.ask_choice(
                "What would you like to do?",
                choices=[
                    "List Chats",
                    "Enter Chat ID/Username Manually",
                    "Exit"
                ]
            )

            targets = []

            if action == "Exit":
                break
                
            elif action == "List Chats":
                limit_str = await tui.ask_text("How many chats to list? (Higher = better search)", default="500")
                if not limit_str.isdigit():
                    tui.print_error("Invalid number.")
                    continue

                limit = int(limit_str)
                dialogs, choices = await downloader.list_dialogs(limit=limit)

                if not choices:
                    tui.print_info("No chats found.")
                    continue

                # Use search-enabled checkbox for better UX with many chats
                selections = await tui.ask_checkbox(
                    "Select chats to download from:",
                    choices=choices,
                    instruction="(Space to select, Enter to confirm)",
                    use_shortcuts=False,
                    enable_search=True  # Enable autocomplete search for large lists
                )
                if not selections:
                    tui.print_error("No chats selected!")
                    continue
                
                # Extract IDs
                targets = []
                for sel in selections:
                     index = choices.index(sel)
                     targets.append(dialogs[index].id)
                
                # We have a list of targets

            elif action == "Enter Chat ID/Username Manually":
                raw = await tui.ask_text("Enter Chat ID or Username:")
                if raw:
                    targets = [raw]
                else:
                    continue

            # Configure each target
            if targets:
                configs = []
                for target_id in targets:
                    # Resolve name for display
                    chat_name = str(target_id)
                    for d in dialogs:
                        if d.id == target_id:
                            chat_name = d.title or d.first_name or str(target_id)
                            break
                            
                    tui.print_info(f"Configuring settings for: [bold]{chat_name}[/]")
                    
                    limit_str = await tui.ask_text(f"  Max messages to check for {chat_name}? (Enter 0 or All for entire history)", default="10")
                    if limit_str.lower() in ["all", "0"]:
                        limit = 0
                    elif limit_str.isdigit():
                        limit = int(limit_str)
                    else:
                        limit = 10
                    
                    media_choice = await tui.ask_choice(
                        f"  Media type for {chat_name}?",
                        choices=["All", "Videos Only", "Photos Only"]
                    )
                    
                    media_types = None
                    if media_choice == "Videos Only":
                        media_types = ['video']
                    elif media_choice == "Photos Only":
                        media_types = ['photo']
                        
                    configs.append({
                        'chat_id': target_id,
                        'limit': limit,
                        'media_types': media_types
                    })
                    tui.print_success(f"  Saved config for {chat_name}")
                
                if len(configs) > 0:
                    # Scan phase: preview files before downloading
                    tui.print_info("\n=== Scanning Phase ===")
                    scan_results = []

                    for config in configs:
                        chat_id = config['chat_id']
                        limit = config.get('limit', 10)
                        media_types = config.get('media_types')

                        # Scan the chat with smart resume checking
                        file_list, count, total_size, chat_title, existing_count, new_count = await downloader.scan_chat(
                            chat_id,
                            limit=limit,
                            media_types=media_types,
                            check_existing=True
                        )

                        scan_results.append({
                            'config': config,
                            'file_list': file_list,
                            'count': count,
                            'total_size': total_size,
                            'chat_title': chat_title,
                            'chat_id': chat_id,
                            'existing_count': existing_count,
                            'new_count': new_count
                        })

                    # Show summary
                    tui.print_info("\n=== Scan Summary ===")
                    total_files = sum(r['count'] for r in scan_results)
                    total_existing = sum(r['existing_count'] for r in scan_results)
                    total_new = sum(r['new_count'] for r in scan_results)
                    total_bytes = sum(r['total_size'] for r in scan_results)
                    total_gb = total_bytes / (1024 ** 3)

                    tui.console.print(f"[bold]Found {total_files} files ({total_existing} existing, {total_new} new). Total Size: ~{total_gb:.2f} GB[/]")

                    # Ask if user wants to save scan results
                    if total_files > 0:
                        save_scan = await tui.ask_confirm("Save scan results to file?")

                        if save_scan:
                            saved_count = 0
                            for result in scan_results:
                                if result['count'] > 0:
                                    success = save_scan_results_to_file(
                                        chat_title=result['chat_title'],
                                        chat_id=str(result['chat_id']),
                                        file_list=result['file_list'],
                                        count=result['count'],
                                        total_size=result['total_size']
                                    )
                                    if success:
                                        saved_count += 1

                            tui.print_info(f"Saved {saved_count} of {len([r for r in scan_results if r['count'] > 0])} scan result files")

                    # Confirmation
                    proceed = await tui.ask_confirm("Proceed with download?")

                    if proceed:
                        # Ask for concurrency
                        concurrency_str = await tui.ask_text("How many parallel downloads per chat? (1-10)", default="5")
                        try:
                            concurrency = int(concurrency_str)
                            if concurrency < 1: concurrency = 1
                            if concurrency > 20: concurrency = 20
                        except:
                            concurrency = 5

                        tui.print_info(f"\n=== Download Phase (Concurrency: {concurrency}) ===")
                        
                        # Update configs with concurrency if I were passing it in config, 
                        # but download_multiple_chats takes configs list.
                        # I need to pass it to download_multiple_chats or update calls inside it.
                        # Actually, download_multiple_chats calls download_from_chat. 
                        # I should probably pass 'concurrent_downloads' to download_multiple_chats 
                        # and have it pass it down.
                        
                        await downloader.download_multiple_chats(configs, concurrent_downloads=concurrency)
                    else:
                        tui.print_info("Download cancelled by user.")
                
                if not await tui.ask_confirm("Download from another chat?"):
                    break

    except KeyboardInterrupt:
        tui.print_info("\nShutdown requested via Ctrl+C")
        shutdown_event.set()
    except Exception as e:
        tui.print_error(f"An unexpected error occurred: {e}")
    finally:
        if shutdown_event.is_set():
            tui.print_info("Cleaning up and closing connections...")
        await client_wrapper.stop()
        tui.print_success("Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
