"""
End-to-end CPA attack on the simulated smart meter, with plots and metrics.

Usage:
    python -m smartmeter_sca.scripts.run_attack            # defaults
    python -m smartmeter_sca.scripts.run_attack --n 2000 --noise 3.0
Run from the "CA 1" directory.
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from smartmeter_sca.src.meter import SmartMeter
from smartmeter_sca.src import leakage, cpa, metrics

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(HERE, "figures")


def banner(t): print("\n" + "=" * 60 + f"\n  {t}\n" + "=" * 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1500, help="number of traces")
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--noise", type=float, default=2.0)
    ap.add_argument("--trials", type=int, default=15, help="trials for success rate")
    args = ap.parse_args()
    os.makedirs(FIG, exist_ok=True)

    meter = SmartMeter()
    key = meter.key_array()
    print(f"Traces={args.n}  Samples={args.samples}  Noise sigma={args.noise}")
    print("True key:", " ".join(f"{b:02x}" for b in key))

    pts = meter.capture(args.n)
    results = {}
    for prot in leakage.PROTECTIONS:
        tr = leakage.simulate_traces(pts, key, n_samples=args.samples,
                                     noise_sigma=args.noise, protection=prot, seed=1)
        rec, best, table = cpa.recover_key(tr, pts)
        ok = int((rec == key).sum())
        results[prot] = (tr, rec, best, table, ok)
        banner(f"{prot.upper()}  ->  {ok}/16 key bytes recovered")
        print("recovered:", " ".join(f"{b:02x}" for b in rec))
        print(f"mean best |correlation| = {best.mean():.3f}")

    # ---- Figure 1: correlation vs key guess (byte 0), none vs masking ----
    _, _, _, tbl_n, _ = results["none"]
    _, _, _, tbl_m, _ = results["masking"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(tbl_n[0], lw=0.8); ax[0].axvline(key[0], color="r", ls="--", lw=1,
              label="true key byte")
    ax[0].set_title("Unprotected: correct key byte spikes")
    ax[0].set_xlabel("key-byte guess"); ax[0].set_ylabel("max |correlation|"); ax[0].legend()
    ax[1].plot(tbl_m[0], lw=0.8, color="green"); ax[1].axvline(key[0], color="r",
              ls="--", lw=1, label="true key byte")
    ax[1].set_title("Masked: no guess stands out")
    ax[1].set_xlabel("key-byte guess"); ax[1].set_ylabel("max |correlation|"); ax[1].legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_correlation.png"), dpi=120)

    # ---- Figure 2: traces-to-disclosure / guessing entropy ----
    cps = np.unique(np.linspace(20, args.n, 25).astype(int))
    ge_n = metrics.guessing_entropy_curve(results["none"][0], pts, key, cps)
    ge_m = metrics.guessing_entropy_curve(results["masking"][0], pts, key, cps)
    ttd, _ = metrics.traces_to_disclosure(results["none"][0], pts, key, 0, cps)
    fig2, ax2 = plt.subplots(figsize=(7, 4.5))
    ax2.plot(cps, ge_n, "-o", ms=3, label="unprotected")
    ax2.plot(cps, ge_m, "-o", ms=3, color="green", label="masked")
    ax2.axhline(0, color="gray", lw=0.8, ls=":")
    ax2.set_xlabel("number of traces"); ax2.set_ylabel("guessing entropy (mean log2 rank)")
    ax2.set_title("Attack strength vs traces (lower = key more broken)")
    ax2.legend(); fig2.tight_layout()
    fig2.savefig(os.path.join(FIG, "fig2_guessing_entropy.png"), dpi=120)

    # ---- Figure 3: example traces ----
    fig3, ax3 = plt.subplots(figsize=(7, 3.5))
    for i in range(6):
        ax3.plot(results["none"][0][i], lw=0.6)
    ax3.set_title("Example simulated power traces (unprotected)")
    ax3.set_xlabel("time sample"); ax3.set_ylabel("power (a.u.)")
    fig3.tight_layout(); fig3.savefig(os.path.join(FIG, "fig3_traces.png"), dpi=120)

    # ---- Success rate over repeated experiments ----
    banner("METRICS")
    print(f"byte 0 traces-to-disclosure (unprotected): {ttd} traces")
    sr_n, _ = metrics.success_rate(meter.capture, key, n_trials=args.trials,
                                   n_traces=args.n, noise_sigma=args.noise, protection="none")
    sr_m, _ = metrics.success_rate(meter.capture, key, n_trials=args.trials,
                                   n_traces=args.n, noise_sigma=args.noise, protection="masking")
    print(f"full-key success rate over {args.trials} trials:")
    print(f"   unprotected : {sr_n*100:5.1f}%")
    print(f"   masked      : {sr_m*100:5.1f}%")
    print(f"\nFigures saved in {FIG}")
    print("Summary:", {k: v[4] for k, v in results.items()}, "(bytes recovered / 16)")


if __name__ == "__main__":
    main()
