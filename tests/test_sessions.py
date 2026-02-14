from datetime import datetime, timezone

from lib.sessions import session_flags


def test_session_flags_boundaries():
    # Tokyo inclusive
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert session_flags(t0)["tokyo"] is True
    t1 = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    assert session_flags(t1)["tokyo"] is True
    t2 = datetime(2024, 1, 1, 9, 1, tzinfo=timezone.utc)
    assert session_flags(t2)["tokyo"] is False

    # London inclusive
    l0 = datetime(2024, 1, 1, 7, 0, tzinfo=timezone.utc)
    assert session_flags(l0)["london"] is True
    l1 = datetime(2024, 1, 1, 16, 0, tzinfo=timezone.utc)
    assert session_flags(l1)["london"] is True
    l2 = datetime(2024, 1, 1, 16, 1, tzinfo=timezone.utc)
    assert session_flags(l2)["london"] is False
