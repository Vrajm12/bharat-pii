"""Package import and namespace governance tests."""

import bharatpii
from bharatpii import BharatPII, Entity, PredictionResult, __version__


def test_package_import_and_version():
    assert __version__ == "1.0.0"
    assert hasattr(bharatpii, "BharatPII")
    assert hasattr(bharatpii, "Entity")
    assert hasattr(bharatpii, "PredictionResult")


def test_entity_dataclass():
    ent = Entity(text="Rahul", start=0, end=5, label="PERSON", score=0.95)
    d = ent.to_dict()
    assert d["text"] == "Rahul"
    assert d["start"] == 0
    assert d["end"] == 5
    assert d["label"] == "PERSON"
    assert d["score"] == 0.95


def test_prediction_result_dataclass():
    ent = Entity(text="ABCDE1234F", start=10, end=20, label="PAN", score=0.99)
    res = PredictionResult(text="My PAN is ABCDE1234F", entities=[ent])
    assert len(res) == 1
    assert res[0].label == "PAN"
    d = res.to_dict()
    assert d["text"] == "My PAN is ABCDE1234F"
    assert len(d["entities"]) == 1
