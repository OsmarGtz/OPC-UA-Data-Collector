"""
Unit tests for simulator.signals.SignalGenerator.

These tests are pure Python — no I/O, no database, no OPC-UA server.
They verify the mathematical correctness of each signal component
(sinusoidal base, Gaussian noise, spike injection/decay) in isolation.
"""

import math
from unittest.mock import patch

import pytest

from simulator.config import TagConfig
from simulator.signals import SignalGenerator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_config(**overrides) -> TagConfig:
    """Return a TagConfig with safe defaults; override any field via kwargs."""
    defaults = dict(
        name="test_tag",
        node_numeric_id=9999,
        unit="°C",
        data_type="Float",
        base=50.0,
        amplitude=10.0,
        period=60.0,
        noise_std=0.0,  # deterministic by default
        spike_probability=0.0,  # no spikes by default
        spike_magnitude=0.0,
        spike_decay_seconds=1.0,
    )
    defaults.update(overrides)
    return TagConfig(**defaults)


def make_generator(fixed_start: float = 0.0, **overrides) -> SignalGenerator:
    """
    Return a SignalGenerator with a pinned _start time so tests that read
    value() at a known monotonic instant get a deterministic sinusoidal result.
    """
    cfg = make_config(**overrides)
    gen = SignalGenerator(cfg)
    gen._start = fixed_start  # bypass the random phase offset
    return gen


# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------


def test_value_returns_float():
    gen = make_generator()
    assert isinstance(gen.value(), float)


def test_value_is_finite():
    gen = make_generator()
    v = gen.value()
    assert math.isfinite(v)


# ---------------------------------------------------------------------------
# Sinusoidal component
# ---------------------------------------------------------------------------


def test_zero_amplitude_equals_base():
    """With amplitude=0 and no noise or spikes, value must equal base exactly."""
    gen = make_generator(amplitude=0.0)
    with patch("simulator.signals.time.monotonic", return_value=gen._start):
        assert gen.value() == pytest.approx(50.0, abs=1e-9)


def test_sinusoidal_peak_at_quarter_period():
    """At t = period/4, sin(2π·t/T) = 1 → value should equal base + amplitude."""
    period = 60.0
    gen = make_generator(period=period)
    # At t = T/4, sin = 1
    t_quarter = gen._start + period / 4
    with patch("simulator.signals.time.monotonic", return_value=t_quarter):
        v = gen.value()
    assert v == pytest.approx(50.0 + 10.0, abs=1e-2)


def test_sinusoidal_trough_at_three_quarter_period():
    """At t = 3·period/4, sin = -1 → value should equal base - amplitude."""
    period = 60.0
    gen = make_generator(period=period)
    t_trough = gen._start + 3 * period / 4
    with patch("simulator.signals.time.monotonic", return_value=t_trough):
        v = gen.value()
    assert v == pytest.approx(50.0 - 10.0, abs=1e-2)


def test_noiseless_value_stays_within_sinusoidal_bounds():
    """Without noise or spikes, every value must lie in [base-amplitude, base+amplitude]."""
    gen = make_generator()
    lo, hi = 50.0 - 10.0, 50.0 + 10.0
    for i in range(120):
        # Advance simulated time by 0.5 s each iteration to cover two full cycles.
        with patch("simulator.signals.time.monotonic", return_value=gen._start + i * 0.5):
            assert lo <= gen.value() <= hi


def test_zero_period_returns_base():
    """period=0 disables the sinusoid; value should always equal base."""
    gen = make_generator(amplitude=5.0, period=0.0)
    with patch("simulator.signals.time.monotonic", return_value=gen._start + 1000.0):
        assert gen.value() == pytest.approx(50.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Noise component
# ---------------------------------------------------------------------------


def test_noise_varies_output():
    """With noise_std > 0, repeated samples at the same instant must not all be equal."""
    gen = make_generator(amplitude=0.0, noise_std=2.0)
    with patch("simulator.signals.time.monotonic", return_value=gen._start):
        samples = [gen.value() for _ in range(50)]
    assert len(set(samples)) > 1, "Noise should produce different values each call"


def test_zero_noise_is_deterministic():
    """With noise_std=0, the same (t, config) always produces the same value."""
    gen = make_generator(noise_std=0.0)
    t = gen._start + 15.0
    with patch("simulator.signals.time.monotonic", return_value=t):
        v1 = gen.value()
        v2 = gen.value()
    assert v1 == v2


# ---------------------------------------------------------------------------
# Spike component
# ---------------------------------------------------------------------------


def test_no_spike_when_probability_zero():
    """spike_probability=0 must never activate a spike regardless of calls."""
    gen = make_generator(spike_probability=0.0, spike_magnitude=100.0)
    for i in range(500):
        with patch("simulator.signals.time.monotonic", return_value=gen._start + i):
            gen.value()
    assert not gen._spike_active


def test_spike_triggers_with_certainty():
    """spike_probability=1.0 must trigger a spike on the very first call."""
    gen = make_generator(
        amplitude=0.0,
        spike_probability=1.0,
        spike_magnitude=20.0,
        spike_decay_seconds=60.0,
    )
    with patch("simulator.signals.time.monotonic", return_value=gen._start):
        gen.value()
    assert gen._spike_active


def test_spike_raises_value_above_base():
    """When a spike is active, the returned value must exceed the noiseless sinusoidal."""
    gen = make_generator(
        amplitude=0.0,
        noise_std=0.0,
        spike_probability=1.0,
        spike_magnitude=20.0,
        spike_decay_seconds=60.0,
    )
    with patch("simulator.signals.time.monotonic", return_value=gen._start):
        v = gen.value()
    # base=50, amplitude=0, spike_magnitude=20 → value ≈ 70
    assert v > 50.0


def test_spike_decays_over_time():
    """The spike contribution must decrease monotonically after it fires."""
    gen = make_generator(
        amplitude=0.0,
        noise_std=0.0,
        spike_probability=1.0,
        spike_magnitude=20.0,
        spike_decay_seconds=10.0,
    )
    # Fire the spike at t=0
    with patch("simulator.signals.time.monotonic", return_value=gen._start):
        v0 = gen.value()
    assert gen._spike_active

    prev = v0
    for elapsed in [1.0, 3.0, 6.0, 10.0, 20.0]:
        with patch("simulator.signals.time.monotonic", return_value=gen._start + elapsed):
            v = gen.value()
        assert v <= prev, f"Spike should decay: {v} > {prev} at t={elapsed}"
        prev = v


def test_spike_eventually_deactivates():
    """After enough decay, _spike_active must return to False."""
    gen = make_generator(
        amplitude=0.0,
        noise_std=0.0,
        spike_probability=1.0,
        spike_magnitude=20.0,
        spike_decay_seconds=1.0,  # fast decay
    )
    with patch("simulator.signals.time.monotonic", return_value=gen._start):
        gen.value()
    assert gen._spike_active

    # After ~10× the decay constant the spike (20 * e^-10 ≈ 0.00009) is well below 0.01
    with patch("simulator.signals.time.monotonic", return_value=gen._start + 10.0):
        gen.value()
    assert not gen._spike_active


# ---------------------------------------------------------------------------
# Random phase
# ---------------------------------------------------------------------------


def test_two_generators_start_at_different_phases():
    """
    Two generators built from the same config must produce different values
    because the constructor randomises the starting phase.
    Probability of accidental equality is negligible (continuous distribution).
    """
    cfg = make_config(amplitude=10.0, noise_std=0.0)
    gen1 = SignalGenerator(cfg)
    gen2 = SignalGenerator(cfg)

    t = max(gen1._start, gen2._start) + 1.0  # same wall-clock instant for both
    with patch("simulator.signals.time.monotonic", return_value=t):
        v1 = gen1.value()
        v2 = gen2.value()
    assert v1 != pytest.approx(
        v2, abs=1e-3
    ), "Generators with different random phases should produce different values"
