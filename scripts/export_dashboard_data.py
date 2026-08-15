"""Final pipeline stage: export dashboard-ready JSON from the already-
computed pipeline artifacts (cached canonical bundles + graphs/embeddings)
to web/public/data/. No new modeling happens here -- everything below
reuses existing tdacn.metrics/segment/graph functions, the same way the
scripts/analyze_*.py passes do, so the numbers this produces are the same
numbers already reported in report/findings.md.

Requires scripts/run_pipeline.py to have been run first (needs its cached
data_processed/<period>/*.parquet bundles and data_processed/embeddings/*.pkl).

    conda activate lalitenv
    python scripts/export_dashboard_data.py
"""

import json
import math
import os
import pickle
import time

import networkx as nx
import numpy as np
import pandas as pd

from tdacn.ingest.cache import load_bundle
from tdacn.metrics.embedding_drift import consecutive_cosine_drift
from tdacn.metrics.global_drift import (
    concept_churn,
    degree_distribution_ks,
    edge_overlap_ratio,
)
from tdacn.metrics.graph_drift import centrality_drift, community_drift, compute_communities
from tdacn.graph.edges import build_co_reporting_edges, build_structural_edges
from tdacn.graph.pmi import pmi_weight
from tdacn.graph.support import compute_concept_support, select_supported_concepts
from tdacn.segment.complexity import compute_filer_complexity
from tdacn.segment.concept_category import classify_concepts
from tdacn.segment.concept_profile import concept_segment_profile
from tdacn.segment.regression import fit_ols

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(REPO_ROOT, "data_processed")
EMB_DIR = os.path.join(PROCESSED_DIR, "embeddings")
FINDINGS_PATH = os.path.join(REPO_ROOT, "report", "findings.md")
OUT_DIR = os.path.join(REPO_ROOT, "web", "public", "data")

PERIOD_ORDER = ["Q1", "Q2", "Q3"]
PAIRS = list(zip(PERIOD_ORDER, PERIOD_ORDER[1:]))  # [("Q1","Q2"), ("Q2","Q3")]

CORE_CONCEPTS = [
    "Assets",
    "Liabilities",
    "StockholdersEquity",
    "Revenues",
    "NetIncomeLoss",
    "CashAndCashEquivalentsAtCarryingValue",
]


# ---------------------------------------------------------------- helpers --

def _clean(value):
    """Make a value JSON-safe: numpy scalars -> python, NaN/inf -> None."""
    if isinstance(value, (np.floating, float)):
        value = float(value)
        return None if (math.isnan(value) or math.isinf(value)) else round(value, 6)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return value


def _write_json(name, payload):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    size_kb = os.path.getsize(path) / 1024
    print(f"  wrote {name} ({size_kb:.0f} KB)")


def load_pickle(name):
    with open(os.path.join(EMB_DIR, f"{name}.pkl"), "rb") as f:
        return pickle.load(f)


def get_bundle(period):
    return load_bundle(os.path.join(PROCESSED_DIR, period))


# ------------------------------------------------------- per-period prep --

def compute_layout(graph):
    """d3-force-equivalent layout, computed once here rather than live in
    the browser (see plan: 'layout is computed once, ahead of time').

    k is pushed well above networkx's default (1/sqrt(n) ~= 0.011 for this
    graph) -- at the default, PMI-weighted attraction pulls the well-
    connected core into a single dense blob with little of the graph's
    actual structure visible. k=0.25 gives enough repulsion to spread
    the periphery out while still respecting edge weight for clustering.
    """
    pos = nx.spring_layout(graph, weight="weight", seed=42, k=0.25, iterations=50)
    return {node: (float(xy[0]), float(xy[1])) for node, xy in pos.items()}


def compute_layer_tags(bundle, period, graph):
    """Tag each surviving (blended, sparsified) edge as structural- or
    co-reporting-dominant, by looking its concept pair up in the two raw
    PMI layers built the same way build_period_graph does upstream of the
    blend step. Mirrors scripts/analyze_edge_layers.py's approach.
    """
    support = compute_concept_support(bundle, period)
    supported = select_supported_concepts(support, min_support=5)
    total_entities = bundle.entities[bundle.entities["period"] == period][
        "entity_id"
    ].nunique()

    structural = pmi_weight(
        build_structural_edges(bundle, period, supported), support, total_entities
    )
    co_reporting = pmi_weight(
        build_co_reporting_edges(bundle, period, supported), support, total_entities
    )

    def _weight_lookup(df):
        lookup = {}
        for row in df.itertuples(index=False):
            lookup[frozenset((row.concept_id_a, row.concept_id_b))] = row.weight
        return lookup

    struct_lookup = _weight_lookup(structural)
    co_lookup = _weight_lookup(co_reporting)

    tags = {}
    for u, v in graph.edges():
        key = frozenset((u, v))
        s = struct_lookup.get(key, 0.0)
        c = co_lookup.get(key, 0.0)
        tags[key] = "structural" if s >= c else "co_reporting"
    return tags


# -------------------------------------------------------------- exporters --

def export_graphs(bundles, graphs, categories, complexity_profiles, cos_drift, pageranks):
    """One graph_<period>.json per period: nodes (with all attributes the
    Explorer/detail-panel needs) + edges (with a structural/co_reporting
    layer tag). Self-contained per file -- no cross-file joins needed.
    """
    drift_lookup = {}  # (concept_id, period_a) -> cosine_distance
    for row in cos_drift.itertuples(index=False):
        drift_lookup[(row.concept_id, row.period_a)] = row.cosine_distance

    for period in PERIOD_ORDER:
        t0 = time.time()
        graph = graphs[period]
        bundle = bundles[period]
        cats = categories[period]
        profile = complexity_profiles[period]
        pagerank = pageranks[period]

        concepts_meta = (
            bundle.concepts[bundle.concepts["period"] == period]
            .drop_duplicates("concept_id")
            .set_index("concept_id")
        )

        pos = compute_layout(graph)
        layer_tags = compute_layer_tags(bundle, period, graph)

        nodes = []
        for node in graph.nodes():
            row = concepts_meta.loc[node] if node in concepts_meta.index else None
            profile_row = profile.loc[node] if node in profile.index else None
            x, y = pos.get(node, (0.0, 0.0))
            nodes.append(
                {
                    "id": node,
                    "label": _clean(row["label"]) if row is not None else node,
                    "category": _clean(cats.get(node, "accounting_fact")),
                    "isCustom": _clean(row["is_custom"]) if row is not None else False,
                    "pagerank": _clean(pagerank.get(node, 0.0)),
                    "degree": _clean(graph.degree(node, weight="weight")),
                    "industry": _clean(profile_row["dominant_industry"]) if profile_row is not None else None,
                    "sizeClass": _clean(profile_row["dominant_size_class"]) if profile_row is not None else None,
                    "complexity": _clean(profile_row["mean_complexity"]) if profile_row is not None else None,
                    "x": _clean(x),
                    "y": _clean(y),
                    "driftNext": _clean(drift_lookup.get((node, period))),
                }
            )

        edges = []
        for u, v, data in graph.edges(data=True):
            edges.append(
                {
                    "source": u,
                    "target": v,
                    "weight": _clean(data.get("weight", 0.0)),
                    "layer": layer_tags.get(frozenset((u, v)), "co_reporting"),
                }
            )

        _write_json(
            f"graph_{period}.json",
            {
                "period": period,
                "nodeCount": graph.number_of_nodes(),
                "edgeCount": graph.number_of_edges(),
                "nodes": nodes,
                "edges": edges,
            },
        )
        print(f"  [{period}] graph exported in {time.time() - t0:.1f}s "
              f"({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)")


def export_overview(bundles, graphs, cos_drift, raw_vectors, aligned_vectors):
    q1q2 = cos_drift[(cos_drift.period_a == "Q1") & (cos_drift.period_b == "Q2")]
    q2q3 = cos_drift[(cos_drift.period_a == "Q2") & (cos_drift.period_b == "Q3")]

    jaccard = edge_overlap_ratio(graphs, PERIOD_ORDER)
    ks = degree_distribution_ks(graphs, PERIOD_ORDER)
    vocab = {p: set(g.nodes) for p, g in graphs.items()}
    churn = concept_churn(vocab, PERIOD_ORDER)

    labels_by_period = {p: compute_communities(g, seed=42) for p, g in graphs.items()}
    community_counts = {p: len(set(labels_by_period[p].values())) for p in PERIOD_ORDER}
    community_agreement = community_drift(labels_by_period, PERIOD_ORDER)

    def pair_row(df, a, b, col):
        r = df[(df.period_a == a) & (df.period_b == b)]
        return _clean(r.iloc[0][col]) if len(r) else None

    metrics = [
        {
            "id": "embedding_drift",
            "label": "Aligned embedding drift",
            "sublabel": "mean cosine distance",
            "q1q2": _clean(q1q2.cosine_distance.mean()),
            "q2q3": _clean(q2q3.cosine_distance.mean()),
            "decelerating": True,
        },
        {
            "id": "edge_jaccard",
            "label": "Edge-set overlap",
            "sublabel": "Jaccard",
            "q1q2": pair_row(jaccard, "Q1", "Q2", "jaccard"),
            "q2q3": pair_row(jaccard, "Q2", "Q3", "jaccard"),
            "decelerating": True,
        },
        {
            "id": "degree_ks",
            "label": "Degree-distribution shape",
            "sublabel": "KS test p-value",
            "q1q2": pair_row(ks, "Q1", "Q2", "p_value"),
            "q2q3": pair_row(ks, "Q2", "Q3", "p_value"),
            "decelerating": True,
        },
        {
            "id": "vocab_churn",
            "label": "Vocabulary churn",
            "sublabel": "% concepts entered/exited",
            "q1q2": pair_row(churn, "Q1", "Q2", "churn_rate"),
            "q2q3": pair_row(churn, "Q2", "Q3", "churn_rate"),
            "decelerating": True,
        },
        {
            "id": "community_count",
            "label": "Community count",
            "sublabel": "Louvain communities",
            "q1q2": community_counts["Q1"],
            "q2q3": community_counts["Q2"],
            "q3": community_counts["Q3"],
            "decelerating": None,
        },
        {
            "id": "community_agreement",
            "label": "Community agreement",
            "sublabel": "NMI",
            "q1q2": pair_row(community_agreement, "Q1", "Q2", "nmi"),
            "q2q3": pair_row(community_agreement, "Q2", "Q3", "nmi"),
            "decelerating": False,
        },
    ]

    dataset_stats = [
        {
            "period": p,
            "concepts": graphs[p].number_of_nodes(),
            "edges": graphs[p].number_of_edges(),
            "entities": int(bundles[p].entities[bundles[p].entities.period == p].entity_id.nunique()),
        }
        for p in PERIOD_ORDER
    ]

    # Q18: how much of naive drift is alignment artifact
    raw_drift = consecutive_cosine_drift(
        {"Q1": raw_vectors["Q1"], "Q2": raw_vectors["Q2"]}, ["Q1", "Q2"]
    )
    aligned_drift_q1q2 = consecutive_cosine_drift(
        {"Q1": aligned_vectors["Q1"], "Q2": aligned_vectors["Q2"]}, ["Q1", "Q2"]
    )

    _write_json(
        "overview.json",
        {
            "headline": (
                "Drift is real, substantial, and decelerating. Five independent "
                "metrics -- embedding distance, raw edge overlap, degree-"
                "distribution shape, vocabulary churn, and community detection -- "
                "all agree that Q1→Q2 shows more structural change than Q2→Q3."
            ),
            "counterIntuitive": (
                "“Core” GAAP concepts (Assets, Liabilities, NetIncomeLoss, "
                "StockholdersEquity, Revenues) drift more than the accounting-fact "
                "average, and smaller filers show less drift than large accelerated "
                "filers -- both opposite the naive hypothesis. PMI weighting "
                "discounts ubiquitous co-occurrence, so concepts used by nearly "
                "every filer end up with weaker, noisier surviving edges after "
                "sparsification than concepts used consistently by a narrower "
                "population."
            ),
            "metrics": metrics,
            "datasetStats": dataset_stats,
            "rawVsAlignedDrift": {
                "raw": _clean(raw_drift.cosine_distance.mean()),
                "aligned": _clean(aligned_drift_q1q2.cosine_distance.mean()),
            },
        },
    )


def export_segmentation(bundles, graphs, cos_drift, pageranks):
    bundle_q1 = bundles["Q1"]
    complexity = compute_filer_complexity(bundle_q1, "Q1")
    profile = concept_segment_profile(bundle_q1, "Q1", complexity)
    categories = classify_concepts(bundle_q1.concepts).set_index("concept_id")["category"]

    q1q2 = cos_drift[(cos_drift.period_a == "Q1") & (cos_drift.period_b == "Q2")].copy()
    q1q2["category"] = q1q2["concept_id"].map(categories)
    facts_only = q1q2[q1q2["category"] == "accounting_fact"].copy()

    data = facts_only.merge(profile, on="concept_id", how="inner")
    data["pagerank_q1"] = data["concept_id"].map(pageranks["Q1"])
    data = data.dropna(
        subset=["dominant_industry", "dominant_size_class", "mean_complexity", "pagerank_q1"]
    )

    by_industry = (
        data.groupby("dominant_industry")["cosine_distance"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"dominant_industry": "group", "mean": "mean", "count": "n"})
        .sort_values("mean", ascending=False)
    )
    by_size = (
        data.groupby("dominant_size_class")["cosine_distance"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"dominant_size_class": "group", "mean": "mean", "count": "n"})
        .sort_values("mean", ascending=False)
    )

    terciles = pd.qcut(data["mean_complexity"], 3, labels=["low", "medium", "high"], duplicates="drop")
    data = data.assign(complexity_tercile=terciles)
    by_complexity = (
        data.groupby("complexity_tercile", observed=True)["cosine_distance"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"complexity_tercile": "group", "mean": "mean", "count": "n"})
    )

    scatter = data[["concept_id", "pagerank_q1", "cosine_distance"]].rename(
        columns={"pagerank_q1": "pagerank", "cosine_distance": "drift"}
    )

    result = fit_ols(
        data,
        "cosine_distance ~ C(dominant_industry) + C(dominant_size_class) + mean_complexity + pagerank_q1",
    )
    regression = []
    for term in result.params.index:
        regression.append(
            {
                "term": term,
                "coef": _clean(result.params[term]),
                "stdErr": _clean(result.bse[term]),
                "pValue": _clean(result.pvalues[term]),
                "significant": bool(result.pvalues[term] < 0.05),
            }
        )

    # custom vs standard tag comparison (Q34/Q51)
    is_custom = bundle_q1.concepts.drop_duplicates("concept_id").set_index("concept_id")["is_custom"]
    facts_only["is_custom"] = facts_only["concept_id"].map(is_custom)
    custom_drift = (
        facts_only.groupby("is_custom")["cosine_distance"].agg(["mean", "count"]).reset_index()
    )
    deg_q1 = dict(graphs["Q1"].degree(weight="weight"))
    facts_only["degree_q1"] = facts_only["concept_id"].map(deg_q1)
    custom_degree = (
        facts_only.groupby("is_custom")["degree_q1"].agg(["mean", "count"]).reset_index()
    )

    _write_json(
        "segmentation.json",
        {
            "sampleSize": int(len(data)),
            "regressionFormula": "cosine_distance ~ industry + size_class + mean_complexity + pagerank_q1",
            "byIndustry": [
                {"group": r.group, "mean": _clean(r.mean), "n": _clean(r.n)}
                for r in by_industry.itertuples(index=False)
            ],
            "bySize": [
                {"group": r.group, "mean": _clean(r.mean), "n": _clean(r.n)}
                for r in by_size.itertuples(index=False)
            ],
            "byComplexity": [
                {"group": str(r.group), "mean": _clean(r.mean), "n": _clean(r.n)}
                for r in by_complexity.itertuples(index=False)
            ],
            "centralityVsDrift": [
                {
                    "conceptId": r.concept_id,
                    "pagerank": _clean(r.pagerank),
                    "drift": _clean(r.drift),
                }
                for r in scatter.itertuples(index=False)
            ],
            "regression": regression,
            "customVsStandard": {
                "drift": [
                    {"isCustom": bool(r.is_custom), "mean": _clean(r.mean), "n": _clean(r.count)}
                    for r in custom_drift.itertuples(index=False)
                ],
                "weightedDegree": [
                    {"isCustom": bool(r.is_custom), "mean": _clean(r.mean), "n": _clean(r.count)}
                    for r in custom_degree.itertuples(index=False)
                ],
            },
        },
    )


# --------------------------------------------------------- findings.md ----

import re

_STATUS_MAP = {"✅": "answered", "\U0001F7E1": "partial", "⬜": "open"}
_SECTION_RE = re.compile(r"^## ([A-Z])\. (.+)$")
_QUESTION_RE = re.compile(r"^(\d+(?:–\d+)?)\.\s+(✅|\U0001F7E1|⬜)\s+(.*)$")


def export_findings():
    with open(FINDINGS_PATH) as f:
        lines = f.readlines()

    sections = []
    current = None
    for line in lines:
        line = line.rstrip("\n")
        m = _SECTION_RE.match(line)
        if m:
            current = {"letter": m.group(1), "title": m.group(2), "questions": []}
            sections.append(current)
            continue
        m = _QUESTION_RE.match(line)
        if m and current is not None:
            current["questions"].append(
                {
                    "number": m.group(1),
                    "status": _STATUS_MAP[m.group(2)],
                    "text": m.group(3),
                }
            )

    total = sum(len(s["questions"]) for s in sections)
    answered = sum(
        1 for s in sections for q in s["questions"] if q["status"] in ("answered", "partial")
    )
    _write_json(
        "findings.json",
        {"sections": sections, "totalQuestions": total, "answeredQuestions": answered},
    )
    print(f"  parsed {len(sections)} sections, {total} questions ({answered} answered/partial)")


# ------------------------------------------------------------------- main --

def main():
    t_start = time.time()
    print("loading pipeline artifacts...")
    graphs = load_pickle("graphs")
    raw_vectors = load_pickle("raw_vectors")
    aligned_vectors = load_pickle("aligned_vectors")
    bundles = {p: get_bundle(p) for p in PERIOD_ORDER}

    print("computing shared metrics (pagerank, categories, segment profiles, drift)...")
    pageranks = {p: nx.pagerank(graphs[p], weight="weight") for p in PERIOD_ORDER}
    categories = {
        p: classify_concepts(bundles[p].concepts).set_index("concept_id")["category"]
        for p in PERIOD_ORDER
    }
    complexity_profiles = {}
    for p in PERIOD_ORDER:
        complexity = compute_filer_complexity(bundles[p], p)
        complexity_profiles[p] = concept_segment_profile(bundles[p], p, complexity).set_index(
            "concept_id"
        )
    cos_drift = consecutive_cosine_drift(aligned_vectors, PERIOD_ORDER)

    print("exporting graph_<period>.json...")
    export_graphs(bundles, graphs, categories, complexity_profiles, cos_drift, pageranks)

    print("exporting overview.json...")
    export_overview(bundles, graphs, cos_drift, raw_vectors, aligned_vectors)

    print("exporting segmentation.json...")
    export_segmentation(bundles, graphs, cos_drift, pageranks)

    print("exporting findings.json...")
    export_findings()

    print(f"done in {time.time() - t_start:.1f}s -> {OUT_DIR}")


if __name__ == "__main__":
    main()
