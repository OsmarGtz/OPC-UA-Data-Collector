import asyncio

import structlog
from asyncua import Client

log = structlog.get_logger()


class OpcUaClient:
    """
    Thin wrapper around asyncua.Client with:
      - exponential-backoff reconnection
      - concurrent batch reads via asyncio.gather (one asyncua call per node,
        all fired simultaneously so they share a single TCP round-trip window)
    """

    def __init__(self, url: str) -> None:
        self._url = url
        self._client: Client | None = None

    async def connect_with_retry(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        """
        Keep trying to connect until successful.
        Delay doubles after each failure, capped at max_delay.
        """
        attempt = 0
        while True:
            try:
                self._client = Client(url=self._url)
                await self._client.connect()
                log.info("opcua_connected", url=self._url)
                return
            except Exception as exc:
                attempt += 1
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                log.warning(
                    "opcua_connection_failed",
                    attempt=attempt,
                    retry_in=delay,
                    error=str(exc),
                )
                await asyncio.sleep(delay)

    async def disconnect(self) -> None:
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None

    async def read_node_values(
        self, node_ids: list[str]
    ) -> list[tuple[str, float | None, str]]:
        """
        Read multiple OPC-UA nodes concurrently.

        Returns a list of (node_id, value, quality) tuples where quality is
        one of "Good", "Uncertain", "Bad" — matching the Reading.quality field.

        All reads are launched simultaneously with asyncio.gather so they
        overlap on the wire rather than executing sequentially.
        """
        if self._client is None:
            raise RuntimeError("OPC-UA client is not connected")

        nodes = [self._client.get_node(nid) for nid in node_ids]

        raw = await asyncio.gather(
            *[n.read_data_value() for n in nodes],
            return_exceptions=True,
        )

        results: list[tuple[str, float | None, str]] = []
        for node_id, data_value in zip(node_ids, raw):
            if isinstance(data_value, Exception):
                log.warning("node_read_error", node_id=node_id, error=str(data_value))
                results.append((node_id, None, "Bad"))
                continue

            try:
                raw_val = data_value.Value.Value
                value = float(raw_val) if raw_val is not None else None
            except (TypeError, ValueError):
                value = None

            status = data_value.StatusCode
            if status.is_good():
                quality = "Good"
            elif status.is_bad():
                quality = "Bad"
            else:
                quality = "Uncertain"

            results.append((node_id, value, quality))

        return results
