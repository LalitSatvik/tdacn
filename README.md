# Temporal Drift in Accounting Concept Networks

A graph-embedding analysis of whether the *relationships* between XBRL
accounting concepts — not the reported numbers — stay stable across
consecutive reporting periods, and whether drift differs by industry, firm
size, or reporting complexity.

Full design: [`docs plan`](/Users/lalitsurisetty/.claude/plans/i-want-build-a-curried-phoenix.md)
(55 empirical questions, methodology, verification plan).

## Architecture

All analysis code operates on a **canonical schema** (`tdacn.schema`) —
five abstract tables (`periods`, `entities`, `concepts`, `facts`,
`relations`) — never on a dataset's raw columns directly. A **dataset
adapter** (`tdacn.adapters.sec_dera.SecDeraAdapter` is the only one so
far) is the sole place that knows about a specific source format. Porting
this pipeline to different quarters, a different jurisdiction's XBRL, or
an unrelated entity×concept×time panel means writing a new adapter
subclassing `tdacn.adapters.base.AdapterBase` — no other code changes.

```
raw files --[adapter]--> CanonicalBundle --[graph]--> per-period nx.Graph
    --[embed]--> node2vec + Procrustes alignment --[metrics]--> drift
```

Package layout (`src/tdacn/`):

| Module | Responsibility |
|---|---|
| `schema.py` | Canonical tables + validation |
| `adapters/` | `AdapterBase`, `SecDeraAdapter` |
| `ingest/` | `combine.concat_bundles`, `cache.save_bundle`/`load_bundle` (Parquet) |
| `graph/` | `support` (min-support filter) → `edges` (structural + co-reporting) → `pmi` (PMI weighting) → `sparsify` (top-K, keeps node2vec tractable) → `blend` (α-combine layers) → `build`/`pipeline` (assemble `nx.Graph`) |
| `embed/` | `node2vec_embed.train_node2vec`, `align.procrustes_align`/`align_periods` (chained cross-period alignment) |
| `metrics/` | `embedding_drift` (cosine + neighbor-Jaccard), `graph_drift` (centrality + community), `global_drift` (edge overlap, degree-distribution KS, vocabulary churn, modularity), `validation` (bootstrap CI / permutation test primitives) |
| `segment/` | `industry.sic_to_division`, `complexity.compute_filer_complexity` |

## Running the pipeline

```bash
conda activate lalitenv   # duckdb, node2vec, gensim, pytest installed here
python scripts/run_pipeline.py
```

Parses `data/Q1`, `data/Q2`, `data/Q3`, caches canonical tables to
`data_processed/<period>/*.parquet`, builds each period's concept graph
(min-support=5, α=0.5, top-K=15 sparsification), trains node2vec, chain-
aligns embeddings, and pickles graphs + raw/aligned vectors to
`data_processed/embeddings/`. Re-running reuses the cached bundles.

## Tests

```bash
python -m pytest tests/
```

Every module above was built test-first; see `tests/` for the
corresponding `test_*.py`. `tests/test_integration_zero_drift_sanity.py`
is the plan's built-in sanity check — an identical graph fed as both
periods must show ~zero drift end-to-end.

## Findings

Full writeup, organized by the plan's 55 empirical questions, with real
evidence (or an honest "not yet computed" flag) for each:
[`report/findings.md`](report/findings.md).

Headline: drift is real and decelerating (five independent metrics agree
Q1→Q2 changed more than Q2→Q3); concept centrality robustly predicts
stability; "core" GAAP concepts and large filers counter-intuitively
drift *more* than niche concepts and small filers, a consequence of PMI
weighting discounting ubiquitous co-occurrence.

`scripts/analyze_*.py` are the analysis passes behind that report
(the project's substitute for per-category notebooks, given no
interactive-kernel execution tool in this environment — each is a
runnable, printed-output script rather than a `.ipynb`).

## Dashboard

A Next.js + D3 dashboard (`web/`) sits on top of the pipeline outputs —
a five-page site (Overview, Explorer, Segmentation, Findings,
Architecture) with a fully interactive, canvas-rendered concept-network
explorer. It reads plain JSON, not a live backend:

```bash
conda activate lalitenv
python scripts/export_dashboard_data.py   # pipeline outputs -> web/public/data/*.json
cd web && npm install && npm run dev      # http://localhost:3000
```

`export_dashboard_data.py` is a new final pipeline stage — it re-derives
nothing, it only reads the already-computed parquet/pickle artifacts
above and writes dashboard-ready JSON (see the script's docstring). The
exported JSON is committed to `web/public/data/`, so the site deploys
as a static Next.js app (e.g. to Vercel) with no Python runtime needed
in production; re-run the export step and commit the new JSON whenever
the pipeline output changes.

## Not yet built

- **True per-segment subgraphs**: current segmentation attributes each
  concept to the plurality industry/size/complexity of its filers using
  the full-population embeddings, rather than rebuilding a fully separate
  graph+embedding per (industry, period) — that would cost ~30 more
  ~13-minute pipeline runs.
- **Clustered standard errors** on the segmentation regression.
- Statement-type (BS/IS/CF/EQ) breakdown of drift (Q44-47).
- Neighbor-Jaccard drift at full vocabulary scale (correctness-tested,
  current implementation is O(n²) and would take ~10-20 min unvectorized).
- Hyperparameter/α/balanced-panel sensitivity checks (Q52-54).
- Filer-resampling bootstrap/permutation on real drift (primitives exist
  in `metrics.validation`; wiring to a real re-run per iteration is a
  separate, expensive batch job).
