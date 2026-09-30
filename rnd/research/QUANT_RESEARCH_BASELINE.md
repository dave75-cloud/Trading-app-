# Quantitative research baseline

Status: R&D CANDIDATE / NON-OPERATIONAL
Task: RND-0025
Strategy search or selection: PROHIBITED
Human merge/promotion decision: REQUIRED

## Purpose

RND-0025 defines the measuring instrument for later quantitative research. It
does not optimize M005, Champion, or any other strategy and it does not claim
that a historical result is profitable or tradeable.

A future experiment is reviewable only when its data identity, hypothesis,
search space, chronological partitions, simulator semantics, trial count and
validation plan are declared before results are used to select a candidate.

## Research-data contract

Every dataset snapshot must identify:

- immutable snapshot ID and SHA-256;
- provider, symbol and timeframe;
- UTC start/end bounds;
- available price components;
- completeness status; and
- non-empty provenance describing how the snapshot was obtained or derived.

Venue-aligned execution research should preserve bid and ask where available.
Mid-only data may be useful for signal research, but cannot silently stand in
for bid/ask execution evidence.

Raw snapshots are immutable inputs. Corrections create a new snapshot identity;
they do not rewrite the evidence behind an earlier experiment.

## Experiment protocol

Before evaluation, declare:

- one falsifiable objective/hypothesis;
- strategy family;
- complete finite parameter search space;
- declared trial count;
- chronological development, validation and final-test windows;
- predetermined metrics; and
- the simulator and validation contract below.

The declared trial count must equal the Cartesian size of the declared search
space. Failed and unattractive trials still count. A later extension is a new
experiment or an explicitly versioned amendment; it is not silently folded into
the original winner.

The final-test window is not used to choose parameters. RND-0025 itself performs
no parameter search and selects no strategy.

## Event-driven simulator standard

Performance-grade research must model explicit entries and exits rather than
editing completed returns after the fact. The baseline requires:

- event-driven state transitions;
- explicit entry/exit semantics;
- bid/ask-aware transaction costs;
- simultaneous/overlapping positions;
- mark-to-market portfolio equity;
- currency-leg exposure;
- no future-bar access; and
- no synthetic return clipping.

A real stop-loss can be modelled only as an executable rule using price-path
information available at that time. Clipping a completed losing return to a
fixed floor while leaving winning returns unchanged is not stop-loss simulation
and is prohibited as performance evidence.

## Validation standard

The declared plan requires chronological out-of-sample evaluation, parameter
perturbation, subperiod/regime analysis, multiple-testing accounting,
dependence-aware resampling, and sufficient retained statistics for later PBO
and Deflated-Sharpe-style analysis.

These declarations do not prove statistical validity. They make omissions and
post-hoc changes machine-detectable and preserve the information needed for
later independent analysis.

## Authority boundary

The contract grants no strategy-selection, broker-write, merge, promotion or
capital authority. A structurally valid research declaration is not evidence of
economic edge and never changes canonical M005 or frozen M006e.
