"""Second analysis pass: everything answerable cheaply from already-saved
artifacts (raw_vectors, graphs) plus fresh-but-fast re-parses. Skips
anything that would require retraining node2vec (that's the expensive
part -- ~3-4 min per period).
"""

import os
import pickle

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import kruskal

from tdacn.adapters.sec_dera import SecDeraAdapter
from tdacn.embed.align import procrustes_align
from tdacn.graph.edges import build_co_reporting_edges, build_structural_edges
from tdacn.graph.pmi import pmi_weight
from tdacn.graph.support import compute_concept_support, select_supported_concepts
from tdacn.metrics.embedding_drift import consecutive_cosine_drift
from tdacn.metrics.graph_drift import centrality_drift
from tdacn.segment.concept_category import classify_concepts

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
EMB_DIR = os.path.join(REPO_ROOT, "data_processed", "embeddings")
pd.set_option("display.width", 120)


def load(name):
    with open(os.path.join(EMB_DIR, f"{name}.pkl"), "rb") as f:
        return pickle.load(f)


def main():
    graphs = load("graphs")
    raw_vectors = load("raw_vectors")
    aligned_vectors = load("aligned_vectors")

    # ---- Q18: how much of apparent drift is alignment artifact? ----
    print("=== Q18: raw (unaligned) vs Procrustes-aligned drift, Q1->Q2 ===")
    raw_drift = consecutive_cosine_drift(
        {"Q1": raw_vectors["Q1"], "Q2": raw_vectors["Q2"]}, ["Q1", "Q2"]
    )
    aligned_drift = consecutive_cosine_drift(
        {"Q1": aligned_vectors["Q1"], "Q2": aligned_vectors["Q2"]}, ["Q1", "Q2"]
    )
    print(f"mean cosine distance, RAW (no alignment):    {raw_drift.cosine_distance.mean():.4f}")
    print(f"mean cosine distance, ALIGNED:                {aligned_drift.cosine_distance.mean():.4f}")
    print("-> the gap is how much of naive drift was just arbitrary rotation, not real change.\n")

    # ---- Q19: does embedding-based drift ranking agree with graph-theoretic drift? ----
    print("=== Q19: correlation between embedding drift and graph-theoretic (degree) drift ===")
    deg_drift = centrality_drift(graphs, ["Q1", "Q2"], centrality_fn=lambda g: dict(g.degree(weight="weight")))
    merged = aligned_drift.merge(deg_drift, on=["concept_id", "period_a", "period_b"])
    merged["abs_degree_delta"] = merged["delta"].abs()
    corr = merged[["cosine_distance", "abs_degree_delta"]].corr(method="spearman").iloc[0, 1]
    print(f"Spearman corr(embedding drift, |weighted-degree delta|): {corr:.4f}\n")

    # ---- Q48-51: custom tag dynamics ----
    print("=== Q48-51: custom vs standard tag dynamics ===")
    print("re-parsing Q1/Q2 concepts for is_custom + namespace...")
    concepts_q1 = SecDeraAdapter().load_period(os.path.join(DATA_DIR, "Q1"), "Q1", 0).concepts
    concepts_q2 = SecDeraAdapter().load_period(os.path.join(DATA_DIR, "Q2"), "Q2", 1).concepts
    cat_q1 = classify_concepts(concepts_q1).set_index("concept_id")
    cat_q2 = classify_concepts(concepts_q2).set_index("concept_id")

    for label, cat, g in [("Q1", cat_q1, graphs["Q1"]), ("Q2", cat_q2, graphs["Q2"])]:
        facts_only = cat[cat["category"] == "accounting_fact"]
        pct_custom = facts_only["is_custom"].mean()
        print(f"{label}: {pct_custom:.1%} of accounting-fact concepts are custom extensions")

    q1q2 = aligned_drift.copy()
    q1q2["is_custom"] = q1q2["concept_id"].map(cat_q1["is_custom"])
    q1q2["category"] = q1q2["concept_id"].map(cat_q1["category"])
    facts_only = q1q2[q1q2["category"] == "accounting_fact"]
    print("\ndrift by custom vs standard (accounting_fact concepts, Q1->Q2):")
    print(facts_only.groupby("is_custom")["cosine_distance"].agg(["mean", "count"]))

    deg_q1 = dict(graphs["Q1"].degree(weight="weight"))
    facts_only = facts_only.copy()
    facts_only["degree_q1"] = facts_only["concept_id"].map(deg_q1)
    print("\nweighted degree by custom vs standard (Q1):")
    print(facts_only.groupby("is_custom")["degree_q1"].agg(["mean", "median", "count"]))

    # ---- Q27: is cross-industry drift variance significant (Kruskal-Wallis)? ----
    print("\n=== Q27: Kruskal-Wallis test, drift across industries ===")
    from tdacn.segment.complexity import compute_filer_complexity
    from tdacn.segment.concept_profile import concept_segment_profile

    bundle_q1 = SecDeraAdapter().load_period(os.path.join(DATA_DIR, "Q1"), "Q1", 0)
    complexity = compute_filer_complexity(bundle_q1, "Q1")
    profile = concept_segment_profile(bundle_q1, "Q1", complexity)
    facts_only = facts_only.merge(profile[["concept_id", "dominant_industry"]], on="concept_id", how="left")
    groups = [g["cosine_distance"].values for _, g in facts_only.groupby("dominant_industry") if len(g) >= 10]
    stat, p = kruskal(*groups)
    print(f"H={stat:.2f}, p={p:.2e}  (n groups={len(groups)})")


if __name__ == "__main__":
    main()
