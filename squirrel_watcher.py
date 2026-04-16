"""
Watches Squirrel.md. On change, fires callback for each relevant new line.
Journal mode: only @squirrel: lines. Other modes: all new lines.
"""
from pathlib import Path
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEventHandler


class _Handler(FileSystemEventHandler):
    def __init__(self, filepath, callback, state_fn):
        self._path = Path(filepath)
        self._callback = callback
        self._state_fn = state_fn
        self._last_size = self._path.stat().st_size if self._path.exists() else 0

    def on_modified(self, event):
        if not isinstance(event, FileModifiedEvent):
            return
        if Path(event.src_path).resolve() != self._path.resolve():
            return
        try:
            size = self._path.stat().st_size
            if size <= self._last_size:
                self._last_size = size
                return
            with open(self._path, encoding="utf-8") as f:
                f.seek(self._last_size)
                new_text = f.read()
            self._last_size = size
            mode = self._state_fn()
            for line in new_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if mode == "journal":
                    if "@squirrel:" in line.lower():
                        self._callback(line)
                else:
                    self._callback(line)
        except Exception as e:
            print(f"[watcher] error: {e}")


def start_watcher(filepath, callback, state_fn):
    handler = _Handler(filepath, callback, state_fn)
    obs = Observer()
    obs.schedule(handler, str(Path(filepath).parent), recursive=False)
    obs.start()
    return obs
