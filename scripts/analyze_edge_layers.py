"""Q40-43: structural vs co-reporting edge layer comparison. Cheap --
reuses the graph-construction building blocks directly, no node2vec.
"""

import os

import pandas as pd

from tdacn.adapters.sec_dera import SecDeraAdapter
from tdacn.graph.edges import build_co_reporting_edges, build_structural_edges
from tdacn.graph.pmi import pmi_weight
from tdacn.graph.support import compute_concept_support, select_supported_concepts

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
PERIODS = [("Q1", 0), ("Q2", 1), ("Q3", 2)]
pd.set_option("display.width", 120)


def layer_pmi(bundle, period, supported):
    total_entities = bundle.entities[bundle.entities["period"] == period]["entity_id"].nunique()
    support = compute_concept_support(bundle, period)
    structural = pmi_weight(build_structural_edges(bundle, period, supported), support, total_entities)
    co_reporting = pmi_weight(build_co_reporting_edges(bundle, period, supported), support, total_entities)
    return structural, co_reporting


def edge_set(df, min_weight=0):
    positive = df[df["weight"] > min_weight]
    return set(zip(positive["concept_id_a"], positive["concept_id_b"])) | set(
        zip(positive["concept_id_b"], positive["concept_id_a"])
    )


def jaccard(a, b):
    union = a | b
    return len(a & b) / len(union) if union else float("nan")


def main():
    by_period = {}
    for period, order in PERIODS:
        print(f"[{period}] parsing + building edge layers...")
        bundle = SecDeraAdapter().load_period(os.path.join(DATA_DIR, period), period, order)
        support = compute_concept_support(bundle, period)
        supported = select_supported_concepts(support, min_support=5)
        structural, co_reporting = layer_pmi(bundle, period, supported)
        by_period[period] = (structural, co_reporting)
        print(f"  structural edges (PMI>0): {(structural.weight>0).sum()}, co-reporting edges (PMI>0): {(co_reporting.weight>0).sum()}")

    print("\n=== Q42: layer stability -- edge-set Jaccard overlap across periods ===")
    for a, b in [("Q1", "Q2"), ("Q2", "Q3")]:
        s_jaccard = jaccard(edge_set(by_period[a][0]), edge_set(by_period[b][0]))
        c_jaccard = jaccard(edge_set(by_period[a][1]), edge_set(by_period[b][1]))
        print(f"{a}->{b}:  structural jaccard={s_jaccard:.4f}   co-reporting jaccard={c_jaccard:.4f}")

    print("\n=== Q43: correlation between the two layers' PMI weights, per period ===")
    for period, order in PERIODS:
        structural, co_reporting = by_period[period]
        merged = structural.merge(
            co_reporting, on=["concept_id_a", "concept_id_b"], suffixes=("_structural", "_co_reporting")
        )
        corr = merged[["weight_structural", "weight_co_reporting"]].corr(method="spearman").iloc[0, 1]
        print(f"{period}: n shared pairs={len(merged)}, spearman corr={corr:.4f}")

    print("\n=== Q41: pairs strong in one layer, weak in the other (Q1) ===")
    structural, co_reporting = by_period["Q1"]
    merged = structural.merge(
        co_reporting, on=["concept_id_a", "concept_id_b"], suffixes=("_structural", "_co_reporting"), how="outer"
    ).fillna(0)
    merged["gap"] = merged["weight_structural"] - merged["weight_co_reporting"]
    print("top 10 structural-heavy, co-reporting-light pairs:")
    print(merged.sort_values("gap", ascending=False).head(10)[["concept_id_a", "concept_id_b", "weight_structural", "weight_co_reporting"]])
    print("\ntop 10 co-reporting-heavy, structural-light pairs:")
    print(merged.sort_values("gap").head(10)[["concept_id_a", "concept_id_b", "weight_structural", "weight_co_reporting"]])


if __name__ == "__main__":
    main()
