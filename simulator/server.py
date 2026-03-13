import asyncio

import structlog
from asyncua import Server, ua

from simulator.config import EQUIPMENT, NAMESPACE_INDEX, NAMESPACE_URI, EquipmentConfig
from simulator.signals import SignalGenerator

log = structlog.get_logger()

ENDPOINT = "opc.tcp://0.0.0.0:4840"


class SimulatorServer:
    """
    OPC-UA server that exposes simulated industrial equipment data.

    On startup it registers three equipment objects (Pump-01, Compressor-01,
    HeatExchanger-01) each with child variable nodes.  Every second it writes
    a new value — produced by SignalGenerator — to every node.

    Node IDs follow the pattern ns=2;i=<node_numeric_id> as defined in
    simulator/config.py.  The collector uses the same IDs to read values.
    """

    def __init__(self) -> None:
        self._server = Server()
        # Maps "ns=2;i=XXXX" -> asyncua Variable node
        self._variables: dict[str, object] = {}
        # Maps "ns=2;i=XXXX" -> SignalGenerator
        self._generators: dict[str, SignalGenerator] = {}

    async def start(self) -> None:
        await self._server.init()
        self._server.set_endpoint(ENDPOINT)
        self._server.set_server_name("OPC-UA Industrial Simulator")

        idx = await self._server.register_namespace(NAMESPACE_URI)
        log.info("namespace_registered", index=idx, uri=NAMESPACE_URI)

        # Sanity-check: the namespace index must match what the collector expects.
        if idx != NAMESPACE_INDEX:
            raise RuntimeError(
                f"Unexpected namespace index {idx} (expected {NAMESPACE_INDEX}). "
                "Update NAMESPACE_INDEX in simulator/config.py."
            )

        await self._build_address_space(idx)

        async with self._server:
            log.info("simulator_started", endpoint=ENDPOINT)
            while True:
                await self._tick()
                await asyncio.sleep(1.0)

    async def _build_address_space(self, idx: int) -> None:
        objects = self._server.nodes.objects

        for eq_cfg in EQUIPMENT:
            eq_obj = await objects.add_object(idx, eq_cfg.name)
            log.info("equipment_registered", name=eq_cfg.name)

            for tag_cfg in eq_cfg.tags:
                node_id_str = f"ns={idx};i={tag_cfg.node_numeric_id}"
                # Create the variable with an explicit numeric node ID so the
                # collector can address it by the well-known "ns=2;i=XXXX" string.
                var = await eq_obj.add_variable(
                    ua.NodeId(tag_cfg.node_numeric_id, idx),
                    tag_cfg.name,
                    tag_cfg.base,
                    varianttype=ua.VariantType.Float,
                )
                await var.set_writable(True)

                self._variables[node_id_str] = var
                self._generators[node_id_str] = SignalGenerator(tag_cfg)

                log.info(
                    "node_registered",
                    node_id=node_id_str,
                    tag=tag_cfg.name,
                    equipment=eq_cfg.name,
                    unit=tag_cfg.unit,
                )

    async def _tick(self) -> None:
        for node_id_str, var in self._variables.items():
            new_val = self._generators[node_id_str].value()
            # Explicitly write as Float (ua.VariantType 10).
            # Without this, Python's float is sent as Double (type 11),
            # which mismatches the Float type declared at node creation.
            await var.write_value(new_val, ua.VariantType.Float)
