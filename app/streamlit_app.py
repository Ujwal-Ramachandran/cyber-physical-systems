"""
Interactive live demo: Side-Channel Attack on a Smart Meter.

Run from the "CA 1" directory:
    streamlit run smartmeter_sca/app/streamlit_app.py

Slide the trace count and noise, pick a protection, hit "Run attack" and watch
the AES key fall out, then turn on masking and watch the attack fail.
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from smartmeter_sca.src.meter import SmartMeter
from smartmeter_sca.src import leakage, cpa, metrics
from smartmeter_sca.src.countermeasure import INFO

st.set_page_config(page_title="Smart Meter Side-Channel Demo", layout="wide")
st.title("Side-Channel Attack on a Smart Meter (CPS)")
st.caption("SE6012 CA1 demo. Real AES-128, real CPA, laptop-only, CPU. "
           "The attacker never sees the key.")

# Optional deep-link: ?auto=none|masking|shuffling runs immediately with that
# protection (used for screenshots / sharing a specific result). Normal use
# just presses the button.
_auto = st.query_params.get("auto")
if isinstance(_auto, list):
    _auto = _auto[0] if _auto else None
_auto = _auto if _auto in leakage.PROTECTIONS else None

with st.sidebar:
    st.header("Attack settings")
    n_traces = st.slider("Number of power traces", 100, 5000, 1500, step=100)
    noise = st.slider("Measurement noise (sigma)", 0.0, 6.0, 2.0, step=0.5)
    _default_idx = leakage.PROTECTIONS.index(_auto) if _auto else 0
    protection = st.radio("Meter protection",
                          leakage.PROTECTIONS, index=_default_idx,
                          format_func=lambda p: INFO[p]["label"])
    st.info(INFO[protection]["desc"])
    st.caption("Cost: " + INFO[protection]["cost"])
    run = st.button("Run attack", type="primary") or (_auto is not None)


@st.cache_data(show_spinner=False)
def run_attack(n_traces, noise, protection):
    meter = SmartMeter()
    key = meter.key_array()
    pts = meter.capture(n_traces)
    tr = leakage.simulate_traces(pts, key, noise_sigma=noise,
                                 protection=protection, seed=1)
    rec, best, table = cpa.recover_key(tr, pts)
    cps = np.unique(np.linspace(20, n_traces, 20).astype(int))
    ge = metrics.guessing_entropy_curve(tr, pts, key, cps)
    ttd, _ = metrics.traces_to_disclosure(tr, pts, key, 0, cps)
    return dict(key=key, rec=rec, best=best, table=table, traces=tr,
                cps=cps, ge=ge, ttd=ttd)


if run:
    r = run_attack(n_traces, noise, protection)
    key, rec = r["key"], r["rec"]
    ok = int((rec == key).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Key bytes recovered", f"{ok} / 16")
    c2.metric("Mean best correlation", f"{r['best'].mean():.3f}")
    c3.metric("Traces to disclosure (byte 0)", "n/a" if r["ttd"] < 0 else r["ttd"])

    if ok == 16:
        st.success("FULL AES-128 KEY RECOVERED. The meter's secret is broken.")
    elif ok <= 3:
        st.error("Attack defeated. The countermeasure stopped key recovery.")
    else:
        st.warning(f"Partial recovery: {ok}/16 bytes (raise traces or lower noise).")

    st.subheader("Recovered key vs true key")
    hexrow = lambda a: " ".join(f"{b:02x}" for b in a)
    marks = "".join("OK " if rec[i] == key[i] else "XX " for i in range(16))
    st.code(f"true      : {hexrow(key)}\nrecovered : {hexrow(rec)}\nmatch     : {marks}")

    left, right = st.columns(2)
    with left:
        st.subheader("Correlation vs key guess (byte 0)")
        fig, ax = plt.subplots(figsize=(5, 3.2))
        ax.plot(r["table"][0], lw=0.8)
        ax.axvline(key[0], color="r", ls="--", lw=1, label="true key byte")
        ax.set_xlabel("guess (0-255)"); ax.set_ylabel("max |corr|"); ax.legend()
        st.pyplot(fig)
    with right:
        st.subheader("Guessing entropy vs traces")
        fig2, ax2 = plt.subplots(figsize=(5, 3.2))
        ax2.plot(r["cps"], r["ge"], "-o", ms=3)
        ax2.axhline(0, color="gray", ls=":", lw=0.8)
        ax2.set_xlabel("number of traces"); ax2.set_ylabel("mean log2 rank")
        st.pyplot(fig2)

    st.subheader("Example simulated power traces")
    fig3, ax3 = plt.subplots(figsize=(9, 2.8))
    for i in range(6):
        ax3.plot(r["traces"][i], lw=0.6)
    ax3.set_xlabel("time sample"); ax3.set_ylabel("power (a.u.)")
    st.pyplot(fig3)
else:
    st.write("Set the parameters on the left and press **Run attack**.")
    st.markdown(
        "- **Unprotected** meter: the AES key is recovered from power alone.\n"
        "- **Masking / shuffling**: the identical attack fails.")
