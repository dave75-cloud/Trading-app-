import pandas as pd

from features.atr import atr


def test_atr_matches_known_case():
    # Construct a tiny deterministic series where true range is constant (=2)
    df = pd.DataFrame(
        {
            "h": [2, 3, 4, 5],
            "l": [0, 1, 2, 3],
            "c": [1, 2, 3, 4],
        }
    )
    out = atr(df, period=2)
    # For rows 1.., TR is max(h-l, |h-prev_c|, |l-prev_c|) = 2 always
    assert out.isna().iloc[0]
    assert float(out.iloc[1]) == 2.0
    assert float(out.iloc[2]) == 2.0
    assert float(out.iloc[3]) == 2.0
