"""
Correlation Power Analysis (CPA) attack engine.

For each key-byte position we try all 256 candidate values. For a candidate we
predict the leakage HW(SBOX[plaintext ^ guess]) and correlate that prediction
with every time sample of the measured traces (Pearson). The candidate whose
prediction best matches the traces is the recovered key byte.

The attacker uses only: plaintexts, traces, and the public AES S-box.
It never sees the key. (Brier, Clavier, Olivier, CHES 2004.)
"""
from __future__ import annotations
import numpy as np
from .aes import SBOX, HW


def _prep_traces(traces: np.ndarray):
    t = traces - traces.mean(axis=0, keepdims=True)
    ss = np.sqrt((t ** 2).sum(axis=0))
    ss[ss == 0] = 1e-12
    return t, ss


def byte_correlations(traces: np.ndarray, plaintexts: np.ndarray, byte: int):
    """Return max |correlation| over samples for each of the 256 guesses."""
    t, t_ss = _prep_traces(traces)
    pt = plaintexts[:, byte].astype(np.int64)

    # Predicted leakage for all 256 guesses at once: shape [n_traces, 256].
    guesses = np.arange(256, dtype=np.int64)
    inter = SBOX[np.bitwise_xor(pt[:, None], guesses[None, :])]
    hyp = HW[inter]
    hyp = hyp - hyp.mean(axis=0, keepdims=True)
    hyp_ss = np.sqrt((hyp ** 2).sum(axis=0))
    hyp_ss[hyp_ss == 0] = 1e-12

    # Correlation of every guess with every sample: [256, n_samples].
    corr = (hyp.T @ t) / (hyp_ss[:, None] * t_ss[None, :])
    return np.max(np.abs(corr), axis=1)


def recover_byte(traces, plaintexts, byte):
    corr = byte_correlations(traces, plaintexts, byte)
    best = int(np.argmax(corr))
    return best, float(corr[best]), corr


def recover_key(traces, plaintexts):
    """Recover all 16 key bytes. Returns (key[16], best_corr[16], corr_table[16,256])."""
    key = np.zeros(16, dtype=np.uint8)
    best = np.zeros(16)
    table = np.zeros((16, 256))
    for b in range(16):
        g, c, corr = recover_byte(traces, plaintexts, b)
        key[b] = g; best[b] = c; table[b] = corr
    return key, best, table
