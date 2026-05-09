from ecommerce_analytics import config


def test_project_paths_are_inside_project_root() -> None:
    assert config.DATA_DIR == config.PROJECT_ROOT / "data"
    assert config.RAW_DATA_DIR == config.DATA_DIR / "raw"
    assert config.PROCESSED_DATA_DIR == config.DATA_DIR / "processed"
    assert config.MARTS_DATA_DIR == config.DATA_DIR / "marts"
    assert config.REPORTS_DIR == config.PROJECT_ROOT / "reports"
    assert config.ASSETS_DIR == config.PROJECT_ROOT / "assets"


def test_expected_directories_exist() -> None:
    assert config.DATA_DIR.exists()
    assert config.RAW_DATA_DIR.exists()
    assert config.PROCESSED_DATA_DIR.exists()
    assert config.MARTS_DATA_DIR.exists()
    assert config.REPORTS_DIR.exists()
    assert config.ASSETS_DIR.exists()
