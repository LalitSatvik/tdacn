"""Parquet caching for a CanonicalBundle.

Re-parsing multi-million-row raw source files on every run is wasteful;
this lets any adapter's output be persisted once (e.g. to
data_processed/<period>/) and reloaded near-instantly thereafter.
"""

import os

import pandas as pd

from tdacn.schema import CanonicalBundle

_TABLES = ("periods", "entities", "concepts", "facts", "relations")


def save_bundle(bundle: CanonicalBundle, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for table in _TABLES:
        getattr(bundle, table).to_parquet(os.path.join(out_dir, f"{table}.parquet"))


def load_bundle(out_dir: str) -> CanonicalBundle:
    tables = {
        table: pd.read_parquet(os.path.join(out_dir, f"{table}.parquet"))
        for table in _TABLES
    }
    return CanonicalBundle(**tables)
