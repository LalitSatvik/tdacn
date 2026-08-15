import pandas as pd

from tdacn.ingest.cache import load_bundle, save_bundle
from tdacn.schema import CanonicalBundle


def test_save_then_load_bundle_round_trips(tmp_path):
    bundle = CanonicalBundle(
        periods=pd.DataFrame({"period_id": ["Q1"], "order": [0]}),
        entities=pd.DataFrame(
            {
                "entity_id": ["1"],
                "period": ["Q1"],
                "industry_code": ["73"],
                "size_class": ["1-LAF"],
            }
        ),
        concepts=pd.DataFrame(
            {
                "concept_id": ["Assets"],
                "period": ["Q1"],
                "label": ["Assets"],
                "is_custom": [False],
                "datatype": ["monetary"],
            }
        ),
        facts=pd.DataFrame(
            {
                "entity_id": ["1"],
                "concept_id": ["Assets"],
                "period": ["Q1"],
                "value": [100.0],
                "uom": ["USD"],
            }
        ),
        relations=pd.DataFrame(
            {
                "concept_id_a": ["Assets"],
                "concept_id_b": ["Liabilities"],
                "period": ["Q1"],
                "relation_type": ["structural"],
                "source_entity_id": ["1"],
            }
        ),
    )

    save_bundle(bundle, str(tmp_path))
    loaded = load_bundle(str(tmp_path))

    pd.testing.assert_frame_equal(
        bundle.entities.reset_index(drop=True), loaded.entities.reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(
        bundle.facts.reset_index(drop=True), loaded.facts.reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(
        bundle.relations.reset_index(drop=True), loaded.relations.reset_index(drop=True)
    )
