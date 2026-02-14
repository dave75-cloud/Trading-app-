from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd

from backtest.engine import monthly_walkforward


@dataclass
class ExecConfig:
    symbol: str = "GBPUSD"
    horizon_bars: int = 6
    mt5_live: bool = False


class ExecutionService:
    """Thin orchestration layer.

    Phase-2: swaps in live execution via MT5 when explicitly enabled.
    For now, dry_run() is the default and is CI-safe.
    """

    def __init__(self, config: Optional[ExecConfig] = None):
        self.cfg = config or ExecConfig()

    def dry_run(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """Runs a no-broker simulation over a candle frame."""
        out = monthly_walkforward(candles, horizon_bars=self.cfg.horizon_bars)
        return {
            "symbol": self.cfg.symbol,
            "horizon_bars": self.cfg.horizon_bars,
            **out,
        }

    def place_order(self, *args, **kwargs) -> Dict[str, Any]:
        """MT5 live toggle scaffolding (no-op unless explicitly enabled)."""
        if not self.cfg.mt5_live:
            return {"accepted": False, "reason": "mt5_live disabled", "dry": True}
        # Import only when needed to keep CI clean.
        from mt5_bridge.bridge import place_order as _mt5_place_order

        return _mt5_place_order(*args, **kwargs, live=True)
