from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "services" / "ai-worker" / "src"))

from story_platform_ai.health import health_payload


class WorkerSmokeTests(unittest.TestCase):
    def test_health_payload_is_stable(self) -> None:
        self.assertEqual(
            health_payload(),
            {"status": "ok", "service": "ai-worker", "version": "0.1.0"},
        )
