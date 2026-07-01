
from record_interview.cli import main


def test_main_launches_tui_when_tty(mocker):
    mocker.patch("sys.stdin.isatty", return_value=True)
    mocker.patch("sys.stdout.isatty", return_value=True)
    app_mock = mocker.MagicMock()
    app_mock.run.return_value = 0
    mocker.patch("record_interview.cli.LincolnRecordApp", return_value=app_mock)
    mocker.patch("record_interview.cli.resolve_workspace_root", return_value=mocker.MagicMock())
    result = main(["2026-06-27-test"])
    assert result == 0
    app_mock.run.assert_called_once()


def test_main_uses_no_tui_flow(mocker, tmp_path):
    mocker.patch("sys.stdin.isatty", return_value=False)
    run_flow = mocker.patch("record_interview.cli.run_recording_flow", return_value=0)
    mocker.patch("record_interview.cli.resolve_workspace_root", return_value=tmp_path)
    result = main(["2026-06-27-test", "--no-tui", "--no-confirm"])
    assert result == 0
    run_flow.assert_called_once()


def test_main_returns_error_on_invalid_session():
    result = main(["bad session"])
    assert result == 1
