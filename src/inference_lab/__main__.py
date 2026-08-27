from __future__ import annotations

import argparse
import json

from .metrics import RequestTiming


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate latency metrics for one streamed LLM request."
    )
    parser.add_argument("--started-at", type=float, required=True)
    parser.add_argument("--first-token-at", type=float, required=True)
    parser.add_argument("--completed-at", type=float, required=True)
    parser.add_argument("--output-tokens", type=int, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    timing = RequestTiming(
        started_at_s=args.started_at,
        first_token_at_s=args.first_token_at,
        completed_at_s=args.completed_at,
        output_tokens=args.output_tokens,
    )
    print(json.dumps(timing.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
