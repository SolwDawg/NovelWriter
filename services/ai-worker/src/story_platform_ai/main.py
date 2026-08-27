from __future__ import annotations

import json
import signal
from threading import Event

from .health import health_payload


def main() -> None:
    stop = Event()

    def request_stop(_signum: int, _frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    print(
        "[ai-worker] startup shell ready "
        f"health={json.dumps(health_payload(), sort_keys=True)}",
        flush=True,
    )
    stop.wait()
    print("[ai-worker] stopped", flush=True)


if __name__ == "__main__":
    main()
