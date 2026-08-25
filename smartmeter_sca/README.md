# Side-Channel Attack on a Smart Meter (CPS)

SE6012 Cyber-Physical System Security, CA1 demo. Team: Ujwal and Markie.

A laptop-only, CPU-only simulation that recovers a smart meter's AES-128 key
from its power consumption using Correlation Power Analysis (CPA), then defeats
the same attack with a masking countermeasure. No hardware, no oscilloscope, no
GPU, no paid tools.

## The one-line story

A smart meter encrypts its readings with AES-128, but the chip's power draw
depends on the data it processes. We simulate that leakage, run a real CPA
attack that recovers the secret key from the traces, connect that to the
Confidentiality / Integrity / Availability impact on the grid, and then
implement masking to show the attack becomes ineffective.

## What is real vs simulated (say this in the talk)

- Real: AES-128 (verified against the FIPS-197 test vector), the CPA algorithm
  (Brier, Clavier, Olivier, CHES 2004), and the masking / shuffling countermeasures.
- Modeled: the physical power measurement. Instead of an oscilloscope we use the
  standard Hamming-weight leakage model plus Gaussian noise. This is the accepted
  model used across the side-channel field and in teaching tools like ChipWhisperer.

The attacker code uses only the known AES input blocks, the traces, and the
public S-box. It never reads the key.

## Install (Windows PowerShell, venv named `cps`)

Open PowerShell and `cd` into the `CA 1` folder (the one containing
`smartmeter_sca/`), then create and activate a virtual environment called `cps`:

```powershell
# 1) create the environment (once)
python -m venv cps

# 2) activate it (every new PowerShell session)
.\cps\Scripts\Activate.ps1

# 3) install dependencies into cps
python -m pip install --upgrade pip
pip install -r smartmeter_sca\requirements.txt
```

Once activated, your prompt shows `(cps)` at the front. Only NumPy is strictly
required for the attack; Matplotlib is for plots and Streamlit for the UI.

If step 2 is blocked by "running scripts is disabled on this system", allow it
for your user once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\cps\Scripts\Activate.ps1
```

To leave the environment later: `deactivate`.

## Run (from `CA 1`, with `(cps)` active)

```powershell
# 1) Full attack with metrics + saved figures
python -m smartmeter_sca.scripts.run_attack --n 1500 --noise 2.0

# 2) Interactive live demo (the +5% moment)
streamlit run smartmeter_sca\app\streamlit_app.py

# 3) Tests (AES vector + attack sanity)
python -m pytest -q

# 4) Save a reusable trace dataset
python -m smartmeter_sca.scripts.generate_traces --n 2000 --protection none
```

## Accessing the Streamlit UI

```powershell
# from the CA 1 folder, in the same PowerShell window
.\cps\Scripts\Activate.ps1                          # if not already active
streamlit run smartmeter_sca\app\streamlit_app.py
```

When it starts, Streamlit prints something like:

```
  Local URL:   http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

It normally opens your browser automatically. If not, open
**http://localhost:8501** yourself. In the app: set the sliders (trace count,
noise) and the protection on the left, then click **Run attack**.

Useful variants:

```powershell
# pick a specific port if 8501 is busy
streamlit run smartmeter_sca\app\streamlit_app.py --server.port 8502

# present from another laptop on the same Wi-Fi: share the Network URL shown
# stop the server: press Ctrl + C in the terminal
```

If `streamlit` is not recognised after install, run it via Python:

```powershell
python -m streamlit run smartmeter_sca\app\streamlit_app.py
```

## What you will see

- Unprotected meter: 16 / 16 AES key bytes recovered; the correct guess spikes
  far above the noise floor in the correlation plot.
- Masking or shuffling on: 0 / 16 recovered; no guess stands out.
- Metrics: traces-to-disclosure, guessing-entropy curve, and full-key success
  rate over repeated trials.

## How it maps to the CA1 rubric

- Positive CPS use case: smart-meter / AMI (accurate billing, outage detection,
  demand response, renewables and EV integration).
- Three CIA issues:
  - Confidentiality (deep-dive): power side channel leaks the AES key.
  - Integrity: with the key, forge meter readings or grid telemetry.
  - Availability: with the key, replay or issue mass remote-disconnect commands.
- Deep dive: the CPA attack above, with consequences across safety, operations,
  and reputation.
- Mitigations (technical / organizational / procedural): masking and hiding
  (implemented here), per-device key diversification, secure element / root of
  trust, authenticated lightweight crypto (ASCON), and PQC for long-lived keys.

## Layout

```
smartmeter_sca/
  src/aes.py             real AES-128 + S-box + Hamming weight
  src/meter.py           SmartMeter: readings -> AES input blocks
  src/leakage.py         power-trace simulation (none / masking / shuffling)
  src/cpa.py             CPA attack + key recovery
  src/metrics.py         traces-to-disclosure, guessing entropy, success rate
  src/countermeasure.py  human-readable protection info
  scripts/run_attack.py  end-to-end run with figures + metrics
  scripts/generate_traces.py
  app/streamlit_app.py   interactive live demo
  tests/test_cpa.py      AES vector + attack sanity tests
  figures/  data/
```

## Honest caveats for Q&A

Real traces are noisier and misaligned, so a real attack needs trace alignment
and more traces. Our simulation places the leak at a known sample. The CPA
principle, the AES, and the countermeasures are identical to the real thing; only
the measurement is modeled. A natural next step is to run the same CPA against a
real measured dataset (ChipWhisperer / ASCAD).
