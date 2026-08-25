"""Generate and save a reusable trace dataset (.npz) for offline experiments.

Usage: python -m smartmeter_sca.scripts.generate_traces --n 2000 --protection none
"""
from __future__ import annotations
import argparse, os
import numpy as np
from smartmeter_sca.src.meter import SmartMeter
from smartmeter_sca.src import leakage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--noise", type=float, default=2.0)
    ap.add_argument("--protection", default="none", choices=leakage.PROTECTIONS)
    args = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)

    meter = SmartMeter()
    key = meter.key_array()
    pts = meter.capture(args.n)
    tr = leakage.simulate_traces(pts, key, n_samples=args.samples,
                                 noise_sigma=args.noise, protection=args.protection, seed=1)
    out = os.path.join(DATA, f"traces_{args.protection}_{args.n}.npz")
    np.savez_compressed(out, traces=tr, plaintexts=pts, key=key,
                        protection=args.protection, noise=args.noise)
    print(f"saved {out}  traces={tr.shape}  (key is included only for evaluation)")


if __name__ == "__main__":
    main()
