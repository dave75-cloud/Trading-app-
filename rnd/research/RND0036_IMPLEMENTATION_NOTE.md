# RND-0036 Boundary-Aware Implementation Requirement

RND-0033 full-year structural loaders must not be reused unchanged for RND-0036.

The RND-0029 development partition ends **exclusively** at `2020-12-31T19:15:00Z`. Therefore RND-0036 requires a dedicated acquisition/quarantine wrapper that:

1. requests only `2020-01-01T00:00:00Z` through `2020-12-31T19:15:00Z` exclusive;
2. rejects any canonical row at or after the boundary;
3. records first/last canonical timestamps and an explicit boundary proof;
4. preserves raw response immutability and deterministic canonical SHA-256 identities;
5. reuses the existing OANDA PRACTICE bid/ask/mid complete-candle semantics;
6. emits structural evidence only and rejects strategy/outcome fields;
7. leaves validation/final, strategy selection, broker writes, sizing and capital authority false.

No calendar-year convenience function may widen the authorized interval.
