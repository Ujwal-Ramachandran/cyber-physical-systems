"""Human-readable metadata about each protection, used by the UI and README."""
INFO = {
    "none": {
        "label": "Unprotected meter",
        "desc": "S-box output leaks directly through power. CPA recovers the key.",
        "cost": "None. Cheapest, and what many low-cost meters actually ship.",
    },
    "masking": {
        "label": "First-order Boolean masking",
        "desc": "Secret is split into two random shares; no single sample "
                "correlates with it, so first-order CPA fails.",
        "cost": "Moderate: ~2x compute/RAM, needs a good RNG. Standard defence.",
    },
    "shuffling": {
        "label": "Operation shuffling / hiding",
        "desc": "Randomises the time order of the 16 byte operations, smearing "
                "each leak across samples and lowering correlation.",
        "cost": "Low: cheap to add, often combined with masking for depth.",
    },
}
