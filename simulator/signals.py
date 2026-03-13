import math
import random
import time

from simulator.config import TagConfig


class SignalGenerator:
    """
    Produces realistic-looking sensor values for a single tag.

    The output is the sum of three components:
      1. Sinusoidal base  — simulates a normal operating cycle
         (e.g. a pump temperature that rises and falls over 10 minutes)
      2. Gaussian noise   — small random variation around the base
      3. Spike            — occasional sudden jump that decays exponentially
         (e.g. a bearing heat spike that builds instantly and fades over 60 s)

    All state is relative to the time of construction so every generator
    starts at a random phase of its cycle (achieved by randomising _start).
    """

    def __init__(self, config: TagConfig) -> None:
        self._cfg = config
        # Randomise the starting phase so different tags on the same machine
        # don't all peak and trough at the same moment.
        random_phase_offset = random.uniform(0, config.period) if config.period > 0 else 0
        self._start = time.monotonic() - random_phase_offset
        self._spike_active = False
        self._spike_start: float | None = None

    def value(self) -> float:
        cfg = self._cfg
        t = time.monotonic() - self._start

        # 1. Sinusoidal base
        if cfg.period > 0:
            sinusoidal = cfg.base + cfg.amplitude * math.sin(2 * math.pi * t / cfg.period)
        else:
            sinusoidal = cfg.base

        # 2. Gaussian noise
        noise = random.gauss(0.0, cfg.noise_std) if cfg.noise_std > 0 else 0.0

        # 3. Spike
        spike = 0.0
        if cfg.spike_probability > 0:
            if not self._spike_active:
                # Each tick has a small independent chance of triggering a spike.
                if random.random() < cfg.spike_probability:
                    self._spike_active = True
                    self._spike_start = t

            if self._spike_active and self._spike_start is not None:
                elapsed = t - self._spike_start
                spike = cfg.spike_magnitude * math.exp(-elapsed / cfg.spike_decay_seconds)
                # Deactivate once the spike has decayed to an imperceptible level.
                if spike < 0.01:
                    self._spike_active = False
                    self._spike_start = None

        return round(sinusoidal + noise + spike, 3)
