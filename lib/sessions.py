from datetime import datetime, time
def session_flags(dt_utc: datetime) -> dict:
    hhmm = dt_utc.time()
    def in_range(start: time, end: time):
        return start <= hhmm <= end
    return {
        "tokyo": in_range(time(0,0), time(9,0)),
        "london": in_range(time(7,0), time(16,0)),
        "newyork": in_range(time(12,0), time(21,0)),
    }
