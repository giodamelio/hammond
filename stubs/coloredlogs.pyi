import logging

def install(
    level: int | str | None = None,
    logger: logging.Logger | None = None,
    fmt: str | None = None,
    datefmt: str | None = None,
    isatty: bool | None = None,
) -> None: ...
