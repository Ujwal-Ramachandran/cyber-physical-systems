"""
Side-Channel Attack on a Smart Meter (CPS) - laptop-only proof of concept.

What this shows, end to end, in pure Python + NumPy:
  1. Simulate a smart meter encrypting a reading with AES-128.
  2. Simulate the physical power leakage of that computation (Hamming-weight
     model + Gaussian noise) -> synthetic power traces.
  3. Run Correlation Power Analysis (CPA) and recover the secret key byte(s).
  4. Turn on a first-order Boolean MASKING countermeasure and run the SAME
     attack again -> key recovery collapses.

No hardware, no oscilloscope, no crypto library required. CPU only.
Only dependency is numpy (matplotlib optional, just for the plot).

Run:  python cpa_smartmeter_demo.py
"""

import numpy as np

# ---------------------------------------------------------------------------
# AES S-box. CPA on AES targets the first-round S-box output:
#     intermediate = SBox[ plaintext_byte XOR key_byte ]
# so we only need this 256-byte table, NOT a full AES implementation.
# ---------------------------------------------------------------------------
SBOX = np.array([
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
], dtype=np.uint8)

# Precompute Hamming weight (number of set bits) for every byte value 0..255.
HW = np.array([bin(x).count("1") for x in range(256)], dtype=np.float64)

# The meter's real secret key (the attacker does NOT get to use this).
SECRET_KEY = np.array([
    0x2b,0x7e,0x15,0x16,0x28,0xae,0xd2,0xa6,
    0xab,0xf7,0x15,0x88,0x09,0xcf,0x4f,0x3c
], dtype=np.uint8)


# ---------------------------------------------------------------------------
# Steps 1-3: simulate the meter + its power leakage and produce traces.
# ---------------------------------------------------------------------------
def simulate_traces(n_traces, n_samples, key, noise_sigma, masked, rng):
    """
    Return (traces, plaintexts).
      traces: float array [n_traces, n_samples]  (synthetic power measurements)
      plaintexts: uint8 array [n_traces, 16]     (the meter readings, known to attacker)

    The leaking operation sits at one 'time sample'; every other sample is noise,
    exactly like a real trace where the S-box lookup happens at one instant.
    """
    plaintexts = rng.integers(0, 256, size=(n_traces, 16), dtype=np.uint8)

    # Baseline traces = pure Gaussian noise.
    traces = rng.normal(0.0, noise_sigma, size=(n_traces, n_samples))

    # Pick which sample index each key byte leaks at (spread across the trace).
    leak_points = np.linspace(5, n_samples - 5, num=16).astype(int)

    for byte_i in range(16):
        inter = SBOX[plaintexts[:, byte_i] ^ key[byte_i]]  # true S-box output

        if not masked:
            # Unprotected device: power depends directly on the secret intermediate.
            leakage = HW[inter]
        else:
            # First-order Boolean masking: process (inter XOR m) and m separately,
            # with a fresh random mask m per encryption. The device never handles
            # `inter` directly, so no single sample correlates with the secret.
            m = rng.integers(0, 256, size=n_traces, dtype=np.uint8)
            masked_val = inter ^ m
            leakage = HW[masked_val]  # attacker sees the MASKED value's leakage

        # Inject the data-dependent leakage into that byte's time sample.
        traces[:, leak_points[byte_i]] += leakage

    return traces, plaintexts


# ---------------------------------------------------------------------------
# Step 4-5: the CPA attack. Recover one key byte by trying all 256 guesses.
# ---------------------------------------------------------------------------
def cpa_recover_byte(traces, plaintexts, byte_i):
    """Return (best_guess, best_corr, corr_per_guess[256])."""
    pt = plaintexts[:, byte_i]

    # Center traces once (for Pearson correlation).
    t = traces - traces.mean(axis=0, keepdims=True)
    t_ss = np.sqrt((t ** 2).sum(axis=0))
    t_ss[t_ss == 0] = 1e-12

    best_corr = np.zeros(256)
    for guess in range(256):
        # Hypothetical leakage for this key guess.
        hyp = HW[SBOX[pt ^ guess]].astype(np.float64)
        hyp -= hyp.mean()
        hyp_ss = np.sqrt((hyp ** 2).sum()) or 1e-12

        # Correlate hypothesis with every time sample; keep the strongest.
        corr = (t * hyp[:, None]).sum(axis=0) / (t_ss * hyp_ss)
        best_corr[guess] = np.max(np.abs(corr))

    best_guess = int(np.argmax(best_corr))
    return best_guess, best_corr[best_guess], best_corr


def attack_all_bytes(traces, plaintexts, label):
    print(f"\n{'='*54}\n  CPA ATTACK - {label}\n{'='*54}")
    recovered = np.zeros(16, dtype=np.uint8)
    ok = 0
    for i in range(16):
        g, c, _ = cpa_recover_byte(traces, plaintexts, i)
        recovered[i] = g
        hit = (g == SECRET_KEY[i])
        ok += hit
        mark = "OK " if hit else "XX "
        print(f"  byte {i:2d}: actual=0x{SECRET_KEY[i]:02x}  "
              f"recovered=0x{g:02x}  corr={c:0.3f}  {mark}")
    print(f"  ----> {ok}/16 key bytes recovered")
    return recovered, ok


def main():
    rng = np.random.default_rng(2026)

    N_TRACES = 1000     # meter encrypts 1000 readings
    N_SAMPLES = 200     # points sampled per trace
    NOISE = 2.0         # measurement noise (HW signal ranges 0..8)

    print("Smart-Meter Side-Channel PoC  (pure NumPy, CPU only)")
    print(f"Traces: {N_TRACES}   Samples/trace: {N_SAMPLES}   Noise sigma: {NOISE}")
    print(f"True key: {' '.join(f'{b:02x}' for b in SECRET_KEY)}")

    import time

    # ---- Attack 1: UNPROTECTED meter -> key should fall out. ----
    t0 = time.time()
    tr, pt = simulate_traces(N_TRACES, N_SAMPLES, SECRET_KEY, NOISE,
                             masked=False, rng=rng)
    rec_u, ok_u = attack_all_bytes(tr, pt, "UNPROTECTED METER")
    # Show the byte-0 guess ranking so the demo has a clear "spike".
    _, _, corr0 = cpa_recover_byte(tr, pt, 0)
    top = np.argsort(corr0)[::-1][:5]
    print("  byte 0 top-5 guesses:",
          ", ".join(f"0x{g:02x}:{corr0[g]:0.3f}" for g in top))

    # ---- Attack 2: MASKED meter, identical attack -> should fail. ----
    tr_m, pt_m = simulate_traces(N_TRACES, N_SAMPLES, SECRET_KEY, NOISE,
                                 masked=True, rng=rng)
    rec_m, ok_m = attack_all_bytes(tr_m, pt_m, "MASKED METER (mitigation on)")
    _, _, corr0m = cpa_recover_byte(tr_m, pt_m, 0)
    print(f"  byte 0 best correlation with masking: {np.max(corr0m):0.3f} "
          f"(vs {np.max(corr0):0.3f} unprotected)")
    dt = time.time() - t0

    print(f"\n{'='*54}\n  RESULT")
    print(f"  Unprotected : {ok_u}/16 bytes recovered  -> key BROKEN")
    print(f"  Masked      : {ok_m}/16 bytes recovered  -> attack DEFEATED")
    print(f"  Total runtime: {dt:0.2f} s")
    print("="*54)

    # Optional plot (only if matplotlib is present).
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(range(256), corr0, lw=0.8)
        ax[0].axvline(SECRET_KEY[0], color="r", ls="--", lw=1, label="true key byte")
        ax[0].set_title("Unprotected: correct key byte spikes")
        ax[0].set_xlabel("key-byte guess"); ax[0].set_ylabel("max |correlation|")
        ax[0].legend()
        ax[1].plot(range(256), corr0m, lw=0.8, color="green")
        ax[1].axvline(SECRET_KEY[0], color="r", ls="--", lw=1, label="true key byte")
        ax[1].set_title("Masked: no guess stands out")
        ax[1].set_xlabel("key-byte guess"); ax[1].set_ylabel("max |correlation|")
        ax[1].legend()
        fig.tight_layout()
        fig.savefig("cpa_result.png", dpi=120)
        print("Saved plot: cpa_result.png")
    except Exception as e:
        print(f"(plot skipped: {e})")


if __name__ == "__main__":
    main()
