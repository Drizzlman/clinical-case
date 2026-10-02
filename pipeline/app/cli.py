"""Pipeline CLI: run extraction from raw text and optionally deliver to the backend.

Usage:
    python -m app.cli extract --input raw.txt [--client mock|vertex] [--out case.json] [--post]
    python -m app.cli harness --golden tests/golden --out report.json

``mock`` runs fully offline (deterministic fixtures); ``vertex`` is the production
path (Application Default Credentials). Errors never echo the raw input text.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.client.base import LLMClient
from app.client.factory import build_llm_client
from app.config import get_settings
from app.errors import PipelineError
from app.extract import extract_case
from app.harness.runner import main as harness_main
from app.input import build_input_source
from app.sink import CaseSink, HttpCaseSink, NullCaseSink

DEFAULT_GOLDEN_DIR = "tests/golden"


def run_extract(
    *,
    raw_text: str,
    client: LLMClient,
    sink: CaseSink,
    post: bool,
) -> dict[str, Any]:
    """Extract a case and optionally deliver it; returns the backend payload."""

    case = asyncio.run(extract_case(client, raw_text))
    payload = case.to_case_create()
    if post:
        sink.send(payload)
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli", description="Clinical case pipeline CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract", help="Extract a case from raw clinical text")
    extract.add_argument("--input", required=True, help="Path to raw text, or '-' for stdin")
    extract.add_argument("--client", choices=["mock", "vertex"], default=None,
                         help="Override LLM_CLIENT from the environment")
    extract.add_argument("--golden", default=DEFAULT_GOLDEN_DIR,
                         help="Fixtures directory used by the mock client")
    extract.add_argument("--out", default=None, help="Write the JSON payload to this file")
    extract.add_argument("--post", action="store_true",
                         help="POST the case to BACKEND_URL/cases")

    sub.add_parser("harness", help="Run the offline accuracy harness")

    return parser


def _run_extract_command(args: argparse.Namespace) -> int:
    try:
        settings = get_settings()
    except ValidationError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    client_name = args.client or settings.llm_client
    try:
        raw_text = build_input_source(args.input).read()
        client = build_llm_client(settings, name=client_name, golden_dir=Path(args.golden))
        sink: CaseSink = HttpCaseSink(settings.backend_url) if args.post else NullCaseSink()
        payload = run_extract(raw_text=raw_text, client=client, sink=sink, post=args.post)
    except PipelineError as exc:
        print(f"extraction failed: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; returns a process exit code."""

    parser = _build_parser()
    args, extras = parser.parse_known_args(argv)

    if args.command == "harness":
        rest = extras
        if rest and rest[0] == "--":
            rest = rest[1:]
        return harness_main(rest)

    if extras:
        parser.error(f"unrecognized arguments: {' '.join(extras)}")

    return _run_extract_command(args)


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
