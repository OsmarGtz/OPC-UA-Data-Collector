import asyncio
import logging

import structlog

from simulator.server import SimulatorServer

# Configure structlog to emit human-readable key=value lines.
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
)

# Suppress the very verbose asyncua internal logs.
logging.getLogger("asyncua").setLevel(logging.WARNING)

log = structlog.get_logger()


async def main() -> None:
    log.info("simulator_starting")
    server = SimulatorServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
