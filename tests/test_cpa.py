"""Correctness + attack sanity tests. Run:  python -m pytest -q  (from CA 1)."""
import numpy as np
from smartmeter_sca.src import aes, cpa, leakage
from smartmeter_sca.src.meter import SmartMeter


def test_aes_fips_vector():
    pt = bytes.fromhex("00112233445566778899aabbccddeeff")
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    assert aes.encrypt_block(pt, key).hex() == "69c4e0d86a7b0430d8cdb78070b4c55a"


def test_aes_second_vector():
    pt = bytes.fromhex("3243f6a8885a308d313198a2e0370734")
    key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
    assert aes.encrypt_block(pt, key).hex() == "3925841d02dc09fbdc118597196a0b32"


def test_cpa_recovers_full_key_low_noise():
    m = SmartMeter(); key = m.key_array(); pts = m.capture(1000)
    tr = leakage.simulate_traces(pts, key, noise_sigma=1.0, protection="none", seed=3)
    rec, _, _ = cpa.recover_key(tr, pts)
    assert (rec == key).all()


def test_masking_defeats_attack():
    m = SmartMeter(); key = m.key_array(); pts = m.capture(1000)
    tr = leakage.simulate_traces(pts, key, noise_sigma=2.0, protection="masking", seed=3)
    rec, _, _ = cpa.recover_key(tr, pts)
    assert (rec == key).sum() <= 3          # at most chance-level hits


def test_shuffling_defeats_attack():
    m = SmartMeter(); key = m.key_array(); pts = m.capture(1000)
    tr = leakage.simulate_traces(pts, key, noise_sigma=2.0, protection="shuffling", seed=3)
    rec, _, _ = cpa.recover_key(tr, pts)
    assert (rec == key).sum() <= 3
