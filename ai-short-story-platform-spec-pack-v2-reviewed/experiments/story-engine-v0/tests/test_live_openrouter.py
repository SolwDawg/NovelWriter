import tempfile
import unittest
from pathlib import Path

from story_v0.live_openrouter import (
    OpenRouterConfig,
    OpenRouterProvider,
    OpenRouterRequestError,
    OpenRouterResponse,
)
from story_v0.contracts import Usage


class OpenRouterConfigTests(unittest.TestCase):
    def test_reads_two_raw_keys_and_model_without_echoing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "env.txt"
            env_file.write_text(
                "sk-or-test-key-one\nmodel: minimax/minimax-m3:free\n"
                "sk-or-test-key-two\n",
                encoding="utf-8",
            )
            config = OpenRouterConfig.from_environment(env_file)
        self.assertEqual(config.model, "minimax/minimax-m3:free")
        self.assertEqual(config.key_count, 2)

    def test_rotates_to_next_key_once_after_rate_limit(self):
        config = OpenRouterConfig(
            api_key="sk-or-test-key-one",
            api_keys=("sk-or-test-key-one", "sk-or-test-key-two"),
            model="minimax/minimax-m3:free",
        )
        provider = OpenRouterProvider(config, cooldown_seconds=30)
        seen_slots = []

        def fake_request(body, headers, key_slot):
            seen_slots.append(key_slot)
            if key_slot == 0:
                raise OpenRouterRequestError("OpenRouter HTTP 429", status_code=429)
            return OpenRouterResponse("READY", Usage(output_tokens=1))

        provider._request_once = fake_request
        response = provider.chat(
            [{"role": "user", "content": "ping"}],
            max_tokens=4,
            temperature=0,
        )
        self.assertEqual(response.text, "READY")
        self.assertEqual(seen_slots, [0, 1])

