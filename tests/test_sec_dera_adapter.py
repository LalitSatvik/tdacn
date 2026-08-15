import pandas as pd

from tdacn.adapters.sec_dera import SecDeraAdapter
from tdacn.schema import validate_bundle


def _write_tsv(path, rows):
    """rows: list of dicts, all sharing the same keys (used as header)."""
    df = pd.DataFrame(rows)
    df.to_csv(path, sep="\t", index=False)


def _write_quarter(tmp_path, name, sub_rows, tag_rows, num_rows, pre_rows):
    qdir = tmp_path / name
    qdir.mkdir()
    _write_tsv(qdir / "sub.txt", sub_rows)
    _write_tsv(qdir / "tag.txt", tag_rows)
    _write_tsv(qdir / "num.txt", num_rows)
    _write_tsv(qdir / "pre.txt", pre_rows)
    return qdir


def _basic_quarter(tmp_path, name="Q1"):
    """A quarter with one 10-K filer (kept) and one 8-K filer (dropped)."""
    sub_rows = [
        {"adsh": "0000001-24-000001", "cik": 1, "sic": 7372, "afs": "1-LAF", "form": "10-K"},
        {"adsh": "0000002-24-000002", "cik": 2, "sic": 2834, "afs": "4-SRC", "form": "8-K"},
    ]
    tag_rows = [
        {"tag": "Assets", "version": "us-gaap/2023", "custom": 0, "abstract": 0, "datatype": "monetary", "tlabel": "Assets"},
        {"tag": "Liabilities", "version": "us-gaap/2023", "custom": 0, "abstract": 0, "datatype": "monetary", "tlabel": "Liabilities"},
        {"tag": "StockholdersEquity", "version": "us-gaap/2023", "custom": 0, "abstract": 0, "datatype": "monetary", "tlabel": "Equity"},
        {"tag": "MyCustomMetric", "version": "0000001-24-000001", "custom": 1, "abstract": 0, "datatype": "monetary", "tlabel": "My Custom Metric"},
    ]
    num_rows = [
        {"adsh": "0000001-24-000001", "tag": "Assets", "version": "us-gaap/2023", "value": 100.0, "uom": "USD"},
        {"adsh": "0000001-24-000001", "tag": "Liabilities", "version": "us-gaap/2023", "value": 40.0, "uom": "USD"},
        {"adsh": "0000002-24-000002", "tag": "Assets", "version": "us-gaap/2023", "value": 999.0, "uom": "USD"},
    ]
    pre_rows = [
        {"adsh": "0000001-24-000001", "stmt": "BS", "line": 1, "tag": "Assets"},
        {"adsh": "0000001-24-000001", "stmt": "BS", "line": 2, "tag": "Liabilities"},
        {"adsh": "0000001-24-000001", "stmt": "BS", "line": 3, "tag": "StockholdersEquity"},
        {"adsh": "0000002-24-000002", "stmt": "BS", "line": 1, "tag": "Assets"},
    ]
    return _write_quarter(tmp_path, name, sub_rows, tag_rows, num_rows, pre_rows)


def test_load_period_produces_a_valid_bundle(tmp_path):
    qdir = _basic_quarter(tmp_path)
    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)

    validate_bundle(bundle)


def test_load_period_drops_non_10k_10q_filers(tmp_path):
    qdir = _basic_quarter(tmp_path)
    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)

    entity_ids = set(bundle.entities["entity_id"])
    assert entity_ids == {"1"}


def test_load_period_maps_afs_and_sic_to_size_class_and_industry(tmp_path):
    qdir = _basic_quarter(tmp_path)
    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)

    row = bundle.entities.set_index("entity_id").loc["1"]
    assert row["size_class"] == "1-LAF"
    assert row["industry_code"] == "7372"


def test_load_period_facts_exclude_dropped_filers(tmp_path):
    qdir = _basic_quarter(tmp_path)
    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)

    assert set(bundle.facts["entity_id"]) == {"1"}
    assert len(bundle.facts) == 2  # Assets + Liabilities for cik 1 only


def test_load_period_concepts_are_restricted_to_used_tags_and_flag_custom(tmp_path):
    qdir = _basic_quarter(tmp_path)
    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)

    concept_ids = set(bundle.concepts["concept_id"])
    # StockholdersEquity appears in pre.txt (relations) but not in num.txt facts
    # for a kept filer -> still a used concept via the structural layer.
    assert concept_ids == {"Assets", "Liabilities", "StockholdersEquity"}
    is_custom = bundle.concepts.set_index("concept_id")["is_custom"]
    assert bool(is_custom.get("Assets")) is False


def test_load_period_builds_structural_relations_from_adjacent_pre_lines(tmp_path):
    qdir = _basic_quarter(tmp_path)
    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)

    pairs = set(
        zip(bundle.relations["concept_id_a"], bundle.relations["concept_id_b"])
    )
    # 3-line BS statement for cik 1 -> 2 adjacent pairs; cik 2 was dropped.
    assert pairs == {("Assets", "Liabilities"), ("Liabilities", "StockholdersEquity")}
    assert set(bundle.relations["relation_type"]) == {"structural"}


def test_load_period_relations_carry_the_source_statement_type(tmp_path):
    qdir = _basic_quarter(tmp_path)
    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)

    assert (bundle.relations["stmt"] == "BS").all()


def test_load_period_concepts_carry_namespace_and_abstract_flag(tmp_path):
    sub_rows = [
        {"adsh": "0000001-24-000001", "cik": 1, "sic": 7372, "afs": "1-LAF", "form": "10-K"},
    ]
    tag_rows = [
        {"tag": "Assets", "version": "us-gaap/2023", "custom": 0, "abstract": 0, "datatype": "monetary", "tlabel": "Assets"},
        {"tag": "AssetsAbstract", "version": "us-gaap/2023", "custom": 0, "abstract": 1, "datatype": "", "tlabel": "Assets [Abstract]"},
        {"tag": "EntityAddressStateOrProvince", "version": "dei/2023", "custom": 0, "abstract": 0, "datatype": "normalizedstring", "tlabel": "Entity Address, State or Province"},
    ]
    num_rows = [
        {"adsh": "0000001-24-000001", "tag": "Assets", "version": "us-gaap/2023", "value": 100.0, "uom": "USD"},
        {"adsh": "0000001-24-000001", "tag": "EntityAddressStateOrProvince", "version": "dei/2023", "value": 0.0, "uom": "pure"},
    ]
    pre_rows = [
        {"adsh": "0000001-24-000001", "stmt": "BS", "line": 1, "tag": "AssetsAbstract"},
        {"adsh": "0000001-24-000001", "stmt": "BS", "line": 2, "tag": "Assets"},
    ]
    qdir = _write_quarter(tmp_path, "Q1", sub_rows, tag_rows, num_rows, pre_rows)

    bundle = SecDeraAdapter().load_period(str(qdir), period_id="Q1", order=0)
    concepts = bundle.concepts.set_index("concept_id")

    assert concepts.loc["Assets", "namespace"] == "us-gaap"
    assert concepts.loc["Assets", "is_abstract"] == False  # noqa: E712
    assert concepts.loc["AssetsAbstract", "is_abstract"] == True  # noqa: E712
    assert concepts.loc["EntityAddressStateOrProvince", "namespace"] == "dei"


def test_load_combines_multiple_periods(tmp_path):
    q1 = _basic_quarter(tmp_path, "Q1")
    q2 = _basic_quarter(tmp_path, "Q2")

    bundle = SecDeraAdapter().load(
        [("Q1", str(q1), 0), ("Q2", str(q2), 1)]
    )

    assert list(bundle.periods.sort_values("order")["period_id"]) == ["Q1", "Q2"]
    assert set(bundle.entities["period"]) == {"Q1", "Q2"}
    validate_bundle(bundle)
