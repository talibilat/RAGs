import json
import random
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.datasets.qasper_step01_ingest import run_step01


@pytest.fixture
def mock_manifest(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    data = {
        "documents": [
            {"doc_id": f"doc_{i}", "pdf_path": f"path_{i}.pdf"} for i in range(100)
        ]
    }
    manifest_path.write_text(json.dumps(data))
    return manifest_path


@patch("src.datasets.qasper_step01_ingest.ingest_file")
@patch("src.datasets.qasper_step01_ingest.settings")
def test_run_step01_samples_correct_number_of_docs(
    mock_settings, mock_ingest, mock_manifest, tmp_path
):
    mock_settings.QASPER_EVAL_LIMIT = 10
    mock_settings.postgres_dsn = "sqlite:///:memory:"
    
    # We need to mock the session factory too
    with patch("src.datasets.qasper_step01_ingest.build_session_factory") as mock_bf:
        run_step01(manifest_path=mock_manifest, storage_dir=tmp_path / "storage")

    assert mock_ingest.call_count == 10
