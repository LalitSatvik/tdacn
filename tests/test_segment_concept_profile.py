import pandas as pd

from tdacn.schema import CanonicalBundle
from tdacn.segment.concept_profile import concept_segment_profile


def _bundle():
    periods = pd.DataFrame({"period_id": ["Q1"], "order": [0]})
    entities = pd.DataFrame(
        {
            "entity_id": ["e1", "e2", "e3"],
            "period": ["Q1"] * 3,
            "industry_code": ["7372", "7371", "6022"],  # e1,e2 -> Services; e3 -> Finance
            "size_class": ["1-LAF", "1-LAF", "4-NON"],
        }
    )
    concepts = pd.DataFrame(
        {"concept_id": [], "period": [], "label": [], "is_custom": [], "datatype": []}
    )
    facts = pd.DataFrame(
        {
            "entity_id": ["e1", "e2", "e3", "e1"],
            "concept_id": ["X", "X", "X", "Y"],
            "period": ["Q1"] * 4,
            "value": [1.0] * 4,
            "uom": ["USD"] * 4,
        }
    )
    relations = pd.DataFrame(
        {
            "concept_id_a": [],
            "concept_id_b": [],
            "period": [],
            "relation_type": [],
            "source_entity_id": [],
        }
    )
    return CanonicalBundle(periods, entities, concepts, facts, relations)


def test_concept_segment_profile_uses_plurality_of_using_entities():
    bundle = _bundle()
    complexity = pd.DataFrame(
        {"entity_id": ["e1", "e2", "e3"], "n_unique_tags": [10, 20, 30]}
    )

    profile = concept_segment_profile(bundle, "Q1", complexity).set_index("concept_id")

    # X used by e1(Services),e2(Services),e3(Finance) -> plurality Services.
    assert profile.loc["X", "dominant_industry"] == "Services"
    assert profile.loc["X", "dominant_size_class"] == "1-LAF"
    assert profile.loc["X", "mean_complexity"] == 20.0  # mean(10,20,30)

    # Y used only by e1 (Services, 1-LAF, complexity 10).
    assert profile.loc["Y", "dominant_industry"] == "Services"
    assert profile.loc["Y", "mean_complexity"] == 10.0


def test_concept_segment_profile_handles_entities_with_missing_size_class():
    # Real SEC data has blank `afs` for some filers -- a concept used only
    # by such filers must not crash the groupby (mode() on all-NaN is empty).
    bundle = _bundle()
    bundle.entities.loc[bundle.entities["entity_id"] == "e1", "size_class"] = None
    complexity = pd.DataFrame(
        {"entity_id": ["e1", "e2", "e3"], "n_unique_tags": [10, 20, 30]}
    )

    profile = concept_segment_profile(bundle, "Q1", complexity).set_index("concept_id")

    # Y is used only by e1, whose size_class is missing -> no crash, NaN result.
    assert pd.isna(profile.loc["Y", "dominant_size_class"])
