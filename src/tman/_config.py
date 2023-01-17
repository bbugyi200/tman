"""Contains this project's clack.Config classes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Literal, Sequence

import clack
from clack import xdg

from . import APP_NAME


Command = Literal["add", "start"]


class Config(clack.Config):
    """Command-line arguments."""

    command: Command

    # ----- CONFIG
    torrent_bucket: Path = (
        xdg.get_full_dir("data", APP_NAME) / "torrent_bucket.txt"
    )


@dataclass
class ValidateOptions:
    command: str
    good_output: str
    retries: int


class StartConfig(Config):
    """Config for the 'start' subcommand."""

    command: Literal["start"]

    # ----- CONFIG
    add_command: str
    runtime: int
    shutdown_commands: List[str]
    validation: ValidateOptions
    startup_commands: List[str]


class AddConfig(Config):
    """Config for the 'add' subcommand."""

    command: Literal["add"]

    # ----- ARGUMENTS
    magnet_url: str
    download_dir: Path


def clack_parser(argv: Sequence[str]) -> dict[str, Any]:
    """Parser we pass to the `main_factory()` `parser` kwarg."""

    parser = clack.Parser(
        description="Don't have a good day. Have a great day."
    )

    new_command = clack.new_command_factory(parser)

    new_command(
        "start",
        help=(
            "Start the system's torrent service, add any missing torrents to"
            " it (i.e. torrents added via `tman add ...`), wait configured"
            " amount of time, and then shutdown the system torrent service we"
            " started earlier."
        ),
    )

    add_parser = new_command(
        "add",
        help="Qeueue new torrent to download next time `tman start` is run.",
    )
    add_parser.add_argument(
        "magnet_url",
        metavar="TODO",
        help="A magnet URL used to identify a torrent.",
    )
    add_parser.add_argument(
        "-w",
        "--download-dir",
        type=Path,
        help="The folder that this torrent should be downloaded to.",
    )

    args = parser.parse_args(argv[1:])
    kwargs = clack.filter_cli_args(args)

    return kwargs
