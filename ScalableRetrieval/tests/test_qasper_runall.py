from unittest.mock import patch

from src.datasets.qasper_runall import main


@patch("src.datasets.qasper_runall.run_step05")
@patch("src.datasets.qasper_runall.run_step04")
@patch("src.datasets.qasper_runall.run_step03")
@patch("src.datasets.qasper_runall.run_step02")
@patch("src.datasets.qasper_runall.run_step01")
def test_runall_all_documents_uses_manifest_count_and_all_pages(
    mock_step01,
    mock_step02,
    mock_step03,
    mock_step04,
    mock_step05,
):
    with patch(
        "sys.argv",
        ["qasper_runall", "--all-documents", "--strategy", "section_aware"],
    ):
        main()

    mock_step01.assert_called_once()
    assert mock_step01.call_args.kwargs["limit"] == 1585
    mock_step02.assert_called_once()
    assert mock_step02.call_args.kwargs["pages"] is None
    mock_step03.assert_called_once()
    assert mock_step03.call_args.kwargs["strategy"] == "section_aware"


@patch("src.datasets.qasper_runall.run_step05")
@patch("src.datasets.qasper_runall.run_step04")
@patch("src.datasets.qasper_runall.run_step03")
@patch("src.datasets.qasper_runall.run_step02")
@patch("src.datasets.qasper_runall.run_step01")
def test_runall_limit_and_pages_remain_available_for_smoke_tests(
    mock_step01,
    mock_step02,
    mock_step03,
    mock_step04,
    mock_step05,
):
    with patch("sys.argv", ["qasper_runall", "--limit", "25", "--pages", "1-2"]):
        main()

    assert mock_step01.call_args.kwargs["limit"] == 25
    assert mock_step02.call_args.kwargs["pages"] == "1-2"
