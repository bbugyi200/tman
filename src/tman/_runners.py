"""Contains this project's clack runners."""

from __future__ import annotations

import atexit
import os
import signal
import subprocess as sp
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

    logger.info(
        "Adding torrent to queue.",
        downlaod_dir=cfg.download_dir,
        magnet_url=cfg.magnet_url,
    )
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

    # run startup commands
    if not execute_commands(*cfg.startup_commands):
        logger.error(
            "Failed to run startup commands (e.g. to start VPN). Aborting...",
            startup_commands=cfg.startup_commands,
        )
        return 1

    # register shutdown commands
    atexit.register(execute_commands, *cfg.shutdown_commands)
    signal.signal(signal.SIGTERM, signal_handler)

    # run validation command
    for i in range(cfg.validation.retries):
        popen = sp.Popen(
            cfg.validation.command, shell=True, stdout=sp.PIPE, stderr=sp.PIPE
        )
        stdout, stderr = popen.communicate()
        output = stdout.decode().strip()
        if output == cfg.validation.good_output:
            logger.info(
                "Validation command succeeded.",
                command=cfg.validation.command,
                output=cfg.validation.good_output,
                attempt=i + 1,
            )
            break
        else:
            logger.warning(
                "Validation command failed.",
                command=cfg.validation.command,
                attempt=i + 1,
                expected_output=cfg.validation.good_output,
                actual_output=output,
                stderr=stderr.decode().strip(),
            )
            time.sleep(1)
    else:
        logger.error(
            "Validation command failed too many times.",
            retries=cfg.validation.retries,
        )
        return 1

    # add new torrents from file
    if cfg.torrent_bucket.is_file():
        add_cmds = []
        for line in cfg.torrent_bucket.open():
            download_dir, magnet_url = line.split(" ", maxsplit=1)
            cmd = cfg.add_command.format(
                download_dir=download_dir, magnet_url=magnet_url
            )
            add_cmds.append(cmd)

        execute_commands(*add_cmds, strict=False)
        cfg.torrent_bucket.unlink()

    logger.info(
        "Downloading / seeding torrents for configured amount of time.",
        seconds=cfg.runtime,
    )

    time.sleep(cfg.runtime)

    return 0


def execute_commands(*cmds: str, strict: bool = True) -> bool:
    """Executes all of the system commands in `cmds`."""
    log = logger.bind_fargs(locals())

    result = True
    for i, cmd in enumerate(cmds):
        log.info("Executing system command.", command=cmd)

        ec = os.system(cmd)
        if ec != 0 and strict:
            log.error(
                "Aborting after command failed with non-zero exit code.",
                commands_not_run=cmd[i + 1 :],
                exit_code=ec,
                failed_command=cmd,
            )
            result = False
            break

        if ec != 0:
            log.warning(
                "Command failed with a non-zero exit status.",
                exit_code=ec,
                failed_command=cmd,
            )
            result = False

    return result
