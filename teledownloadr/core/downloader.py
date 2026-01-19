import os
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from teledownloadr.config.settings import DOWNLOAD_DIR
from teledownloadr.utils.display import tui

class Downloader:
    def __init__(self, client: Client, shutdown_event: asyncio.Event = None):
        self.client = client
        self.shutdown_event = shutdown_event or asyncio.Event()

    async def download_media(self, message: Message, progress_task_id=None, progress_object=None, description_prefix=""):
        """
        Downloads media from a single message with retries.
        Uses rich progress bar if progress_object and progress_task_id are provided.
        Returns: True if downloaded/skipped successfully, False if failed after retries
        """
        if not message.media:
            return False

        # Determine file name
        file_name = self._get_file_name(message)
        file_path = os.path.join(DOWNLOAD_DIR, file_name)

        # Check if file exists and is complete
        remote_size = self._get_file_size(message)
        if os.path.exists(file_path):
            local_size = os.path.getsize(file_path)
            if remote_size and local_size == remote_size:
                if progress_object and progress_task_id is not None:
                     progress_object.update(progress_task_id, description=f"{description_prefix}[green]Skipped (exists) {file_name}", completed=remote_size, total=remote_size)
                await asyncio.sleep(0.1)  # Brief pause to show message
                return True
            else:
                if progress_object and progress_task_id is not None:
                    progress_object.update(progress_task_id, description=f"{description_prefix}[yellow]Redownloading {file_name}")
                os.remove(file_path)

        # Callback for Pyrogram
        async def progress_callback(current, total):
            if progress_object and progress_task_id is not None:
                progress_object.update(progress_task_id, completed=current, total=total)

        # Retry loop
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if progress_object and progress_task_id is not None:
                     progress_object.update(progress_task_id, description=f"{description_prefix}Downloading {file_name}", total=remote_size)

                await self.client.download_media(
                    message,
                    file_name=file_path,
                    progress=progress_callback
                )

                if progress_object and progress_task_id is not None:
                     progress_object.update(progress_task_id, description=f"{description_prefix}[green]Downloaded {file_name}")
                await asyncio.sleep(0.1)  # Brief pause to show message
                return True  # Success
            except Exception as e:
                if progress_object and progress_task_id is not None:
                    # Shorten error message to fit
                    error_msg = str(e).split('\n')[0][:20]
                    progress_object.update(progress_task_id, description=f"{description_prefix}[red]Error {file_name}: {error_msg} (Retry {attempt+1})")

                if attempt < max_retries - 1:
                    # Check for shutdown signal before retry sleep
                    if self.shutdown_event.is_set():
                        if progress_object and progress_task_id is not None:
                            progress_object.update(progress_task_id, description=f"{description_prefix}[yellow]Cancelled")
                        # Clean up partial file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return False
                    await asyncio.sleep(5)
                else:
                    if progress_object and progress_task_id is not None:
                         progress_object.update(progress_task_id, description=f"{description_prefix}[bold red]Failed {file_name}")
                    # Clean up partial file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return False  # Failed after all retries

    def _get_file_size(self, message: Message) -> int:
        if message.video: return message.video.file_size
        if message.document: return message.document.file_size
        if message.photo: return message.photo.file_size
        if message.audio: return message.audio.file_size
        if message.animation: return message.animation.file_size
        if message.voice: return message.voice.file_size
        if message.video_note: return message.video_note.file_size
        if message.sticker: return message.sticker.file_size
        return 0

    def _get_file_name(self, message: Message) -> str:
        """
        Helper to extract or generate a filename.
        """
        if message.video:
            return message.video.file_name or f"video_{message.id}.mp4"
        elif message.document:
            return message.document.file_name or f"doc_{message.id}"
        elif message.photo:
            return f"photo_{message.id}.jpg"
        elif message.audio:
            return message.audio.file_name or f"audio_{message.id}.mp3"
        elif message.animation:
            return message.animation.file_name or f"animation_{message.id}.mp4"
        elif message.voice:
            return f"voice_{message.id}.ogg"
        elif message.video_note:
            return f"videonote_{message.id}.mp4"
        elif message.sticker:
            return f"sticker_{message.id}.webp"
        else:
            return f"unknown_{message.id}_{message.media}"

    async def scan_chat(self, chat_id: str, limit: int = 10, media_types: list = None, check_existing: bool = True):
        """
        Scans chat history without downloading.
        Returns: (file_list, total_count, total_size, chat_title, existing_count, new_count)
        file_list: List of dicts with file info [{date, type, filename, size, exists}, ...]
        total_count: Total number of files found
        total_size: Total size in bytes
        chat_title: Resolved chat title/name
        existing_count: Number of files already downloaded
        new_count: Number of new files to download
        """
        tui.print_info(f"Scanning messages from chat (Limit: {'All' if limit == 0 else limit})...")

        # Resolve chat title
        chat_title = str(chat_id)
        try:
            chat = await self.client.get_chat(chat_id)
            chat_title = chat.title or chat.first_name or str(chat_id)
        except:
            pass

        tui.print_info(f"Chat: {chat_title}")

        # Load metadata for this chat
        from teledownloadr.core.metadata import MetadataManager
        metadata = MetadataManager(chat_id) if check_existing else None

        file_list = []
        total_count = 0
        total_size = 0
        existing_count = 0
        new_count = 0

        try:
            async for message in self.client.get_chat_history(chat_id, limit=limit):
                # Check for shutdown
                if self.shutdown_event.is_set():
                    tui.print_info("Scan cancelled by user")
                    break

                if not message.media:
                    continue

                # Filter by media type
                if media_types:
                    if message.media.value not in media_types:
                        continue

                # Extract file info
                file_name = self._get_file_name(message)
                file_size = self._get_file_size(message)
                media_type = message.media.value
                date_str = message.date.strftime("%Y-%m-%d %H:%M") if message.date else "Unknown"

                # Check if file already exists
                exists = False
                if check_existing and metadata:
                    file_path = os.path.join(DOWNLOAD_DIR, file_name)
                    exists = os.path.exists(file_path) and os.path.getsize(file_path) == file_size

                # Add to list
                file_list.append({
                    'date': date_str,
                    'type': media_type,
                    'filename': file_name,
                    'size': file_size,
                    'exists': exists
                })

                total_count += 1
                total_size += file_size

                if exists:
                    existing_count += 1
                else:
                    new_count += 1

                # Print each file with status indicator
                size_mb = file_size / (1024 * 1024)
                if exists:
                    tui.console.print(f"  • [{date_str}] [{media_type}] [green][Existing][/green] {file_name} ({size_mb:.2f} MB)")
                else:
                    tui.console.print(f"  • [{date_str}] [{media_type}] [white][New][/white] {file_name} ({size_mb:.2f} MB)")

        except Exception as e:
            tui.print_error(f"Error scanning chat: {e}")
            return [], 0, 0, chat_title, 0, 0

        return file_list, total_count, total_size, chat_title, existing_count, new_count

    async def download_from_chat(self, chat_id: str, limit: int = 10, media_types: list = None, 
                                 progress=None, task_id=None, use_metadata: bool = True,
                                 concurrent_downloads: int = 5):
        """
        Iterates through chat history and downloads media.
        Uses MetadataManager to track downloads and skip existing files.
        Supports parallel downloads with `concurrent_downloads`.
        """
        if not progress:
            tui.print_info(f"Fetching messages from {chat_id} (Limit: {'All' if limit == 0 else limit})...")
            tui.print_info(f"Parallel downloads: {concurrent_downloads}")

        # Resolve chat ID to title for display if possible, otherwise use ID
        chat_title = str(chat_id)
        try:
             chat = await self.client.get_chat(chat_id)
             chat_title = chat.title or chat.first_name or str(chat_id)
        except:
             pass

        # Initialize MetadataManager
        from teledownloadr.core.metadata import MetadataManager
        metadata = MetadataManager(chat_id) if use_metadata else None

        if progress and task_id:
            progress.update(task_id, description=f"[{chat_title}] Starting...", completed=0, total=None)

        # For self-managed progress (single chat mode)
        local_progress = None
        if not progress:
            local_progress = tui.create_progress()
            local_progress.start()
            task_id = local_progress.add_task(f"[{chat_title}] Starting...", total=None)
            progress = local_progress

        # Stats containers (mutable for closure access)
        stats = {
            'count': 0,
            'skipped': 0,
            'downloaded': 0,
            'failed': 0
        }

        # Concurrency control
        semaphore = asyncio.Semaphore(concurrent_downloads)
        active_tasks = set()

        async def _process_message(message, current_count):
            async with semaphore:
                # Determine task ID for this download
                download_task_id = task_id
                ephemeral_task = False

                try:
                    # Check for shutdown signal inside worker
                    if self.shutdown_event.is_set():
                        return

                    if not message.media:
                        return

                    if media_types and message.media.value not in media_types:
                        return

                    file_name = self._get_file_name(message)
                    file_size = self._get_file_size(message)
                    media_type = message.media.value
                    
                    # Estimate total for display
                    total_display = limit if limit > 0 else "?"
                    prefix = f"[{chat_title}] ({current_count}/{total_display}) "

                    # Check if file was already downloaded using metadata
                    if metadata and metadata.is_downloaded(file_name, file_size):
                        stats['skipped'] += 1
                        # Only show skipped message on main bar if not busy, or log it?
                        # In parallel mode, too many updates might flood. 
                        # Let's just update the count on the main bar text if possible, 
                        # or show a quick status.
                        if progress and task_id:
                             progress.update(task_id, description=f"{prefix}Skipping {file_name}")
                        return

                    # Prepare progress bar
                    if concurrent_downloads > 1 and progress:
                        # Create ephemeral task for this specific file
                        download_task_id = progress.add_task(f"Downloading {file_name}", total=file_size, visible=True)
                        ephemeral_task = True
                        current_prefix = "" # No prefix needed for individual bar
                        
                        # Update main bar to show we are processing this index
                        if task_id:
                            progress.update(task_id, description=f"{prefix}Downloading metadata...")
                    else:
                        current_prefix = prefix
                        if progress and task_id:
                            progress.update(task_id, description=f"{current_prefix}Processing {file_name}", completed=0, total=None)

                    success = await self.download_media(
                        message,
                        progress_task_id=download_task_id,
                        progress_object=progress,
                        description_prefix=current_prefix
                    )

                    # Update metadata & stats
                    if metadata:
                        if success:
                            metadata.update_entry(file_name, file_size, media_type, "downloaded")
                            stats['downloaded'] += 1
                        else:
                            metadata.update_entry(file_name, file_size, media_type, "failed")
                            stats['failed'] += 1
                        
                        # Periodic save (check safely)
                        total_processed = stats['downloaded'] + stats['failed'] + stats['skipped']
                        if total_processed % 20 == 0:
                            try:
                                metadata.save_history()
                            except Exception:
                                pass # Don't crash on save failure
                    else:
                        if success:
                            stats['downloaded'] += 1
                        else:
                            stats['failed'] += 1

                except Exception as msg_error:
                    stats['failed'] += 1
                    error_msg = str(msg_error).split('\n')[0][:40]
                    target_tid = download_task_id if (progress and download_task_id) else task_id
                    if progress and target_tid:
                        progress.update(target_tid, description=f"[red]Error msg {message.id}: {error_msg}")
                finally:
                    # Clean up ephemeral task
                    if ephemeral_task and progress:
                        progress.remove_task(download_task_id)
                        # Refresh main bar
                        if task_id:
                            progress.update(task_id, description=f"{prefix}Active")

        try:
            # Using async generator
            async for message in self.client.get_chat_history(chat_id, limit=limit):
                if self.shutdown_event.is_set():
                    if progress and task_id:
                        progress.update(task_id, description=f"[{chat_title}] Cancelled by user")
                    
                    # Cancel all active tasks immediately
                    tui.print_info(f"Paramount shutdown: Cancelling {len(active_tasks)} active downloads...")
                    for task in active_tasks:
                        task.cancel()
                    break
                
                # Check media type early to avoid creating useless tasks? 
                # Doing it inside worker keeps main loop fast, but creating task has overhead.
                # Let's do basic check here if possible, but message.media check is fast.
                if not message.media:
                    continue
                
                stats['count'] += 1
                
                # Create task
                task = asyncio.create_task(_process_message(message, stats['count']))
                active_tasks.add(task)
                task.add_done_callback(active_tasks.discard)

                # Flow control: Don't let queue grow indefinitely (memory protection)
                # If we scan faster than we download, tasks pile up.
                # Limit pending tasks to 2x or 3x concurrency.
                if len(active_tasks) >= concurrent_downloads * 3:
                     # Check shutdown again during wait
                    if self.shutdown_event.is_set():
                         for task in active_tasks:
                             task.cancel()
                         break
                    
                    # Wait for at least one task to finish
                    done, pending = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
                    # Check for exceptions in done tasks? 
                    # They are handled in _process_message but we should let loop continue.

            # Wait for remaining tasks to complete (or cancel them if shutdown)
            if active_tasks:
                if self.shutdown_event.is_set():
                    # If we broke out due to shutdown, ensure they are really cancelled
                    for task in active_tasks:
                        task.cancel()
                    if progress and task_id:
                        progress.update(task_id, description=f"[{chat_title}] Stopping downloads...")
                    await asyncio.gather(*active_tasks, return_exceptions=True)
                else:
                    if progress and task_id:
                        progress.update(task_id, description=f"[{chat_title}] Finishing remaining downloads...")
                    await asyncio.gather(*active_tasks, return_exceptions=True)

            # Final Save
            if metadata:
                try:
                    metadata.save_history()
                except Exception:
                    pass

            # Summary
            summary_parts = []
            if stats['downloaded'] > 0:
                summary_parts.append(f"{stats['downloaded']} downloaded")
            if stats['skipped'] > 0:
                summary_parts.append(f"{stats['skipped']} skipped")
            if stats['failed'] > 0:
                summary_parts.append(f"{stats['failed']} failed")

            if stats['downloaded'] == 0 and stats['failed'] == 0 and stats['skipped'] == 0:
                 if progress and task_id:
                     progress.update(task_id, description=f"[{chat_title}] No media found.", completed=100, total=100)
                 elif not progress:
                     tui.print_info("No media found.")
            else:
                summary = ", ".join(summary_parts)
                progress.update(task_id, description=f"[{chat_title}] Done! ({summary})", completed=100, total=100)

        except Exception as e:
            if progress and task_id:
                progress.update(task_id, description=f"[{chat_title}] Error: {e}")
            else:
                tui.print_error(f"Error downloading from {chat_id}: {e}")
        finally:
            if local_progress:
                local_progress.stop()

    async def download_multiple_chats(self, chat_configs: list[dict], concurrent_downloads: int = 5):
        tui.print_info(f"Starting parallel download for {len(chat_configs)} chats...")

        with tui.create_progress() as progress:
            task_objects = []  # Store task objects for cancellation

            # Create a progress bar for each chat
            for config in chat_configs:
                chat_id = config['chat_id']
                limit = config.get('limit', 10)
                media_types = config.get('media_types')

                # Placeholder title until resolved
                task_id = progress.add_task(f"[Chat {chat_id}] Waiting...", total=None, visible=True)

                # Create task and store reference for cancellation
                task = asyncio.create_task(
                    self.download_from_chat(
                        chat_id,
                        limit=limit,
                        media_types=media_types,
                        progress=progress,
                        task_id=task_id,
                        concurrent_downloads=concurrent_downloads
                    )
                )
                task_objects.append(task)

            try:
                # Wait for all tasks with cancellation support
                await asyncio.gather(*task_objects, return_exceptions=True)
            except asyncio.CancelledError:
                # Cancel all running tasks
                for task in task_objects:
                    if not task.done():
                        task.cancel()
                # Wait for cancellation to complete
                await asyncio.gather(*task_objects, return_exceptions=True)
                tui.print_info("All downloads cancelled")

    async def list_dialogs(self, limit: int = 50):
        """
        Lists dialogs returning a list of dicts for questionary.
        """
        from rich.table import Table

        tui.print_info(f"Fetching last {limit} active chats...")
        
        dialogs = []
        choices = []
        
        async for dialog in self.client.get_dialogs(limit=limit):
            chat = dialog.chat
            title = chat.title or chat.first_name or "Unknown"
            dialogs.append(chat)
            choices.append(f"{title} ({chat.id})")
            
        return dialogs, choices

