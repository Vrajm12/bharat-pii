import json

import pytest

from generators.base_instances import (
    CATEGORY_COUNTS,
    SEED,
    _EXPECTED_DOMAIN_TOTALS,
    assert_dataset_valid,
    generate_pilot_base_instances,
    write_pilot_base_instances,
)


@pytest.fixture(scope="module")
def records():
    return generate_pilot_base_instances(SEED)


def test_generates_exactly_100_records(records):
    assert len(records) == 100


def test_category_counts_match_approved_table(records):
    counts = {}
    for r in records:
        category = r["base_id"].rsplit("_", 1)[0]
        counts[category] = counts.get(category, 0) + 1
    assert counts == CATEGORY_COUNTS


def test_all_records_are_positive_single_pii(records):
    for r in records:
        assert r["base_kind"] == "POSITIVE"
        assert len(r["pii"]) == 1


def test_all_records_use_frozen_semantic_role_mapping(records):
    from generators.base_instances import SEMANTIC_ROLE

    for r in records:
        category = r["base_id"].rsplit("_", 1)[0]
        assert r["pii"][0]["semantic_role"] == SEMANTIC_ROLE[category]


def test_domain_allocation_matches_approved_matrix(records):
    totals = {}
    for r in records:
        domain = r["scenario"]["domain"]
        totals[domain] = totals.get(domain, 0) + 1
    assert totals == _EXPECTED_DOMAIN_TOTALS


def test_no_domain_assigned_outside_the_approved_matrix(records):
    approved_domains = set(_EXPECTED_DOMAIN_TOTALS)
    for r in records:
        assert r["scenario"]["domain"] in approved_domains


def test_unique_base_ids(records):
    ids = [r["base_id"] for r in records]
    assert len(ids) == len(set(ids))


def test_unique_target_pii_value_within_each_category(records):
    seen = {}
    for r in records:
        category = r["base_id"].rsplit("_", 1)[0]
        value = r["pii"][0]["base_pii_value"]
        bucket = seen.setdefault(category, set())
        assert value not in bucket, f"duplicate {category} value: {value}"
        bucket.add(value)


def test_target_pii_occurs_exactly_once_in_canonical_text(records):
    for r in records:
        value = r["pii"][0]["base_pii_value"]
        assert r["canonical_text"].count(value) == 1


def test_address_structure_single_iff_address_type(records):
    for r in records:
        category = r["base_id"].rsplit("_", 1)[0]
        if category == "ADDRESS":
            assert r["address_structure"] == "SINGLE"
        else:
            assert r["address_structure"] is None


def test_all_synthetic_true(records):
    assert all(r["synthetic"] is True for r in records)


def test_name_deva_is_populated_for_all(records):
    """T07 (transliteration table) is implemented -- name_deva is populated
    via generators.translit.table.transliterate_value for every base."""
    from generators.translit.table import transliterate_value

    for r in records:
        name = r["person_context"]["name"]
        assert r["person_context"]["name_deva"] == transliterate_value(name)


def test_generator_version_recorded_on_every_record(records):
    for r in records:
        assert r["generator_version"] == "0.1.0"


def test_assert_dataset_valid_passes(records):
    assert_dataset_valid(records)  # must not raise


def test_generation_is_deterministic_under_seed_42():
    first = generate_pilot_base_instances(42)
    second = generate_pilot_base_instances(42)
    assert first == second


def test_write_refuses_to_overwrite_existing_file(tmp_path, records):
    target = tmp_path / "base_instances.jsonl"
    target.write_text("pre-existing content\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_pilot_base_instances(records, output_path=target)
    assert target.read_text(encoding="utf-8") == "pre-existing content\n"


def test_write_produces_valid_jsonl(tmp_path, records):
    target = tmp_path / "base_instances.jsonl"
    write_pilot_base_instances(records, output_path=target)
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 100
    parsed = [json.loads(line) for line in lines]
    assert parsed == records
