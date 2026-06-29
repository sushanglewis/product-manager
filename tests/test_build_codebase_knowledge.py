from pathlib import Path

from scripts.build_codebase_knowledge import scan_features


def test_scan_features_finds_top_level_dirs(tmp_path):
    (tmp_path / "src" / "auth").mkdir(parents=True)
    (tmp_path / "src" / "auth" / "login.py").write_text("def login(): pass")
    (tmp_path / "src" / "billing").mkdir()
    (tmp_path / "src" / "billing" / "invoice.py").write_text("def invoice(): pass")
    (tmp_path / "tests" / "auth").mkdir(parents=True)
    (tmp_path / "tests" / "auth" / "test_login.py").write_text("")

    result = scan_features(tmp_path, max_features=10)
    names = {f["name"] for f in result["features"]}
    assert "auth" in names
    assert "billing" in names
    assert result["root"] == str(tmp_path)


def test_scan_features_respects_max_features(tmp_path):
    (tmp_path / "src").mkdir()
    for i in range(15):
        (tmp_path / "src" / f"feat{i}").mkdir()
        (tmp_path / "src" / f"feat{i}" / "main.py").write_text("pass")

    result = scan_features(tmp_path, max_features=5)
    assert len(result["features"]) == 5
