"""
Physical power-leakage model.

On a real chip the instantaneous power depends on the data being processed.
We use the standard Hamming-weight model: power at the leaking instant is
proportional to HW(intermediate), buried in Gaussian measurement noise.
The leaking intermediate targeted here is the AES first-round S-box output.

Protections supported:
  - "none"      : unprotected meter, S-box output leaks directly.
  - "masking"   : first-order Boolean masking. Each byte is processed as
                  (intermediate XOR m) and m separately, m random per trace.
                  No single sample correlates with the secret intermediate,
                  so first-order CPA fails.
  - "shuffling" : the 16 byte operations happen in a random time order each
                  trace, so a given key byte's leak is smeared across samples,
                  sharply reducing correlation at any fixed sample.
"""
from __future__ import annotations
import numpy as np
from .aes import SBOX, HW

PROTECTIONS = ("none", "masking", "shuffling")


def simulate_traces(plaintexts: np.ndarray, key: np.ndarray, *,
                    n_samples: int = 200, noise_sigma: float = 2.0,
                    protection: str = "none", seed: int = 0):
    """
    Build synthetic power traces for the given plaintext blocks and key.

    Returns traces [n_traces, n_samples] (float). Each key byte leaks at its
    own time sample; all other samples are noise, like a real trace where the
    S-box lookups happen at distinct instants.
    """
    assert protection in PROTECTIONS, f"unknown protection {protection}"
    rng = np.random.default_rng(seed)
    n = plaintexts.shape[0]
    traces = rng.normal(0.0, noise_sigma, size=(n, n_samples))
    leak_pts = np.linspace(6, n_samples - 6, num=16).astype(int)

    for b in range(16):
        inter = SBOX[np.bitwise_xor(plaintexts[:, b], key[b])]   # true S-box out
        if protection == "none":
            traces[:, leak_pts[b]] += HW[inter]

        elif protection == "masking":
            m = rng.integers(0, 256, size=n, dtype=np.uint8)
            masked = np.bitwise_xor(inter, m)
            # Two shares leak at two different samples; neither is the secret.
            traces[:, leak_pts[b]] += HW[masked]
            other = (leak_pts[b] + 3) % n_samples
            traces[:, other] += HW[m]

        elif protection == "shuffling":
            # Each trace puts this byte's leak at a random one of the 16 slots.
            slot = rng.integers(0, 16, size=n)
            for s in range(16):
                sel = slot == s
                if sel.any():
                    traces[sel, leak_pts[s]] += HW[inter[sel]]

    return traces
