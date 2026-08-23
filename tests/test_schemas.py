import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_base_instance_fixture_validates():
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _load(FIXTURES / "base_instance.valid.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(instance)


def test_example_fixture_validates():
    schema = _load(SCHEMAS / "example.schema.json")
    instance = _load(FIXTURES / "example.valid.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(instance)
