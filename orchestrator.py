"""Wrapper exposing workflow functions from :mod:`botml.workflow`."""

from botml.workflow import (
    load_price_data,
    generate_features_and_labels,
    train_random_forest,
    hyperopt_random_forest,
    backtest_model,
    run_live_trading,
    main,
)

__all__ = [
    "load_price_data",
    "generate_features_and_labels",
    "train_random_forest",
    "hyperopt_random_forest",
    "backtest_model",
    "run_live_trading",
    "main",
]

if __name__ == "__main__":
    main()
