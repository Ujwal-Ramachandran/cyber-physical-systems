"""
Rigorous side-channel evaluation metrics.

- traces_to_disclosure: how the correct key byte's rank drops as more traces
  are used. TTD = smallest number of traces at which the correct byte becomes,
  and stays, the top guess (rank 0).
- guessing_entropy: average log2 rank of the correct key across bytes vs number
  of traces (a standard SCA metric; lower is a stronger attack).
- success_rate: fraction of independent experiments that recover the full key.
"""
from __future__ import annotations
import numpy as np
from .aes import SBOX, HW
from . import cpa, leakage


def _ranks_for_byte(traces, plaintexts, byte, true_val, checkpoints):
    """Rank of the true key byte (0 = best guess) at each checkpoint count."""
    ranks = []
    for k in checkpoints:
        corr = cpa.byte_correlations(traces[:k], plaintexts[:k], byte)
        order = np.argsort(corr)[::-1]              # best first
        rank = int(np.where(order == true_val)[0][0])
        ranks.append(rank)
    return np.array(ranks)


def guessing_entropy_curve(traces, plaintexts, key, checkpoints):
    """Mean log2(rank+1) of the correct key across all 16 bytes vs #traces."""
    ge = np.zeros(len(checkpoints))
    for b in range(16):
        r = _ranks_for_byte(traces, plaintexts, b, int(key[b]), checkpoints)
        ge += np.log2(r + 1)
    return ge / 16.0


def traces_to_disclosure(traces, plaintexts, key, byte, checkpoints):
    """Smallest checkpoint from which the true byte stays rank 0. -1 if never."""
    ranks = _ranks_for_byte(traces, plaintexts, byte, int(key[byte]), checkpoints)
    ttd = -1
    for i in range(len(checkpoints)):
        if np.all(ranks[i:] == 0):
            ttd = int(checkpoints[i]); break
    return ttd, ranks


def success_rate(meter_capture_fn, key, *, n_trials=20, n_traces=1000,
                 noise_sigma=2.0, protection="none", base_seed=100):
    """Repeat capture+attack n_trials times; fraction recovering the FULL key."""
    full = 0
    per_byte = np.zeros(16)
    for t in range(n_trials):
        pts = meter_capture_fn(n_traces)
        tr = leakage.simulate_traces(pts, key, noise_sigma=noise_sigma,
                                     protection=protection, seed=base_seed + t)
        rec, _, _ = cpa.recover_key(tr, pts)
        hits = (rec == key)
        per_byte += hits
        if hits.all():
            full += 1
    return full / n_trials, per_byte / n_trials
