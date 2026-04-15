import pandas as pd
from execution.signal_engine import generate_signal
from execution.risk_manager import can_trade
from execution.trade_logger import log_trade


def main():
    df = pd.read_csv("./data/resampled/GBPUSD_5m.csv")

    signal = generate_signal(df)

    if not can_trade(open_positions=0, daily_pnl=0.0):
        print("Risk filter blocked trade")
        return

    latest = df.iloc[-1]

    if signal == 1:
        print("PAPER BUY")
        log_trade(latest["ts"], "GBPUSD", "BUY", latest["c"])

    elif signal == -1:
        print("PAPER SELL")
        log_trade(latest["ts"], "GBPUSD", "SELL", latest["c"])

    else:
        print("NO TRADE")


if __name__ == "__main__":
    main()