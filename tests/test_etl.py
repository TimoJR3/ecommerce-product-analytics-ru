from pathlib import Path

import pandas as pd
import pytest

from ecommerce_analytics.etl import (
    clean_events,
    find_raw_files,
    load_raw_events,
    save_processed_events,
)


def make_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_time": "2019-10-01 00:00:00 UTC",
                "event_type": "view",
                "product_id": 1,
                "category_id": 10,
                "category_code": "beauty",
                "brand": "brand_a",
                "price": "12.5",
                "user_id": 100,
                "user_session": "session_a",
            },
            {
                "event_time": "2019-10-01 00:00:00 UTC",
                "event_type": "view",
                "product_id": 1,
                "category_id": 10,
                "category_code": "beauty",
                "brand": "brand_a",
                "price": "12.5",
                "user_id": 100,
                "user_session": "session_a",
            },
            {
                "event_time": "2019-10-01 00:01:00 UTC",
                "event_type": "cart",
                "product_id": 2,
                "category_id": 20,
                "category_code": "beauty",
                "brand": "brand_b",
                "price": "-1",
                "user_id": 200,
                "user_session": "session_b",
            },
        ]
    )


def test_clean_events_removes_duplicates() -> None:
    clean_data = clean_events(make_events())

    assert len(clean_data) == 1


def test_clean_events_removes_negative_price() -> None:
    clean_data = clean_events(make_events())

    assert (clean_data["price"] >= 0).all()


def test_clean_events_checks_required_columns() -> None:
    data = make_events().drop(columns=["user_session"])

    with pytest.raises(ValueError, match="обязательные колонки"):
        clean_events(data)


def test_save_processed_events_writes_parquet(tmp_path: Path) -> None:
    output_path = tmp_path / "events_clean.parquet"
    clean_data = clean_events(make_events())

    saved_path = save_processed_events(clean_data, output_path)

    assert saved_path == output_path
    assert output_path.exists()
    loaded_data = pd.read_parquet(output_path)
    assert len(loaded_data) == len(clean_data)


def test_load_raw_events_raises_clear_error_when_files_are_missing(
    tmp_path: Path,
) -> None:
    raw_files = find_raw_files(tmp_path)

    assert raw_files == []
    with pytest.raises(FileNotFoundError, match="не найдены CSV-файлы"):
        load_raw_events(raw_files)
