from collections.abc import Iterable

import pandas as pd


REQUIRED_EVENT_COLUMNS = {
    "event_time",
    "event_type",
    "product_id",
    "category_id",
    "category_code",
    "brand",
    "price",
    "user_id",
    "user_session",
}


def find_missing_columns(
    columns: Iterable[str],
    required_columns: Iterable[str] = REQUIRED_EVENT_COLUMNS,
) -> set[str]:
    return set(required_columns) - set(columns)


def has_required_columns(
    columns: Iterable[str],
    required_columns: Iterable[str] = REQUIRED_EVENT_COLUMNS,
) -> bool:
    return not find_missing_columns(columns, required_columns)


def is_non_empty_frame(data: pd.DataFrame) -> bool:
    return not data.empty


def validate_event_frame(data: pd.DataFrame) -> None:
    missing_columns = find_missing_columns(data.columns)
    if missing_columns:
        ordered_columns = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {ordered_columns}")

    if data.empty:
        raise ValueError("Event data frame is empty")
