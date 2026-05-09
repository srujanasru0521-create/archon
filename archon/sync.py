"""File watching and incremental indexing."""

import hashlib
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

from .rag import CodeRAG

logger = logging.getLogger(__name__)


class ChangeDetector:
    """Detect file changes by content hash."""

    def __init__(self):
        self.file_hashes = {}

    def compute_hash(self, file_path: Path) -> str:
        """SHA256 of file content."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Error computing hash for {file_path}: {e}")
            return ""

    def has_changed(self, file_path: Path) -> bool:
        """Check if file changed since last index."""
        current_hash = self.compute_hash(file_path)

        if not current_hash:
            return False

        if file_path not in self.file_hashes:
            self.file_hashes[file_path] = current_hash
            return True

        if self.file_hashes[file_path] != current_hash:
            self.file_hashes[file_path] = current_hash
            return True

        return False


class CodeWatcher(FileSystemEventHandler):
    """Watch for code changes."""

    def __init__(self, on_change_callback):
        self.on_change = on_change_callback
        self.debounce_timers = {}

    def on_modified(self, event):
        """Handle file modification with debouncing."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix != '.py':
            return

        # Debounce rapid changes
        if file_path in self.debounce_timers:
            return

        self.debounce_timers[file_path] = True

        def trigger():
            time.sleep(1)
            try:
                self.on_change(file_path)
            finally:
                del self.debounce_timers[file_path]

        thread = threading.Thread(target=trigger, daemon=True)
        thread.start()


class FileWatcher:
    """Watch repository for changes and sync index."""

    def __init__(self, rag_engine: CodeRAG):
        self.rag = rag_engine
        self.detector = ChangeDetector()
        self.observer = None

    def start(self, repo_path: Path):
        """Start watching repository."""
        def on_change(file_path: Path):
            if self.detector.has_changed(file_path):
                logger.info(f"[SYNC] Change detected in {file_path}")
                try:
                    self.rag.index_file(file_path)
                except Exception as e:
                    logger.error(f"Error reindexing {file_path}: {e}")

        handler = CodeWatcher(on_change)
        self.observer = Observer()
        self.observer.schedule(handler, path=str(repo_path), recursive=True)
        self.observer.start()

        logger.info(f"[WATCH] Monitoring {repo_path} for changes. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping watcher...")
            self.observer.stop()

        self.observer.join()
