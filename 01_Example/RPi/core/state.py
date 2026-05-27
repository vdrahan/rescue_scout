from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class SharedState:
    shutdown_requested: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)

    def mark_shutdown(self) -> bool:
        with self.lock:
            if self.shutdown_requested:
                return False
            self.shutdown_requested = True
            return True
