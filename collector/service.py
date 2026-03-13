import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models.equipment import Equipment
from app.models.tag import Tag
from app.alerts.evaluator import RuleEvaluator
from collector.opcua_client import OpcUaClient
from collector.settings import CollectorSettings
from collector.writer import DatabaseWriter
from simulator.config import EQUIPMENT as SIM_EQUIPMENT

log = structlog.get_logger()


class CollectorService:
    """
    Main service that:
      1. Seeds the database with Equipment + Tags from simulator config (idempotent)
      2. Connects to the OPC-UA server with exponential-backoff retry
      3. Polls all tags every POLL_INTERVAL seconds and bulk-inserts Readings

    NullPool is used so each async context manager gets a fresh connection
    with no pool state shared between poll cycles.
    """

    def __init__(self, settings: CollectorSettings) -> None:
        self._settings = settings
        self._opcua = OpcUaClient(settings.OPCUA_URL)
        self._writer = DatabaseWriter()
        self._evaluator = RuleEvaluator()
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            poolclass=NullPool,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def run(self) -> None:
        log.info("collector_starting", opcua_url=self._settings.OPCUA_URL)

        # Step 1 — Seed DB from simulator config (safe to re-run)
        async with self._session_factory() as session:
            await self._seed_db(session)

        # Step 2 — Connect to OPC-UA (blocks until connected)
        await self._opcua.connect_with_retry(
            base_delay=self._settings.RETRY_BASE_DELAY,
            max_delay=self._settings.RETRY_MAX_DELAY,
        )

        # Step 3 — Load all tags from DB so we have their PKs
        async with self._session_factory() as session:
            tags = await self._load_tags(session)

        log.info("collector_ready", tag_count=len(tags))

        # Step 4 — Poll loop
        while True:
            try:
                await self._poll_and_store(tags)
            except Exception as exc:
                # Don't crash on a single bad poll cycle; log and continue.
                log.error("poll_cycle_failed", error=str(exc))

            await asyncio.sleep(self._settings.POLL_INTERVAL)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _seed_db(self, session: AsyncSession) -> None:
        """
        Create Equipment and Tag rows from simulator config if they don't
        already exist.  Matches Equipment by name and Tag by node_id so the
        operation is safe to run on every startup.
        """
        for eq_cfg in SIM_EQUIPMENT:
            result = await session.execute(
                select(Equipment).where(Equipment.name == eq_cfg.name)
            )
            eq = result.scalar_one_or_none()

            if eq is None:
                eq = Equipment(
                    name=eq_cfg.name,
                    description=eq_cfg.description,
                    location=eq_cfg.location,
                )
                session.add(eq)
                await session.flush()  # populate eq.id before inserting tags
                log.info("equipment_created", name=eq_cfg.name)

            for tag_cfg in eq_cfg.tags:
                node_id = f"ns=2;i={tag_cfg.node_numeric_id}"
                result = await session.execute(
                    select(Tag).where(Tag.node_id == node_id)
                )
                tag = result.scalar_one_or_none()

                if tag is None:
                    tag = Tag(
                        name=tag_cfg.name,
                        node_id=node_id,
                        unit=tag_cfg.unit,
                        data_type=tag_cfg.data_type,
                        equipment_id=eq.id,
                    )
                    session.add(tag)
                    log.info("tag_created", node_id=node_id, name=tag_cfg.name)

        await session.commit()

    async def _load_tags(self, session: AsyncSession) -> list[Tag]:
        result = await session.execute(select(Tag))
        return list(result.scalars().all())

    async def _poll_and_store(self, tags: list[Tag]) -> None:
        node_ids = [tag.node_id for tag in tags]
        tag_by_node_id = {tag.node_id: tag for tag in tags}

        readings_raw = await self._opcua.read_node_values(node_ids)

        now = datetime.now(timezone.utc)
        rows: list[dict] = []

        for node_id, value, quality in readings_raw:
            tag = tag_by_node_id.get(node_id)
            if tag is None:
                continue

            rows.append(
                {
                    "tag_id": tag.id,
                    "value": value,
                    "raw_value": str(value) if value is not None else None,
                    "quality": quality,
                    "timestamp": now,
                }
            )

        async with self._session_factory() as session:
            await self._writer.bulk_insert(session, rows)
            await self._evaluator.check(session, rows)
