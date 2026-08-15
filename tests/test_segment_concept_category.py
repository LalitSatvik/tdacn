import pandas as pd

from tdacn.segment.concept_category import classify_concepts


def test_classify_concepts_assigns_dei_ahead_of_other_flags():
    concepts = pd.DataFrame(
        [
            {
                "concept_id": "EntityAddressStateOrProvince",
                "namespace": "dei",
                "is_abstract": False,
                "datatype": "normalizedstring",
            },
            {
                "concept_id": "AssetsAbstract",
                "namespace": "us-gaap",
                "is_abstract": True,
                "datatype": "",
            },
            {
                "concept_id": "AddressTypeDomain",
                "namespace": "us-gaap",
                "is_abstract": False,
                "datatype": "domain",
            },
            {
                "concept_id": "AdrMember",
                "namespace": "us-gaap",
                "is_abstract": False,
                "datatype": "member",
            },
            {
                "concept_id": "Assets",
                "namespace": "us-gaap",
                "is_abstract": False,
                "datatype": "monetary",
            },
        ]
    )

    categories = classify_concepts(concepts).set_index(concepts["concept_id"])["category"]

    assert categories["EntityAddressStateOrProvince"] == "dei"
    assert categories["AssetsAbstract"] == "abstract_header"
    assert categories["AddressTypeDomain"] == "dimensional"
    assert categories["AdrMember"] == "dimensional"
    assert categories["Assets"] == "accounting_fact"


def test_classify_concepts_dei_namespace_wins_even_if_also_abstract():
    concepts = pd.DataFrame(
        [
            {
                "concept_id": "DeiAbstractThing",
                "namespace": "dei",
                "is_abstract": True,
                "datatype": "",
            }
        ]
    )

    categories = classify_concepts(concepts).set_index(concepts["concept_id"])["category"]

    assert categories["DeiAbstractThing"] == "dei"
