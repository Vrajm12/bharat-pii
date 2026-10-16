import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent


def pii_item_validator() -> Draft202012Validator:
    """A validator for a single schemas/base_instance.schema.json pii[]
    entry, standing alone (its own $defs copied in so '#/$defs/pii_type'
    still resolves). Lets generator tests confirm their output is shaped
    correctly for the eventual base-instance generator (T04) without
    building a full base instance here."""
    schema = json.loads(
        (ROOT / "schemas" / "base_instance.schema.json").read_text(encoding="utf-8")
    )
    item_schema = dict(schema["properties"]["pii"]["items"])
    item_schema["$defs"] = schema["$defs"]
    item_schema["$schema"] = schema["$schema"]
    return Draft202012Validator(item_schema)
