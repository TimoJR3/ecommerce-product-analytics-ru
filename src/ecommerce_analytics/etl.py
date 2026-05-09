from pathlib import Path
from typing import Sequence

import pandas as pd

from ecommerce_analytics.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from ecommerce_analytics.data_checks import REQUIRED_EVENT_COLUMNS, find_missing_columns
from ecommerce_analytics.logging_utils import get_logger


logger = get_logger(__name__)
PROCESSED_EVENTS_FILE = PROCESSED_DATA_DIR / "events_clean.parquet"


def find_raw_files(raw_data_dir: Path = RAW_DATA_DIR) -> list[Path]:
    return sorted(raw_data_dir.glob("*.csv"))


def load_raw_events(raw_files: Sequence[Path] | None = None) -> pd.DataFrame:
    files = list(raw_files) if raw_files is not None else find_raw_files()

    if not files:
        raise FileNotFoundError(
            "В data/raw/ не найдены CSV-файлы. "
            "Положите сырые файлы Kaggle в data/raw/ и запустите ETL повторно."
        )

    frames = [pd.read_csv(file) for file in files]
    return pd.concat(frames, ignore_index=True)


def clean_events(events: pd.DataFrame) -> pd.DataFrame:
    missing_columns = find_missing_columns(events.columns, REQUIRED_EVENT_COLUMNS)
    if missing_columns:
        ordered_columns = ", ".join(sorted(missing_columns))
        raise ValueError(f"В сырых данных отсутствуют обязательные колонки: {ordered_columns}")

    clean_data = events.copy()
    clean_data["event_time"] = pd.to_datetime(clean_data["event_time"], errors="coerce")
    clean_data["price"] = pd.to_numeric(clean_data["price"], errors="coerce").astype(float)
    clean_data = clean_data.drop_duplicates()
    clean_data = clean_data[clean_data["price"] >= 0].reset_index(drop=True)
    return clean_data


def save_processed_events(
    events: pd.DataFrame,
    output_path: Path = PROCESSED_EVENTS_FILE,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    events.to_parquet(output_path, index=False)
    return output_path


def _sql_string(value: Path) -> str:
    return "'" + value.resolve().as_posix().replace("'", "''") + "'"


def _validate_raw_file_columns(raw_files: Sequence[Path]) -> None:
    for file in raw_files:
        columns = pd.read_csv(file, nrows=0).columns
        missing_columns = find_missing_columns(columns, REQUIRED_EVENT_COLUMNS)
        if missing_columns:
            ordered_columns = ", ".join(sorted(missing_columns))
            raise ValueError(
                f"В файле {file.name} отсутствуют обязательные колонки: {ordered_columns}"
            )


def _save_processed_events_with_duckdb(
    raw_files: Sequence[Path],
    output_path: Path,
) -> Path:
    import duckdb

    output_path.parent.mkdir(parents=True, exist_ok=True)
    files_sql = "[" + ", ".join(_sql_string(file) for file in raw_files) + "]"
    output_sql = _sql_string(output_path)

    query = f"""
    COPY (
        SELECT DISTINCT
            TRY_CAST(event_time AS TIMESTAMP) AS event_time,
            event_type,
            product_id,
            category_id,
            category_code,
            brand,
            TRY_CAST(price AS DOUBLE) AS price,
            user_id,
            user_session
        FROM read_csv_auto({files_sql}, union_by_name = true, header = true)
        WHERE TRY_CAST(price AS DOUBLE) >= 0
    )
    TO {output_sql}
    (FORMAT PARQUET)
    """

    with duckdb.connect() as connection:
        connection.execute(query)

    return output_path


def run_etl(
    raw_data_dir: Path = RAW_DATA_DIR,
    output_path: Path = PROCESSED_EVENTS_FILE,
) -> Path:
    raw_files = find_raw_files(raw_data_dir)
    logger.info("Найдено CSV-файлов: %s", len(raw_files))

    if not raw_files:
        load_raw_events(raw_files)

    _validate_raw_file_columns(raw_files)

    saved_path = _save_processed_events_with_duckdb(raw_files, output_path)
    logger.info("Очищенные события сохранены: %s", saved_path)
    return saved_path
