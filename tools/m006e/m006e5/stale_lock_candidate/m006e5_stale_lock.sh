#!/bin/bash

# M006e.5a conservative stale-lock helper.
#
# Required:
#   LOCKDIR
#
# Optional:
#   LOCK_STALE_SECONDS
#
# Rules:
# - clean mkdir => acquire
# - live matching owner => do not reclaim
# - recent orphan/uncertain lock => do not reclaim
# - old dead/mismatched owner => atomic quarantine + reacquire
#
# No network activity.
# No trading/order capability.

LOCK_STALE_SECONDS="${LOCK_STALE_SECONDS:-900}"


m006e5_lock_now_epoch() {
    date -u '+%s'
}


m006e5_lock_owner_command() {
    _pid="$1"

    ps -p "$_pid" -o command= 2>/dev/null || true
}


m006e5_lock_age_seconds() {
    _now="$1"
    _created=""

    if [ -f "$LOCKDIR/created_epoch" ]; then
        _created="$(
            cat "$LOCKDIR/created_epoch" 2>/dev/null || true
        )"
    fi

    case "$_created" in
        ''|*[!0-9]*)
            # macOS fallback to directory mtime.
            _created="$(
                stat -f '%m' "$LOCKDIR" 2>/dev/null || true
            )"
            ;;
    esac

    case "$_created" in
        ''|*[!0-9]*)
            echo "-1"
            return 0
            ;;
    esac

    _age=$((_now - _created))

    if [ "$_age" -lt 0 ]; then
        echo "-1"
    else
        echo "$_age"
    fi
}


m006e5_write_lock_metadata() {
    _now="$1"

    printf '%s\n' "$$" > "$LOCKDIR/pid"
    printf '%s\n' "$_now" > "$LOCKDIR/created_epoch"
    printf '%s\n' \
      "run_m006e5_cycle.sh" \
      > "$LOCKDIR/owner_tag"
}


m006e5_acquire_lock() {
    if [ -z "${LOCKDIR:-}" ]; then
        echo "FAIL_CLOSED: LOCKDIR is unset"
        return 2
    fi

    _now="$(
        m006e5_lock_now_epoch
    )"

    if mkdir "$LOCKDIR" 2>/dev/null; then
        m006e5_write_lock_metadata "$_now"
        echo "LOCK_ACQUIRED: clean"
        return 0
    fi

    _pid=""

    if [ -f "$LOCKDIR/pid" ]; then
        _pid="$(
            cat "$LOCKDIR/pid" 2>/dev/null || true
        )"
    fi

    _age="$(
        m006e5_lock_age_seconds "$_now"
    )"

    _owner_live="false"
    _owner_matching="false"

    case "$_pid" in
        ''|*[!0-9]*)
            ;;
        *)
            if kill -0 "$_pid" 2>/dev/null; then
                _owner_live="true"

                _cmd="$(
                    m006e5_lock_owner_command "$_pid"
                )"

                case "$_cmd" in
                    *run_m006e5_cycle.sh*)
                        _owner_matching="true"
                        ;;
                esac
            fi
            ;;
    esac

    if [ "$_owner_live" = "true" ] \
       && [ "$_owner_matching" = "true" ]
    then
        echo \
          "LOCK_BUSY: live matching owner pid=$_pid age=${_age}s"
        return 1
    fi

    # Fail closed if we cannot establish that the lock is old.
    case "$_age" in
        ''|*[!0-9]*)
            echo \
              "LOCK_BUSY: age unknown; refusing stale recovery"
            return 1
            ;;
    esac

    if [ "$_age" -lt "$LOCK_STALE_SECONDS" ]; then
        echo \
          "LOCK_BUSY: recent orphan/uncertain lock age=${_age}s"
        return 1
    fi

    _quarantine="${LOCKDIR}.stale.$$"

    # Atomic rename prevents two concurrent recovery attempts from
    # deleting or stealing the same lock.
    if ! mv "$LOCKDIR" "$_quarantine" 2>/dev/null; then
        echo \
          "LOCK_BUSY: stale-lock recovery race lost"
        return 1
    fi

    if ! mkdir "$LOCKDIR" 2>/dev/null; then
        # Another process acquired after quarantine.
        echo \
          "LOCK_BUSY: another process acquired during recovery"
        return 1
    fi

    m006e5_write_lock_metadata "$_now"

    rm -rf "$_quarantine"

    echo \
      "LOCK_ACQUIRED: stale lock recovered age=${_age}s old_pid=${_pid:-unknown}"

    return 0
}


m006e5_release_lock() {
    if [ -z "${LOCKDIR:-}" ]; then
        return 0
    fi

    if [ ! -d "$LOCKDIR" ]; then
        return 0
    fi

    _pid=""

    if [ -f "$LOCKDIR/pid" ]; then
        _pid="$(
            cat "$LOCKDIR/pid" 2>/dev/null || true
        )"
    fi

    # Never remove a lock that now belongs to another process.
    if [ "$_pid" != "$$" ]; then
        echo \
          "LOCK_RELEASE_SKIPPED: owner changed pid=${_pid:-unknown}"
        return 0
    fi

    rm -f \
      "$LOCKDIR/pid" \
      "$LOCKDIR/created_epoch" \
      "$LOCKDIR/owner_tag"

    rmdir "$LOCKDIR" 2>/dev/null || true
}
