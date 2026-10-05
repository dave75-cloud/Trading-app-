# RND-0060C — Execution-State Clarification

Status: PRE-OUTCOME / FROZEN

Before any RND-0060C outcome code or development run, the following execution-state rule is frozen to make the economic-position semantics complete:

- RND-0060C permits at most one open economic position across the four-pair research portfolio at a time.
- If a prior RND-0060C position remains open at a later day's 11:30 UTC decision time because missing observations delayed its three genuine post-entry holding bars, no new RND-0060C signal or entry is permitted that day.
- The existing position continues under frozen RND-0034 gap semantics until three genuine observed post-entry bars have accrued.
- This rule does not change the signal definition, selected-pair rule, observation time, peer construction, holding period, or falsification criteria.

No outcomes were inspected before this clarification was frozen.
