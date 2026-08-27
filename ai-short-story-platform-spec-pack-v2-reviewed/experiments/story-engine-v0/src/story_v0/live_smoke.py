"""Run one secret-safe live OpenRouter smoke request."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from .live_openrouter import OpenRouterProvider, OpenRouterConfig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path("F:/Son/tool/NovelWriter/env.txt"),
    )
    args = parser.parse_args(argv)
    config = OpenRouterConfig.from_environment(args.env_file)
    response = OpenRouterProvider(config).chat(
        [
            {
                "role": "system",
                "content": "You are a connectivity check. Reply with exactly the word READY.",
            },
            {"role": "user", "content": "Return the connectivity check response."},
        ],
        max_tokens=16,
        temperature=0,
    )
    digest = hashlib.sha256(response.text.encode("utf-8")).hexdigest()[:12]
    print(
        f"openrouter_ok model={config.model} key_count={config.key_count} "
        f"response_chars={len(response.text)} "
        f"response_sha256={digest} input_tokens={response.usage.input_tokens} "
        f"output_tokens={response.usage.output_tokens}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
