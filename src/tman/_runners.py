"""Contains this project's clack runners."""

from __future__ import annotations

import atexit
import os
import signal
import sys
import time
from types import FrameType
from typing import List

import clack
from clack.types import ClackRunner
from logrus import Logger

from ._config import AddConfig, StartConfig


ALL_RUNNERS: List[ClackRunner] = []
runner = clack.register_runner_factory(ALL_RUNNERS)

logger = Logger(__name__)


@runner
def run_add(cfg: AddConfig) -> int:
    """Runner for the `tman add ...` command."""
    cfg.torrent_bucket.parent.mkdir(parents=True, exist_ok=True)
    with cfg.torrent_bucket.open("a+") as f:
        f.write(f"{cfg.download_dir} {cfg.magnet_url}\n")
    return 0


def signal_handler(signum: int, frame: FrameType | None) -> None:
    """Generic signal handler (used to make sure exit handlers trigger)."""
    del frame
    sys.exit(128 + signum)


@runner
def run_start(cfg: StartConfig) -> int:
    """Runner for the `tman start` command."""
    cfg.torrent_bucket.parent.mkdir(parents=True, exist_ok=True)

    execute_commands(*cfg.startup_commands)
    if cfg.torrent_bucket.is_file():
        add_cmds = []
        for line in cfg.torrent_bucket.open():
            download_dir, magnet_url = line.split(" ", maxsplit=1)
            cmd = cfg.add_command.format(
                download_dir=download_dir, magnet_url=magnet_url
            )
            add_cmds.append(cmd)

        execute_commands(*add_cmds)
        cfg.torrent_bucket.unlink()

    logger.info(
        "Downloading / seeding torrents for configured amount of time.",
        seconds=cfg.runtime,
    )

    atexit.register(execute_commands, *cfg.shutdown_commands)
    signal.signal(signal.SIGTERM, signal_handler)

    time.sleep(cfg.runtime)

    return 0


def execute_commands(*cmds: str) -> None:
    """Executes all of the system commands in `cmds`."""
    for cmd in cmds:
        logger.info("Executing system command.", command=cmd)
        os.system(cmd)
