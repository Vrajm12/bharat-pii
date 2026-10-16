"""Model loading, parameter verification, and error handling tests."""

from pathlib import Path
import pytest
from bharatpii import BharatPII

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"


def test_model_loading_and_parameter_counts():
    model = BharatPII.from_pretrained(MODEL_DIR, verify_checksums=True)
    assert model.total_parameters == 278057044
    assert model.encoder_parameters == 278043648
    assert model.trainable_head_parameters == 13396

    assert len(model.labels) == 17
    assert model.labels[0] == "O"
    assert model.labels[1] == "B-PERSON"
    assert model.labels[3] == "B-PAN"


def test_model_info():
    model = BharatPII.from_pretrained(MODEL_DIR)
    info = model.info()
    assert info["package_version"] == "1.0.0"
    assert info["model_name"] == "BharatPII-CRF"
    assert info["total_parameters"] == 278057044
    assert info["encoder_parameters"] == 278043648
    assert info["trainable_head_parameters"] == 13396
    assert info["num_labels"] == 17
    assert info["base_model"] == "XLM-RoBERTa-base"
    assert info["offline_mode"] is True


def test_missing_model_directory_raises():
    with pytest.raises(FileNotFoundError):
        BharatPII.from_pretrained(REPO_ROOT / "non_existent_directory_12345")


def test_corrupted_manifest_raises(tmp_path):
    # Empty dir raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        BharatPII.from_pretrained(tmp_path)
