"""Re-run the top-movers analysis split by concept category (dei /
abstract_header / dimensional / accounting_fact), reusing the already-
trained graphs/embeddings -- only concepts tables need re-parsing since
namespace/is_abstract are new adapter fields.
"""

import os
import pickle

import pandas as pd

from tdacn.adapters.sec_dera import SecDeraAdapter
from tdacn.metrics.embedding_drift import consecutive_cosine_drift
from tdacn.segment.concept_category import classify_concepts

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
EMB_DIR = os.path.join(REPO_ROOT, "data_processed", "embeddings")

pd.set_option("display.width", 120)
pd.set_option("display.max_colwidth", 60)


def load(name):
    with open(os.path.join(EMB_DIR, f"{name}.pkl"), "rb") as f:
        return pickle.load(f)


def main():
    aligned_vectors = load("aligned_vectors")

    print("re-parsing concepts tables for Q1, Q2 (namespace/abstract fields)...")
    concepts_q1 = SecDeraAdapter().load_period(os.path.join(DATA_DIR, "Q1"), "Q1", 0).concepts
    concepts_q1 = classify_concepts(concepts_q1).set_index("concept_id")["category"]

    cos_drift = consecutive_cosine_drift(aligned_vectors, period_order=["Q1", "Q2", "Q3"])
    q1q2 = cos_drift[(cos_drift.period_a == "Q1") & (cos_drift.period_b == "Q2")].copy()
    q1q2["category"] = q1q2["concept_id"].map(concepts_q1)

    print("\n=== concept category breakdown among Q1->Q2 compared concepts ===")
    print(q1q2["category"].value_counts())

    print("\n=== mean/median cosine drift by category ===")
    print(q1q2.groupby("category")["cosine_distance"].agg(["mean", "median", "count"]))

    print("\n=== Q8 (corrected): top 20 most-drifting ACCOUNTING FACT concepts ===")
    facts_only = q1q2[q1q2.category == "accounting_fact"]
    print(facts_only.sort_values("cosine_distance", ascending=False).head(20)[["concept_id", "cosine_distance"]])

    print("\n=== Q9 (corrected): top 20 most-stable ACCOUNTING FACT concepts ===")
    print(facts_only.sort_values("cosine_distance").head(20)[["concept_id", "cosine_distance"]])

    core_concepts = ["Assets", "Liabilities", "StockholdersEquity", "Revenues", "NetIncomeLoss", "CashAndCashEquivalentsAtCarryingValue"]
    present = facts_only[facts_only.concept_id.isin(core_concepts)]
    print("\n=== Q10 (corrected): core GAAP concepts vs. accounting_fact-only baseline ===")
    print(present[["concept_id", "cosine_distance"]])
    print(f"accounting_fact mean: {facts_only.cosine_distance.mean():.4f} vs core-concept mean: {present.cosine_distance.mean():.4f}")


if __name__ == "__main__":
    main()
