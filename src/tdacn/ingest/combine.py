"""Dataset-agnostic combination of per-period CanonicalBundles.

Any adapter can load one period at a time and use this to assemble the
full multi-period bundle the rest of the pipeline expects. This lives
outside any adapter because it depends only on the canonical schema.
"""

from typing import List

import pandas as pd

from tdacn.schema import CanonicalBundle


def concat_bundles(bundles: List[CanonicalBundle]) -> CanonicalBundle:
    if not bundles:
        raise ValueError("concat_bundles requires at least one bundle")

    return CanonicalBundle(
        periods=pd.concat([b.periods for b in bundles], ignore_index=True),
        entities=pd.concat([b.entities for b in bundles], ignore_index=True),
        concepts=pd.concat([b.concepts for b in bundles], ignore_index=True),
        facts=pd.concat([b.facts for b in bundles], ignore_index=True),
        relations=pd.concat([b.relations for b in bundles], ignore_index=True),
    )
