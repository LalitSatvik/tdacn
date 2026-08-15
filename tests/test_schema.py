import pandas as pd
import pytest

from tdacn.schema import CanonicalBundle, validate_bundle


def _make_valid_bundle():
    periods = pd.DataFrame({"period_id": ["Q1"], "order": [0]})
    entities = pd.DataFrame(
        {
            "entity_id": ["0000001"],
            "period": ["Q1"],
            "industry_code": ["73"],
            "size_class": ["large-accelerated-filer"],
        }
    )
    concepts = pd.DataFrame(
        {
            "concept_id": ["Assets"],
            "period": ["Q1"],
            "label": ["Assets"],
            "is_custom": [False],
            "datatype": ["monetary"],
        }
    )
    facts = pd.DataFrame(
        {
            "entity_id": ["0000001"],
            "concept_id": ["Assets"],
            "period": ["Q1"],
            "value": [100.0],
            "uom": ["USD"],
        }
    )
    relations = pd.DataFrame(
        {
            "concept_id_a": ["Assets"],
            "concept_id_b": ["Liabilities"],
            "period": ["Q1"],
            "relation_type": ["structural"],
            "source_entity_id": ["0000001"],
        }
    )
    return CanonicalBundle(
        periods=periods,
        entities=entities,
        concepts=concepts,
        facts=facts,
        relations=relations,
    )


def test_validate_bundle_accepts_a_well_formed_bundle():
    bundle = _make_valid_bundle()

    # Should not raise.
    validate_bundle(bundle)


def test_validate_bundle_raises_when_facts_missing_required_column():
    bundle = _make_valid_bundle()
    bundle.facts = bundle.facts.drop(columns=["value"])

    with pytest.raises(ValueError, match="facts.*value"):
        validate_bundle(bundle)
