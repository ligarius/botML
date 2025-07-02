"""Model management for training and prediction tasks."""

import joblib
from sklearn.ensemble import RandomForestClassifier
import pandas as pd


class ModelManager:
    """Load, train and use machine learning models for trading signals."""

    def __init__(self, config, logger):
        """Instantiate the manager and load any existing model.

        Parameters
        ----------
        config : dict
            Configuration parameters.
        logger : logging.Logger
            Logger for outputting progress information.
        """

        self.config = config
        self.logger = logger
        self.model_path = "model_rf.pkl"
        self.model = self._load_model()

    def _load_model(self):
        """Load the model from disk if present."""

        try:
            model = joblib.load(self.model_path)
            self.logger.info(
                f"Modelo cargado desde disco: {self.model_path}"
            )
            return model
        except Exception:
            self.logger.warning("No hay modelo, entrenar desde cero.")
            return None

    def predict(self, dfs):
        """Generate signals for provided data frames.

        Parameters
        ----------
        dfs : list[pandas.DataFrame]
            Data frames containing market information.

        Returns
        -------
        list[dict]
            List of signal dictionaries.
        """

        if not self.model:
            self.logger.warning("No hay modelo entrenado.")
            return []
        signals = []
        for df in dfs:
            if not df.empty:
                price = float(df["close"].astype(float).iloc[-1])
                usdt_amount = self.config.get("trade_size", 10)
                qty = usdt_amount / price if price else 0
                signal = {
                    "symbol": df["symbol"].iloc[-1],
                    "side": "BUY",
                    "score": 1.0,
                    "usdt_amount": usdt_amount,
                    "price": price,
                    "qty": qty,
                }
                signals.append(signal)
                self.logger.info(
                    "Se\u00f1al detectada | Symbol: %s | Acci\u00f3n: %s | Score: %s | Monto USDT: %s | Qty: %.8f | Precio: %.2f",
                    signal.get("symbol", "n/a"),
                    signal.get("side", "n/a"),
                    signal.get("score", "n/a"),
                    signal.get("usdt_amount", "n/a"),
                    signal.get("qty", 0.0),
                    signal.get("price", float("nan")),
                )
        return signals

    def need_retrain(self):
        """Determine whether the model requires retraining."""

        # Aquí una lógica simple de ejemplo: reentrenar cada 100 ciclos
        # Implementar un contador persistente en producción
        return self.model is None

    def retrain(self, dfs):
        """Retrain the model using the supplied data frames."""

        self.logger.info("Entrenando modelo RandomForest...")
        X, y = [], []
        for df in dfs:
            if not df.empty:
                X.extend(df["close"].astype(float).values.reshape(-1, 1))
                y.extend([1] * len(df))
        if X and y:
            model = RandomForestClassifier()
            model.fit(X, y)
            joblib.dump(model, self.model_path)
            self.model = model
            self.logger.info("Modelo entrenado y guardado.")

    def stats(self):
        """Return metrics about the current model."""

        return {}
