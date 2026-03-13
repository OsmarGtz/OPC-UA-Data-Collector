from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.models.reading import Reading

log = structlog.get_logger()


class DatabaseWriter:
    """
    Handles bulk insertion of Reading rows.

    Uses SQLAlchemy's insert().values([...]) bulk form instead of adding
    ORM objects one by one — this sends a single INSERT statement with
    multiple value tuples, which is significantly faster at high polling rates.
    """

    async def bulk_insert(
        self, session: AsyncSession, rows: list[dict]
    ) -> int:
        """
        Insert a batch of reading dicts and commit.
        Returns the number of rows inserted.
        """
        if not rows:
            return 0

        await session.execute(insert(Reading), rows)
        await session.commit()

        log.info("readings_inserted", count=len(rows))
        return len(rows)
