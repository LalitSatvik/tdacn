"""Real segmentation analysis: does drift differ by the industry/size/
complexity profile of the filers who report a concept? Reuses the
already-trained Q1 graph/embeddings; only complexity + segment-profile
tables need computing fresh.
"""

import os
import pickle

import networkx as nx
import pandas as pd

from tdacn.adapters.sec_dera import SecDeraAdapter
from tdacn.metrics.embedding_drift import consecutive_cosine_drift
from tdacn.segment.complexity import compute_filer_complexity
from tdacn.segment.concept_category import classify_concepts
from tdacn.segment.concept_profile import concept_segment_profile
from tdacn.segment.regression import fit_ols

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
EMB_DIR = os.path.join(REPO_ROOT, "data_processed", "embeddings")

pd.set_option("display.width", 120)


def load(name):
    with open(os.path.join(EMB_DIR, f"{name}.pkl"), "rb") as f:
        return pickle.load(f)


def main():
    graphs = load("graphs")
    aligned_vectors = load("aligned_vectors")

    print("re-parsing Q1 bundle (for entities/facts/concepts)...")
    bundle_q1 = SecDeraAdapter().load_period(os.path.join(DATA_DIR, "Q1"), "Q1", 0)

    print("computing filer complexity + concept segment profiles...")
    complexity = compute_filer_complexity(bundle_q1, "Q1")
    profile = concept_segment_profile(bundle_q1, "Q1", complexity)

    categories = classify_concepts(bundle_q1.concepts).set_index("concept_id")["category"]

    print("computing Q1 pagerank as a control...")
    pagerank = nx.pagerank(graphs["Q1"], weight="weight")

    cos_drift = consecutive_cosine_drift(aligned_vectors, period_order=["Q1", "Q2", "Q3"])
    q1q2 = cos_drift[(cos_drift.period_a == "Q1") & (cos_drift.period_b == "Q2")].copy()
    q1q2["category"] = q1q2["concept_id"].map(categories)
    q1q2 = q1q2[q1q2["category"] == "accounting_fact"]

    data = q1q2.merge(profile, on="concept_id", how="inner")
    data["pagerank_q1"] = data["concept_id"].map(pagerank)
    data = data.dropna(subset=["dominant_industry", "dominant_size_class", "mean_complexity", "pagerank_q1"])
    print(f"\nregression sample size: {len(data)} accounting-fact concepts\n")

    print("=== descriptive: mean drift by dominant industry ===")
    print(
        data.groupby("dominant_industry")["cosine_distance"]
        .agg(["mean", "count"])
        .sort_values("mean", ascending=False)
    )

    print("\n=== descriptive: mean drift by dominant size class ===")
    print(data.groupby("dominant_size_class")["cosine_distance"].agg(["mean", "count"]))

    print("\n=== D/E/F: inferential regression ===")
    print("cosine_distance ~ C(dominant_industry) + C(dominant_size_class) + mean_complexity + pagerank_q1")
    result = fit_ols(
        data,
        "cosine_distance ~ C(dominant_industry) + C(dominant_size_class) + mean_complexity + pagerank_q1",
    )
    print(result.summary())


if __name__ == "__main__":
    main()
