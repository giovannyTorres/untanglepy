"""Extract explicitly marked regional subheaders and preserve source positions."""

import pandas as pd

from untanglepy import untangle

raw = pd.DataFrame(
    {
        "product": ["REGION: NORTH", "Tea", "Coffee", "REGION: SOUTH", "Cocoa"],
        "value": [None, 100, 200, None, 300],
    }
)
result = untangle(raw, group_column="product", group_pattern=r"^REGION:", group_name="region")
assert result.frame["region"].tolist() == ["NORTH", "NORTH", "SOUTH"]
assert result.source_rows == ((0, 1), (0, 2), (3, 4))
print(result.frame)
print(result.lineage())
