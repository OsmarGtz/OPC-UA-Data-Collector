from dataclasses import dataclass

# The OPC-UA namespace URI registered by this simulator.
# The server will assign it index 2 (indices 0 and 1 are reserved by OPC-UA).
NAMESPACE_URI = "http://opc-ua-simulator"
NAMESPACE_INDEX = 2


@dataclass(frozen=True)
class TagConfig:
    name: str
    node_numeric_id: int  # forms node_id "ns=2;i=<node_numeric_id>"
    unit: str
    data_type: str
    # --- sinusoidal base signal ---
    base: float           # centre value
    amplitude: float      # half the oscillation range
    period: float         # full cycle length in seconds
    noise_std: float      # standard deviation of Gaussian noise
    # --- spike injection ---
    spike_probability: float   # probability per 1-second tick (0 = no spikes)
    spike_magnitude: float     # how much the spike adds at its peak
    spike_decay_seconds: float # exponential decay constant


@dataclass(frozen=True)
class EquipmentConfig:
    name: str
    description: str
    location: str
    tags: tuple[TagConfig, ...]


# ---------------------------------------------------------------------------
# Equipment and tag definitions
# Each tag's node_numeric_id maps to an OPC-UA node "ns=2;i=<id>".
# Signal parameters are chosen to look realistic in a screen recording.
# ---------------------------------------------------------------------------
EQUIPMENT: tuple[EquipmentConfig, ...] = (
    EquipmentConfig(
        name="Pump-01",
        description="Primary circulation pump",
        location="Building A",
        tags=(
            # temperature: 65–78 °C, 10-min cycle, spike to ~88 °C every ~30 min
            TagConfig("temperature",   1001, "°C",    "Float", 71.5,  6.5, 600, 0.5,  1 / 1800, 16.0, 60.0),
            # pressure: 4.0–5.0 bar, 8-min cycle, rare spike
            TagConfig("pressure",      1002, "bar",   "Float",  4.5,  0.5, 480, 0.1,  1 / 3600,  1.5, 30.0),
            # vibration: 2.5–3.1 mm/s, 5-min cycle, occasional spike
            TagConfig("vibration_rms", 1003, "mm/s",  "Float",  2.8,  0.3, 300, 0.15, 1 / 2700,  3.5, 120.0),
            # flow rate: 77–93 L/min, 9-min cycle, no spikes
            TagConfig("flow_rate",     1004, "L/min", "Float", 85.0,  8.0, 540, 1.0,  0.0,       0.0, 0.0),
        ),
    ),
    EquipmentConfig(
        name="Compressor-01",
        description="Air compression unit",
        location="Building B",
        tags=(
            TagConfig("temperature",   1011, "°C",    "Float",  95.0,  8.0, 720, 0.8,  1 / 1800, 20.0,  90.0),
            TagConfig("pressure",      1012, "bar",   "Float",  12.5,  1.5, 600, 0.2,  1 / 3600,  3.0,  45.0),
            TagConfig("vibration_rms", 1013, "mm/s",  "Float",   4.2,  0.5, 240, 0.2,  1 / 1800,  5.0,  90.0),
            TagConfig("flow_rate",     1014, "Nm³/h", "Float", 120.0, 12.0, 480, 2.0,  0.0,       0.0,   0.0),
        ),
    ),
    EquipmentConfig(
        name="HeatExchanger-01",
        description="Shell and tube heat exchanger",
        location="Building A",
        tags=(
            TagConfig("temperature_in",  1021, "°C",    "Float",  85.0,  5.0, 600, 0.4,  0.0,       0.0,  0.0),
            TagConfig("temperature_out", 1022, "°C",    "Float",  42.0,  3.0, 600, 0.3,  0.0,       0.0,  0.0),
            TagConfig("pressure",        1023, "bar",   "Float",   3.2,  0.3, 420, 0.05, 1 / 3600,  1.0, 30.0),
            TagConfig("flow_rate",       1024, "L/min", "Float", 200.0, 15.0, 540, 2.0,  0.0,       0.0,  0.0),
        ),
    ),
)
