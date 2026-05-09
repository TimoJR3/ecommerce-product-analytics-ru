from pathlib import Path
from typing import Iterable

import duckdb

from ecommerce_analytics.config import MARTS_DATA_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT
from ecommerce_analytics.logging_utils import get_logger


logger = get_logger(__name__)

SQL_DIR = PROJECT_ROOT / "sql"
EVENTS_PARQUET = PROCESSED_DATA_DIR / "events_clean.parquet"
MARTS_DATABASE = MARTS_DATA_DIR / "ecommerce.duckdb"
SQL_SCRIPTS = [
    "01_create_fct_events.sql",
    "02_create_fct_sessions.sql",
    "03_create_mart_funnel_daily.sql",
    "04_create_mart_retention.sql",
    "05_create_mart_product_conversion.sql",
]
EXPORT_TABLES = [
    "mart_funnel_daily",
    "mart_retention",
    "mart_product_conversion",
]


def _sql_path(value: Path) -> str:
    return value.resolve().as_posix().replace("'", "''")


def _render_sql(sql_text: str, events_parquet: Path) -> str:
    return sql_text.replace("{{EVENTS_PARQUET}}", _sql_path(events_parquet))


def execute_sql_scripts(
    connection: duckdb.DuckDBPyConnection,
    sql_dir: Path,
    events_parquet: Path,
    scripts: Iterable[str] = SQL_SCRIPTS,
) -> None:
    for script_name in scripts:
        script_path = sql_dir / script_name
        logger.info("Выполняется SQL-скрипт: %s", script_path.name)
        sql_text = script_path.read_text(encoding="utf-8")
        connection.execute(_render_sql(sql_text, events_parquet))


def export_marts(
    connection: duckdb.DuckDBPyConnection,
    marts_dir: Path,
    tables: Iterable[str] = EXPORT_TABLES,
) -> None:
    marts_dir.mkdir(parents=True, exist_ok=True)

    for table in tables:
        parquet_path = marts_dir / f"{table}.parquet"
        csv_path = marts_dir / f"{table}.csv"
        logger.info("Экспорт витрины: %s", table)
        connection.execute(
            f"COPY {table} TO '{_sql_path(parquet_path)}' (FORMAT PARQUET)"
        )
        connection.execute(
            f"COPY {table} TO '{_sql_path(csv_path)}' (HEADER, DELIMITER ',')"
        )


def build_marts(
    events_parquet: Path = EVENTS_PARQUET,
    database_path: Path = MARTS_DATABASE,
    sql_dir: Path = SQL_DIR,
    marts_dir: Path = MARTS_DATA_DIR,
) -> Path:
    if not events_parquet.exists():
        raise FileNotFoundError(
            "Не найден файл data/processed/events_clean.parquet. "
            "Сначала запустите python scripts/run_etl.py."
        )

    database_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(database_path)) as connection:
        execute_sql_scripts(connection, sql_dir, events_parquet)
        export_marts(connection, marts_dir)

    logger.info("DuckDB-база сохранена: %s", database_path)
    return database_path
