import pandas as pd
import pytest

from ecommerce_analytics.data_checks import (
    REQUIRED_EVENT_COLUMNS,
    find_missing_columns,
    has_required_columns,
    is_non_empty_frame,
    validate_event_frame,
)


def test_has_required_columns_for_complete_schema() -> None:
    assert has_required_columns(REQUIRED_EVENT_COLUMNS)


def test_find_missing_columns_returns_missing_values() -> None:
    columns = REQUIRED_EVENT_COLUMNS - {"price", "user_session"}

    assert find_missing_columns(columns) == {"price", "user_session"}


def test_is_non_empty_frame() -> None:
    data = pd.DataFrame([{"event_type": "view"}])

    assert is_non_empty_frame(data)


def test_validate_event_frame_raises_for_missing_columns() -> None:
    data = pd.DataFrame([{"event_type": "view"}])

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_event_frame(data)


def test_validate_event_frame_raises_for_empty_frame() -> None:
    data = pd.DataFrame(columns=sorted(REQUIRED_EVENT_COLUMNS))

    with pytest.raises(ValueError, match="empty"):
        validate_event_frame(data)
