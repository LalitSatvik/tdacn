"""Orchestrates support -> edges -> PMI -> blend -> graph for one period."""

import networkx as nx

from typing import Optional

from tdacn.graph.blend import blend_edges
from tdacn.graph.build import build_graph
from tdacn.graph.edges import build_co_reporting_edges, build_structural_edges
from tdacn.graph.pmi import pmi_weight
from tdacn.graph.sparsify import top_k_sparsify
from tdacn.graph.support import compute_concept_support, select_supported_concepts
from tdacn.schema import CanonicalBundle


def build_period_graph(
    bundle: CanonicalBundle,
    period: str,
    min_support: int = 5,
    alpha: float = 0.5,
    positive_pmi: bool = True,
    top_k: Optional[int] = 15,
) -> nx.Graph:
    support = compute_concept_support(bundle, period)
    supported = select_supported_concepts(support, min_support)
    total_entities = bundle.entities[bundle.entities["period"] == period][
        "entity_id"
    ].nunique()

    structural_raw = build_structural_edges(bundle, period, supported)
    co_reporting_raw = build_co_reporting_edges(bundle, period, supported)

    structural_pmi = pmi_weight(structural_raw, support, total_entities, positive_pmi)
    co_reporting_pmi = pmi_weight(co_reporting_raw, support, total_entities, positive_pmi)

    blended = blend_edges(structural_pmi, co_reporting_pmi, alpha=alpha)
    if top_k is not None:
        blended = top_k_sparsify(blended, k=top_k)
    return build_graph(supported, blended)
