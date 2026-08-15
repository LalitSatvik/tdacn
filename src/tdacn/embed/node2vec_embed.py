"""Thin, documented wrapper around the node2vec package.

Fixes the parameters that matter for reproducibility (seed, single-threaded
gensim training) so re-running the pipeline with the same inputs gives the
same embeddings — important for the hyperparameter-sensitivity robustness
check, which needs to vary one thing at a time.
"""

from typing import Dict

import networkx as nx
import numpy as np
from node2vec import Node2Vec


def train_node2vec(
    graph: nx.Graph,
    dimensions: int = 64,
    walk_length: int = 40,
    num_walks: int = 10,
    p: float = 1.0,
    q: float = 1.0,
    seed: int = 42,
    workers: int = 1,
    window: int = 10,
) -> Dict[str, np.ndarray]:
    node2vec = Node2Vec(
        graph,
        dimensions=dimensions,
        walk_length=walk_length,
        num_walks=num_walks,
        p=p,
        q=q,
        weight_key="weight",
        workers=workers,
        seed=seed,
        quiet=True,
    )
    model = node2vec.fit(
        window=window, min_count=1, batch_words=4, workers=workers, seed=seed
    )
    return {node: model.wv[str(node)] for node in graph.nodes}
