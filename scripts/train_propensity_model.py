from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecommerce_analytics.features import build_session_features
from ecommerce_analytics.logging_utils import get_logger
from ecommerce_analytics.modeling import (
    evaluate_model,
    make_time_split,
    save_metrics,
    save_scores,
    train_baseline_model,
    train_tree_model,
)


logger = get_logger(__name__)


if __name__ == "__main__":
    features = build_session_features()
    train_data, test_data = make_time_split(features)

    logger.info("Обучающая выборка: %s строк", len(train_data))
    logger.info("Тестовая выборка: %s строк", len(test_data))

    baseline_model = train_baseline_model(train_data)
    tree_model = train_tree_model(train_data)

    metrics = {
        "baseline_logistic_regression": evaluate_model(baseline_model, test_data),
        "hist_gradient_boosting": evaluate_model(tree_model, test_data),
    }
    metrics_path = save_metrics(metrics)
    scores_path = save_scores(features, baseline_model, tree_model)

    logger.info("Метрики сохранены: %s", metrics_path)
    logger.info("Скоринги сохранены: %s", scores_path)
