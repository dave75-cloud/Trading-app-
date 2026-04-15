def can_trade(open_positions: int, daily_pnl: float) -> bool:
    if open_positions > 0:
        return False

    if daily_pnl <= -0.005:
        return False

    return True