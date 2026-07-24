"""Command-line interface for the static blog builder."""

import argparse
import logging

from .builder import build_site, clean_outputs


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the static LaTeX blog.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show command-level build diagnostics",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="render all posts into site/")
    commands.add_parser("clean", help="remove generated site/, build/, and logs/")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    try:
        if args.command == "build":
            build_site()
        elif args.command == "clean":
            clean_outputs()
    except (OSError, RuntimeError) as error:
        logging.getLogger(__name__).error("%s", error)
        return 1
    return 0
