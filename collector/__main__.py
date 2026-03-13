import asyncio
import logging

import structlog

from collector.service import CollectorService
from collector.settings import settings

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
)

logging.getLogger("asyncua").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

log = structlog.get_logger()


async def main() -> None:
    service = CollectorService(settings)
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
