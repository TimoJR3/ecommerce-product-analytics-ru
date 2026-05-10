from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import duckdb
import pandas as pd

from ecommerce_analytics.config import MARTS_DATA_DIR
from ecommerce_analytics.logging_utils import get_logger


logger = get_logger(__name__)

DATABASE_PATH = MARTS_DATA_DIR / "ecommerce.duckdb"
PROPENSITY_SCORES_PATH = MARTS_DATA_DIR / "propensity_scores.parquet"


def export_frame(data: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("CSV сохранен: %s", output_path)


def read_table_or_file(
    connection: duckdb.DuckDBPyConnection | None,
    table_name: str,
) -> pd.DataFrame | None:
    if connection is not None:
        try:
            return connection.execute(f"SELECT * FROM {table_name}").fetchdf()
        except duckdb.CatalogException:
            logger.warning("В DuckDB нет таблицы: %s", table_name)

    parquet_path = MARTS_DATA_DIR / f"{table_name}.parquet"
    csv_path = MARTS_DATA_DIR / f"{table_name}.csv"

    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    if csv_path.exists():
        return pd.read_csv(csv_path)

    logger.warning("Не найдена витрина для экспорта: %s", table_name)
    return None


def export_sessions_summary(connection: duckdb.DuckDBPyConnection) -> None:
    query = """
    WITH sessions AS (
        SELECT
            CAST(session_start AS DATE) AS session_date,
            CASE
                WHEN events_cnt = 1 THEN '01 событие'
                WHEN events_cnt BETWEEN 2 AND 3 THEN '02-03 события'
                WHEN events_cnt BETWEEN 4 AND 7 THEN '04-07 событий'
                WHEN events_cnt BETWEEN 8 AND 15 THEN '08-15 событий'
                ELSE '16+ событий'
            END AS session_depth_segment,
            COUNT(*) AS sessions_cnt,
            SUM(purchase_flag) AS purchase_sessions_cnt,
            SUM(CASE WHEN carts_cnt > 0 THEN 1 ELSE 0 END) AS cart_sessions_cnt,
            SUM(CASE WHEN carts_cnt > 0 AND purchases_cnt = 0 THEN 1 ELSE 0 END)
                AS abandoned_cart_sessions_cnt,
            SUM(revenue) AS revenue,
            AVG(session_duration_minutes) AS avg_session_duration_minutes,
            AVG(events_cnt) AS avg_events_cnt
        FROM fct_sessions
        GROUP BY
            session_date,
            session_depth_segment
    )
    SELECT
        session_date,
        session_depth_segment,
        sessions_cnt,
        purchase_sessions_cnt,
        cart_sessions_cnt,
        abandoned_cart_sessions_cnt,
        revenue,
        avg_session_duration_minutes,
        avg_events_cnt
    FROM sessions
    ORDER BY
        session_date,
        session_depth_segment
    """
    data = connection.execute(query).fetchdf()
    export_frame(data, MARTS_DATA_DIR / "datalens_sessions_summary.csv")


def export_propensity_scores() -> None:
    if not PROPENSITY_SCORES_PATH.exists():
        logger.warning(
            "Файл propensity_scores.parquet не найден. "
            "Экспорт datalens_propensity_scores.csv пропущен."
        )
        return

    data = pd.read_parquet(PROPENSITY_SCORES_PATH)
    if "model_score" not in data.columns:
        logger.warning(
            "В propensity_scores.parquet нет колонки model_score. "
            "Экспорт datalens_propensity_scores.csv пропущен."
        )
        return

    data = data.copy()
    data["score_decile"] = pd.qcut(
        data["model_score"].rank(method="first", ascending=False),
        q=10,
        labels=[f"D{i}" for i in range(1, 11)],
    )
    export_columns = [
        "session_id",
        "user_id",
        "session_start",
        "purchase_flag",
        "baseline_score",
        "model_score",
        "score_decile",
    ]
    existing_columns = [column for column in export_columns if column in data.columns]
    export_frame(
        data[existing_columns],
        MARTS_DATA_DIR / "datalens_propensity_scores.csv",
    )


def export_for_datalens() -> None:
    connection = None
    if DATABASE_PATH.exists():
        connection = duckdb.connect(str(DATABASE_PATH), read_only=True)
    else:
        logger.warning(
            "База data/marts/ecommerce.duckdb не найдена. "
            "Скрипт попробует использовать parquet или CSV из data/marts/."
        )

    try:
        exports = {
            "mart_funnel_daily": "datalens_funnel_daily.csv",
            "mart_retention": "datalens_retention.csv",
            "mart_product_conversion": "datalens_product_conversion.csv",
        }

        exported_any = False
        for table_name, file_name in exports.items():
            data = read_table_or_file(connection, table_name)
            if data is None:
                continue
            export_frame(data, MARTS_DATA_DIR / file_name)
            exported_any = True

        if connection is not None:
            export_sessions_summary(connection)
            exported_any = True
        else:
            logger.warning(
                "Сводка сессий требует таблицу fct_sessions в DuckDB. "
                "Экспорт datalens_sessions_summary.csv пропущен."
            )

        export_propensity_scores()

        if not exported_any:
            raise FileNotFoundError(
                "Не найдены витрины для DataLens. "
                "Сначала запустите python scripts/run_etl.py и python scripts/build_marts.py."
            )
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    export_for_datalens()
