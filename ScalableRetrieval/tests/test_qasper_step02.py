from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.datasets.qasper_step02_parse import run_step02


@patch("src.datasets.qasper_step02_parse.parse_next_pending_document")
@patch("src.datasets.qasper_step02_parse.AzureParser")
@patch("src.datasets.qasper_step02_parse.build_session_factory_from_url")
def test_run_step02_processes_until_none(
    mock_bf, mock_parser_class, mock_parse_next, tmp_path
):
    mock_parser = MagicMock()
    mock_parser_class.from_settings.return_value = mock_parser
    
    # Mock parse_next_pending_document to return something 3 times then None
    mock_parse_next.side_effect = [
        MagicMock(document_id=1),
        MagicMock(document_id=2),
        MagicMock(document_id=3),
        None
    ]
    
    run_step02(parsed_dir=tmp_path / "parsed", database_url="sqlite:///:memory:")
    
    assert mock_parse_next.call_count == 4


@patch("src.datasets.qasper_step02_parse.parse_next_pending_document")
@patch("src.datasets.qasper_step02_parse.AzureParser")
@patch("src.datasets.qasper_step02_parse.build_session_factory_from_url")
def test_run_step02_continues_after_one_document_parse_failure(
    mock_bf, mock_parser_class, mock_parse_next, tmp_path
):
    mock_parser = MagicMock()
    mock_parser_class.from_settings.return_value = mock_parser
    mock_parse_next.side_effect = [
        MagicMock(document_id=1),
        RuntimeError("azure internal error"),
        MagicMock(document_id=3),
        None,
    ]

    run_step02(parsed_dir=tmp_path / "parsed", database_url="sqlite:///:memory:")

    assert mock_parse_next.call_count == 4
