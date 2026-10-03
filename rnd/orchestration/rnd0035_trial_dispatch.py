#!/usr/bin/env python3
"""Unified RND-0035 pair-trial dispatch for the frozen A-F matrix.

A/C/D/R000 continue through the staged adversarial kernel. E/F go through the
separately fixture-proven sensitive kernel. This module does not authorize
historical execution; the bounded runner remains the execution gate.
"""

from __future__ import annotations

from rnd0035_adversarial_kernel import run_trial_pair as run_standard_trial_pair
from rnd0035_sensitive_kernel import SENSITIVE_TRIALS, reconstruct_sensitive_pair


def run_declared_trial_pair(trial_id, symbol, rows):
    if trial_id in SENSITIVE_TRIALS:
        return reconstruct_sensitive_pair(trial_id, symbol, rows)
    return run_standard_trial_pair(trial_id, symbol, rows)
