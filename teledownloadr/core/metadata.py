import json
import os
from datetime import datetime
from teledownloadr.config.settings import DOWNLOAD_DIR

class MetadataManager:
    """
    Manages download metadata tracking for resume capability.
    Stores history of downloaded files in JSON format.
    """

    def __init__(self, chat_id: str):
        """
        Initialize metadata manager for a specific chat.

        Args:
            chat_id: The chat ID to manage metadata for
        """
        self.chat_id = str(chat_id)
        self.metadata_file = os.path.join(DOWNLOAD_DIR, f"{self.chat_id}_history.json")
        self.history = {}
        self.load_history()

    def load_history(self) -> dict:
        """
        Load download history from JSON file.
        Returns empty dict if file doesn't exist or is corrupted.
        """
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)

                    # Validate structure
                    if not isinstance(self.history, dict):
                        self.history = {}

            return self.history
        except json.JSONDecodeError:
            # Corrupted JSON file, start fresh
            self.history = {}
            return {}
        except Exception as e:
            # Any other error, start fresh
            self.history = {}
            return {}

    def update_entry(self, filename: str, file_size: int, media_type: str, status: str = "downloaded"):
        """
        Update or add an entry to the download history.

        Args:
            filename: Name of the downloaded file
            file_size: Size of the file in bytes
            media_type: Type of media (photo, video, etc.)
            status: Download status (downloaded, failed, skipped)
        """
        try:
            self.history[filename] = {
                'size': file_size,
                'type': media_type,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'chat_id': self.chat_id
            }
        except Exception:
            # If update fails, just skip it
            pass

    def save_history(self) -> bool:
        """
        Save download history to JSON file.
        Returns True on success, False on failure.
        """
        try:
            # Ensure download directory exists
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)

            return True
        except OSError:
            # Filesystem error (disk full, permission denied, etc.)
            return False
        except Exception:
            # Any other error
            return False

    def is_downloaded(self, filename: str, file_size: int) -> bool:
        """
        Check if a file was previously downloaded successfully.

        Args:
            filename: Name of the file to check
            file_size: Expected file size in bytes

        Returns:
            True if file exists in history with matching size and on disk
        """
        try:
            # Check metadata history
            if filename not in self.history:
                return False

            entry = self.history.get(filename, {})

            # Check if status was successful
            if entry.get('status') != 'downloaded':
                return False

            # Check if size matches
            if entry.get('size') != file_size:
                return False

            # Verify file actually exists on disk
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if not os.path.exists(file_path):
                return False

            # Verify disk file size matches
            disk_size = os.path.getsize(file_path)
            if disk_size != file_size:
                return False

            return True

        except Exception:
            # On any error, assume not downloaded
            return False

    def get_stats(self) -> dict:
        """
        Get statistics about download history.

        Returns:
            Dict with counts of downloaded, failed, skipped files
        """
        try:
            stats = {
                'downloaded': 0,
                'failed': 0,
                'skipped': 0,
                'total': len(self.history)
            }

            for entry in self.history.values():
                status = entry.get('status', 'unknown')
                if status in stats:
                    stats[status] += 1

            return stats
        except Exception:
            return {'downloaded': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    def clear_history(self):
        """Clear all download history."""
        self.history = {}

    def remove_entry(self, filename: str) -> bool:
        """
        Remove a file entry from history.

        Args:
            filename: Name of the file to remove

        Returns:
            True if removed, False if not found
        """
        try:
            if filename in self.history:
                del self.history[filename]
                return True
            return False
        except Exception:
            return False
