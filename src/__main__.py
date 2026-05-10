from __future__ import annotations

from click import group, version_option  # type: ignore

from . import version
from .cli.commands import APP


@version_option(version=version, message="%(version)s")
@group(cls=APP)
def cli() -> None:
    pass


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
