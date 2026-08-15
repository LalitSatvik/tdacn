"""End-to-end run: adapt -> cache -> graph -> embed -> align, for Q1-Q3.

Caches canonical bundles to data_processed/<period>/ (parquet) and pipeline
outputs (graphs, raw/aligned embeddings) to data_processed/embeddings/
(pickle) so repeated notebook runs don't have to redo this from scratch.
Run from the repo root: python scripts/run_pipeline.py
"""

import os
import pickle
import time

from tdacn.adapters.sec_dera import SecDeraAdapter
from tdacn.embed.align import align_periods
from tdacn.embed.node2vec_embed import train_node2vec
from tdacn.graph.pipeline import build_period_graph
from tdacn.ingest.cache import load_bundle, save_bundle

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
PROCESSED_DIR = os.path.join(REPO_ROOT, "data_processed")

PERIODS = [("Q1", 0), ("Q2", 1), ("Q3", 2)]


def get_bundle(period: str):
    cache_dir = os.path.join(PROCESSED_DIR, period)
    if os.path.exists(os.path.join(cache_dir, "facts.parquet")):
        print(f"[{period}] loading cached bundle")
        return load_bundle(cache_dir)

    print(f"[{period}] parsing raw SEC files")
    t0 = time.time()
    bundle = SecDeraAdapter().load_period(
        os.path.join(DATA_DIR, period), period_id=period, order=dict(PERIODS)[period]
    )
    save_bundle(bundle, cache_dir)
    print(f"[{period}] parsed + cached in {time.time() - t0:.1f}s")
    return bundle


def main():
    graphs = {}
    for period, _ in PERIODS:
        bundle = get_bundle(period)
        t0 = time.time()
        graphs[period] = build_period_graph(
            bundle, period, min_support=5, alpha=0.5, top_k=15
        )
        g = graphs[period]
        print(
            f"[{period}] graph: {g.number_of_nodes()} nodes, "
            f"{g.number_of_edges()} edges ({time.time() - t0:.1f}s)"
        )

    raw_vectors = {}
    for period, _ in PERIODS:
        t0 = time.time()
        raw_vectors[period] = train_node2vec(
            graphs[period], dimensions=64, walk_length=40, num_walks=10, seed=42, workers=1
        )
        print(f"[{period}] node2vec trained in {time.time() - t0:.1f}s")

    period_order = [p for p, _ in PERIODS]
    aligned_vectors = align_periods(raw_vectors, period_order)

    out_dir = os.path.join(PROCESSED_DIR, "embeddings")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "graphs.pkl"), "wb") as f:
        pickle.dump(graphs, f)
    with open(os.path.join(out_dir, "raw_vectors.pkl"), "wb") as f:
        pickle.dump(raw_vectors, f)
    with open(os.path.join(out_dir, "aligned_vectors.pkl"), "wb") as f:
        pickle.dump(aligned_vectors, f)
    print(f"saved graphs + embeddings to {out_dir}")


if __name__ == "__main__":
    main()
