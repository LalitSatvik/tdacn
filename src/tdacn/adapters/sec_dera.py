"""Adapter for the SEC DERA "Financial Statement Data Sets" format.

Each quarter directory is expected to contain sub.txt, tag.txt, num.txt and
pre.txt as published by SEC DERA. This is the only module in the pipeline
that knows about those raw column names — everything downstream consumes
the CanonicalBundle this produces.
"""

import os
from typing import List, Tuple

import duckdb
import pandas as pd

from tdacn.adapters.base import AdapterBase
from tdacn.ingest.combine import concat_bundles
from tdacn.schema import CanonicalBundle

DEFAULT_FORMS = ("10-K", "10-Q")


class SecDeraAdapter(AdapterBase):
    def __init__(self, forms: Tuple[str, ...] = DEFAULT_FORMS):
        self.forms = forms

    def load(self, source: List[Tuple[str, str, int]]) -> CanonicalBundle:
        """source: list of (period_id, quarter_dir, order) tuples."""
        bundles = [
            self.load_period(quarter_dir, period_id=period_id, order=order)
            for period_id, quarter_dir, order in source
        ]
        return concat_bundles(bundles)

    def load_period(self, quarter_dir: str, period_id: str, order: int) -> CanonicalBundle:
        con = duckdb.connect()
        try:
            forms_list = ", ".join(f"'{f}'" for f in self.forms)

            sub_path = os.path.join(quarter_dir, "sub.txt")
            tag_path = os.path.join(quarter_dir, "tag.txt")
            num_path = os.path.join(quarter_dir, "num.txt")
            pre_path = os.path.join(quarter_dir, "pre.txt")

            con.execute(
                f"""
                CREATE TEMP TABLE kept_sub AS
                SELECT
                    adsh,
                    CAST(cik AS VARCHAR) AS entity_id,
                    CAST(sic AS VARCHAR) AS industry_code,
                    afs AS size_class,
                    ROW_NUMBER() OVER (
                        PARTITION BY CAST(cik AS VARCHAR) ORDER BY adsh
                    ) AS rn
                FROM read_csv('{sub_path}', delim='\t', header=True, all_varchar=True)
                WHERE form IN ({forms_list})
                """
            )

            entities = con.execute(
                """
                SELECT entity_id, industry_code, size_class
                FROM kept_sub
                WHERE rn = 1
                """
            ).df()
            entities["period"] = period_id

            facts = con.execute(
                f"""
                SELECT
                    s.entity_id AS entity_id,
                    n.tag AS concept_id,
                    n.value AS value,
                    n.uom AS uom,
                    n.version AS version
                FROM read_csv('{num_path}', delim='\t', header=True, all_varchar=True) n
                JOIN kept_sub s ON s.adsh = n.adsh AND s.rn = 1
                """
            ).df()
            facts["period"] = period_id
            facts["value"] = pd.to_numeric(facts["value"], errors="coerce")

            relation_pairs = con.execute(
                f"""
                WITH kept_pre AS (
                    SELECT
                        p.adsh AS adsh,
                        p.stmt AS stmt,
                        CAST(p.line AS BIGINT) AS line,
                        p.tag AS tag,
                        s.entity_id AS entity_id
                    FROM read_csv('{pre_path}', delim='\t', header=True, all_varchar=True) p
                    JOIN kept_sub s ON s.adsh = p.adsh AND s.rn = 1
                ),
                ordered AS (
                    SELECT
                        adsh, stmt, entity_id, tag,
                        LEAD(tag) OVER (
                            PARTITION BY adsh, stmt ORDER BY line
                        ) AS next_tag
                    FROM kept_pre
                )
                SELECT entity_id, stmt, tag AS concept_id_a, next_tag AS concept_id_b
                FROM ordered
                WHERE next_tag IS NOT NULL
                """
            ).df()
            relations = pd.DataFrame(
                {
                    "concept_id_a": relation_pairs["concept_id_a"],
                    "concept_id_b": relation_pairs["concept_id_b"],
                    "source_entity_id": relation_pairs["entity_id"],
                    # Optional, SEC-specific attribute (which statement this
                    # adjacency came from -- BS/IS/CF/EQ/...). Not part of
                    # the required canonical schema, so other adapters are
                    # free to omit it; used here for reporting-complexity
                    # segmentation (distinct statement types per filer).
                    "stmt": relation_pairs["stmt"],
                }
            )
            relations["period"] = period_id
            relations["relation_type"] = "structural"

            used_tags = set(facts["concept_id"]) | set(relations["concept_id_a"]) | set(
                relations["concept_id_b"]
            )

            tag_df = con.execute(
                f"""
                SELECT tag, custom, abstract, datatype, tlabel, version,
                    ROW_NUMBER() OVER (PARTITION BY tag ORDER BY version) AS rn
                FROM read_csv('{tag_path}', delim='\t', header=True, all_varchar=True)
                """
            ).df()
            tag_df = tag_df[tag_df["rn"] == 1]
            tag_df = tag_df[tag_df["tag"].isin(used_tags)]

            concepts = pd.DataFrame(
                {
                    "concept_id": tag_df["tag"],
                    "label": tag_df["tlabel"],
                    "is_custom": tag_df["custom"].astype(str) == "1",
                    "datatype": tag_df["datatype"],
                    # Optional, SEC-specific attributes (not part of the
                    # required canonical schema): `abstract` flags
                    # structural header-only tags with no reportable value;
                    # `namespace` (the part of `version` before the slash,
                    # e.g. "dei"/"us-gaap"/"srt") separates cover-page
                    # metadata from real accounting concepts. Used by
                    # segment.concept_category rather than guessing from
                    # tag-name patterns.
                    "is_abstract": tag_df["abstract"].astype(str) == "1",
                    "namespace": tag_df["version"].str.split("/").str[0],
                }
            )
            concepts["period"] = period_id

            periods = pd.DataFrame({"period_id": [period_id], "order": [order]})

            return CanonicalBundle(
                periods=periods,
                entities=entities,
                concepts=concepts,
                facts=facts,
                relations=relations,
            )
        finally:
            con.close()
