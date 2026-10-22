"""Same regional catalog values; untanglepy additionally records source rows."""

import pandas as pd
from pandas.testing import assert_frame_equal

from untanglepy import untangle


def baseline(raw):
    labels = raw["item"].astype("string")
    headers = labels.str.match("^REGION:").fillna(False)
    groups = labels.str.replace("^REGION:", "", regex=True).str.strip().where(headers).ffill()
    frame = raw.loc[~headers].reset_index(drop=True)
    frame.insert(0, "region", groups.loc[~headers].reset_index(drop=True))
    return frame


def library(raw):
    return untangle(raw, group_column="item", group_pattern="^REGION:", group_name="region").frame


if __name__ == "__main__":
    raw = pd.DataFrame(
        {"item": ["REGION: NORTH", "Tea", "REGION: SOUTH", "Cocoa"], "price": [None, 10, None, 20]}
    )
    assert_frame_equal(baseline(raw), library(raw), check_dtype=False)
    result = untangle(raw, group_column="item", group_pattern="^REGION:", group_name="region")
    assert result.source_rows == ((0, 1), (2, 3))
    print("Both return NORTH/Tea and SOUTH/Cocoa; source rows are (0,1) and (2,3).")
