"""Assemble the final per-period weighted concept graph."""

from typing import Set

import networkx as nx
import pandas as pd


def build_graph(supported_concepts: Set[str], edges: pd.DataFrame) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(supported_concepts)
    for row in edges.itertuples(index=False):
        if row.weight > 0:
            graph.add_edge(row.concept_id_a, row.concept_id_b, weight=row.weight)
    return graph
