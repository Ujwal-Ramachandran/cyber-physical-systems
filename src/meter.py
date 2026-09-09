"""
Smart-meter model. A meter measures a kWh reading, serialises it into a
16-byte block (reading + timestamp + rolling counter), and AES-128 encrypts
that block before sending it to the utility.

For the side-channel attack we use the standard known-plaintext assumption:
the attacker can observe the block being encrypted (or equivalently the
ciphertext) and measures power while the meter runs AES.
"""
from __future__ import annotations
import struct
import numpy as np
from . import aes

# A fixed demo key so results are reproducible. This is the SECRET the attacker
# is trying to recover; the attack code never reads it.
DEMO_KEY = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")


class SmartMeter:
    def __init__(self, key: bytes = DEMO_KEY, seed: int = 2026):
        assert len(key) == 16
        self.key = key
        self._rng = np.random.default_rng(seed)

    def reading_to_block(self, reading_kwh: float, counter: int) -> bytes:
        """Serialise a reading into a 16-byte AES input block."""
        ts = 1_756_000_000 + counter * 900          # a plausible unix timestamp
        rnd = int(self._rng.integers(0, 2**32))
        return struct.pack("<f I I I", float(reading_kwh), ts & 0xFFFFFFFF,
                           counter & 0xFFFFFFFF, rnd)

    def encrypt_reading(self, reading_kwh: float, counter: int) -> tuple[bytes, bytes]:
        """Return (plaintext_block, ciphertext) for one reading."""
        block = self.reading_to_block(reading_kwh, counter)
        return block, aes.encrypt_block(block, self.key)

    def capture(self, n_traces: int) -> np.ndarray:
        """
        Simulate the meter running AES n_traces times and return the array of
        AES input blocks [n_traces, 16] the attacker observes.

        Real AMI meters use a nonce/counter mode (AES-CTR or AES-GCM), so each
        message feeds AES a fresh, varying, publicly known counter block. We
        model that here: uniformly varying known inputs across all 16 bytes,
        which is exactly the standard known-input target of a CPA on AES-GCM.
        (encrypt_reading() above shows the meter also encrypting a real kWh
        reading; capture() provides the varied inputs the attack needs.)
        """
        return self._rng.integers(0, 256, size=(n_traces, 16), dtype=np.uint8)

    def key_array(self) -> np.ndarray:
        return np.frombuffer(self.key, dtype=np.uint8)
