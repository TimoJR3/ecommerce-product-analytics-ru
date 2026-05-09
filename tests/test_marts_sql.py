from pathlib import Path

import duckdb
import pandas as pd

from ecommerce_analytics.build_marts import SQL_DIR, SQL_SCRIPTS, build_marts


def make_sample_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_time": pd.Timestamp("2020-01-01 10:00:00"),
                "event_type": "view",
                "product_id": 1,
                "category_id": 10,
                "category_code": "beauty.face",
                "brand": "brand_a",
                "price": 10.0,
                "user_id": 100,
                "user_session": "session_100",
            },
            {
                "event_time": pd.Timestamp("2020-01-01 10:05:00"),
                "event_type": "cart",
                "product_id": 1,
                "category_id": 10,
                "category_code": "beauty.face",
                "brand": "brand_a",
                "price": 10.0,
                "user_id": 100,
                "user_session": "session_100",
            },
            {
                "event_time": pd.Timestamp("2020-01-01 10:10:00"),
                "event_type": "purchase",
                "product_id": 1,
                "category_id": 10,
                "category_code": "beauty.face",
                "brand": "brand_a",
                "price": 10.0,
                "user_id": 100,
                "user_session": "session_100",
            },
            {
                "event_time": pd.Timestamp("2020-02-01 11:00:00"),
                "event_type": "purchase",
                "product_id": 2,
                "category_id": 20,
                "category_code": "beauty.hair",
                "brand": "brand_b",
                "price": 20.0,
                "user_id": 100,
                "user_session": "",
            },
            {
                "event_time": pd.Timestamp("2020-02-01 12:00:00"),
                "event_type": "view",
                "product_id": 3,
                "category_id": 30,
                "category_code": "beauty.nails",
                "brand": "brand_c",
                "price": 30.0,
                "user_id": 200,
                "user_session": None,
            },
        ]
    )


def table_exists(database_path: Path, table_name: str) -> bool:
    with duckdb.connect(str(database_path)) as connection:
        result = connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = ?
            """,
            [table_name],
        ).fetchone()
    return result[0] == 1


def test_sql_files_exist() -> None:
    for script_name in SQL_SCRIPTS:
        assert (SQL_DIR / script_name).exists()


def test_build_marts_smoke_on_sample_parquet(tmp_path: Path) -> None:
    events_path = tmp_path / "events_clean.parquet"
    database_path = tmp_path / "ecommerce.duckdb"
    marts_dir = tmp_path / "marts"
    make_sample_events().to_parquet(events_path, index=False)

    saved_database = build_marts(
        events_parquet=events_path,
        database_path=database_path,
        marts_dir=marts_dir,
    )

    assert saved_database == database_path
    assert database_path.exists()
    assert (marts_dir / "mart_funnel_daily.parquet").exists()
    assert (marts_dir / "mart_funnel_daily.csv").exists()


def test_fct_sessions_is_created(tmp_path: Path) -> None:
    events_path = tmp_path / "events_clean.parquet"
    database_path = tmp_path / "ecommerce.duckdb"
    make_sample_events().to_parquet(events_path, index=False)

    build_marts(events_parquet=events_path, database_path=database_path, marts_dir=tmp_path)

    assert table_exists(database_path, "fct_sessions")


def test_mart_funnel_daily_is_created(tmp_path: Path) -> None:
    events_path = tmp_path / "events_clean.parquet"
    database_path = tmp_path / "ecommerce.duckdb"
    make_sample_events().to_parquet(events_path, index=False)

    build_marts(events_parquet=events_path, database_path=database_path, marts_dir=tmp_path)

    assert table_exists(database_path, "mart_funnel_daily")
