"""First real pass at drift metrics over the Q1-Q3 pipeline output."""

import os
import pickle
import time

import networkx as nx
import pandas as pd

from tdacn.metrics.embedding_drift import consecutive_cosine_drift
from tdacn.metrics.global_drift import concept_churn, degree_distribution_ks, edge_overlap_ratio
from tdacn.metrics.graph_drift import centrality_drift, community_drift, compute_communities

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMB_DIR = os.path.join(REPO_ROOT, "data_processed", "embeddings")
PERIOD_ORDER = ["Q1", "Q2", "Q3"]

pd.set_option("display.width", 120)
pd.set_option("display.max_colwidth", 60)


def load(name):
    with open(os.path.join(EMB_DIR, f"{name}.pkl"), "rb") as f:
        return pickle.load(f)


def main():
    graphs = load("graphs")
    aligned_vectors = load("aligned_vectors")

    print("=== Q1: global network stability ===")
    print(edge_overlap_ratio(graphs, PERIOD_ORDER))
    print()
    print(degree_distribution_ks(graphs, PERIOD_ORDER))
    print()

    print("=== Q7: concept vocabulary churn ===")
    vocab = {p: set(g.nodes) for p, g in graphs.items()}
    print(concept_churn(vocab, PERIOD_ORDER))
    print()

    print("=== Q8/Q9: node-level embedding drift (cosine distance, aligned) ===")
    cos_drift = consecutive_cosine_drift(aligned_vectors, PERIOD_ORDER)
    q1q2 = cos_drift[(cos_drift.period_a == "Q1") & (cos_drift.period_b == "Q2")]
    print(f"n concepts compared Q1->Q2: {len(q1q2)}")
    print(f"mean cosine distance: {q1q2.cosine_distance.mean():.4f}")
    print(f"median cosine distance: {q1q2.cosine_distance.median():.4f}")
    print("\nTop 20 most-drifting concepts (Q1->Q2):")
    print(q1q2.sort_values("cosine_distance", ascending=False).head(20)[["concept_id", "cosine_distance"]])
    print("\nTop 20 most-stable concepts (Q1->Q2):")
    print(q1q2.sort_values("cosine_distance").head(20)[["concept_id", "cosine_distance"]])
    print()

    core_concepts = ["Assets", "Liabilities", "StockholdersEquity", "Revenues", "NetIncomeLoss", "CashAndCashEquivalentsAtCarryingValue"]
    present = q1q2[q1q2.concept_id.isin(core_concepts)]
    print("=== Q10: core GAAP concept drift vs. overall (Q1->Q2) ===")
    print(present[["concept_id", "cosine_distance"]])
    print(f"overall mean: {q1q2.cosine_distance.mean():.4f} vs core-concept mean: {present.cosine_distance.mean():.4f}")
    print()

    print("=== Q5/Q12: centrality drift (PageRank) vs. drift magnitude ===")
    t0 = time.time()
    pr_drift = centrality_drift(graphs, PERIOD_ORDER, centrality_fn=lambda g: nx.pagerank(g, weight="weight"))
    pr_q1q2 = pr_drift[(pr_drift.period_a == "Q1") & (pr_drift.period_b == "Q2")].set_index("concept_id")
    merged = q1q2.set_index("concept_id").join(pr_q1q2[["delta"]].rename(columns={"delta": "pagerank_delta"}))
    # centrality at Q1 as a proxy for "hub-ness"
    pr_q1 = nx.pagerank(graphs["Q1"], weight="weight")
    merged["pagerank_q1"] = merged.index.map(pr_q1)
    corr = merged[["cosine_distance", "pagerank_q1"]].corr().iloc[0, 1]
    print(f"correlation(embedding drift, Q1 pagerank): {corr:.4f}  ({time.time()-t0:.1f}s)")
    print()

    print("=== Q4/community structure ===")
    t0 = time.time()
    labels = {p: compute_communities(g, seed=42) for p, g in graphs.items()}
    print(f"communities computed in {time.time()-t0:.1f}s")
    for p in PERIOD_ORDER:
        n_communities = len(set(labels[p].values()))
        print(f"{p}: {n_communities} communities over {len(labels[p])} nodes")
    print(community_drift(labels, PERIOD_ORDER))


if __name__ == "__main__":
    main()
