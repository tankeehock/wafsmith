import rich.console
import logging

from rich.logging import RichHandler

console = rich.console.Console()

def init_logging(level: str = logging.INFO):
    # Log and progress should use the same console instance
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True
    )
    rich_handler.setLevel(level)
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.basicConfig(
        level=logging.NOTSET,
        format="%(message)s",
        datefmt="[%X]",
        # handlers=[RichHandler(rich_tracebacks=True, markup=True)],
        handlers=[rich_handler]
    )
