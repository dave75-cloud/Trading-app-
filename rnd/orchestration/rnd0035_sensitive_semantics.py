#!/usr/bin/env python3
"""Pure outcome-blind state machines for RND-0035 E/F sensitive semantics.

These helpers contain no market-history loading, P&L calculation, broker access,
strategy selection, promotion, capital authority, validation access, or file writes.
They exist so sensitive execution/gap rules can be fixture-proven before integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

M5 = timedelta(minutes=5)


class RND0035SensitiveSemanticsError(ValueError):
    pass


def _check_dt(dt):
    if not isinstance(dt, datetime) or dt.tzinfo is None:
        raise RND0035SensitiveSemanticsError("timezone-aware datetime required")
    if dt.second or dt.microsecond or dt.minute % 5:
        raise RND0035SensitiveSemanticsError("observation must be on M5 grid")


@dataclass
class HundredBarCooldown:
    """E002 entry eligibility after 100 fully observed contiguous post-gap bars."""

    suppressed: bool = False
    contiguous_count: int = 0
    previous_dt: datetime | None = None

    def on_gap(self):
        self.suppressed = True
        self.contiguous_count = 0
        self.previous_dt = None

    def observe(self, dt):
        _check_dt(dt)
        if not self.suppressed:
            self.previous_dt = dt
            return True
        if self.previous_dt is None:
            self.contiguous_count = 1
        elif dt - self.previous_dt == M5:
            self.contiguous_count += 1
        else:
            self.contiguous_count = 1
        self.previous_dt = dt
        # Bar 100 is processed under suppression; eligibility starts on bar 101.
        if self.contiguous_count >= 101:
            self.suppressed = False
            return True
        return False


@dataclass
class CompleteSessionCooldown:
    """E001 entry eligibility after one entire reference session is observed."""

    session_start_hour: int
    session_end_hour: int
    suppressed: bool = False
    previous_dt: datetime | None = None
    candidate_date: object | None = None
    candidate_count: int = 0
    session_completed: bool = False

    def __post_init__(self):
        if not (0 <= self.session_start_hour < self.session_end_hour <= 24):
            raise RND0035SensitiveSemanticsError("invalid session")

    @property
    def expected_bars(self):
        return (self.session_end_hour - self.session_start_hour) * 12

    def on_gap(self):
        self.suppressed = True
        self.previous_dt = None
        self.candidate_date = None
        self.candidate_count = 0
        self.session_completed = False

    def _in_session(self, dt):
        return dt.weekday() < 5 and self.session_start_hour <= dt.hour < self.session_end_hour

    def _is_session_open(self, dt):
        return dt.weekday() < 5 and dt.hour == self.session_start_hour and dt.minute == 0

    def observe(self, dt):
        _check_dt(dt)
        if not self.suppressed:
            self.previous_dt = dt
            return True

        # Eligibility resumes only on first genuine observation after a complete
        # qualifying session has ended.
        if self.session_completed:
            self.suppressed = False
            self.previous_dt = dt
            return True

        contiguous = self.previous_dt is None or dt - self.previous_dt == M5
        if not contiguous:
            self.candidate_date = None
            self.candidate_count = 0

        if self._is_session_open(dt):
            self.candidate_date = dt.date()
            self.candidate_count = 1
        elif self._in_session(dt) and self.candidate_date == dt.date() and contiguous:
            self.candidate_count += 1
        elif self._in_session(dt):
            # Starting mid-session can never qualify that session.
            self.candidate_date = None
            self.candidate_count = 0

        if (
            self.candidate_date == dt.date()
            and self.candidate_count == self.expected_bars
            and dt.hour == self.session_end_hour - 1
            and dt.minute == 55
        ):
            self.session_completed = True

        self.previous_dt = dt
        return False


@dataclass
class PendingEntry:
    """F001 one-observed-bar conservative entry latency."""

    side: int
    created_at: datetime

    def __post_init__(self):
        if self.side not in (-1, 1):
            raise RND0035SensitiveSemanticsError("entry side must be -1 or 1")
        _check_dt(self.created_at)

    def resolve(self, dt, fresh_instruction):
        _check_dt(dt)
        if dt - self.created_at != M5:
            return "CANCEL_GAP_OR_NONCONTIGUOUS"
        if fresh_instruction in (0, -self.side):
            return "CANCEL_CONTRADICTED"
        return "EXECUTE"


@dataclass
class PendingExit:
    """F002 one-observed-bar exit latency with no synthetic gap fill."""

    side: int
    created_at: datetime

    def __post_init__(self):
        if self.side not in (-1, 1):
            raise RND0035SensitiveSemanticsError("exit side must be -1 or 1")
        _check_dt(self.created_at)

    def resolve(self, dt):
        _check_dt(dt)
        return {
            "action": "EXECUTE",
            "gap_exposed": dt - self.created_at != M5,
        }


def reversal_action(no_same_observation_reentry, current_side, desired_side):
    """F004 decision primitive for a delayed reversal instruction."""
    if current_side not in (-1, 1):
        raise RND0035SensitiveSemanticsError("current position required")
    if desired_side != -current_side:
        raise RND0035SensitiveSemanticsError("opposite desired side required")
    if no_same_observation_reentry:
        return "EXIT_ONLY_NO_CARRIED_ENTRY"
    return "EXIT_AND_REENTER"
