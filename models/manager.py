import joblib
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

class ModelManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.model_path = "model_rf.pkl"
        self.model = self._load_model()

    def _load_model(self):
        try:
            model = joblib.load(self.model_path)
            self.logger.info("Modelo cargado desde disco.")
            return model
        except:
            self.logger.warning("No hay modelo, entrenar desde cero.")
            return None

    def predict(self, dfs):
        if not self.model:
            self.logger.warning("No hay modelo entrenado.")
            return []
        # Dummy: para cada DataFrame, retorna una señal aleatoria
        signals = []
        for df in dfs:
            if not df.empty:
                # Aquí deberías construir features
                signals.append({"symbol": df["symbol"][0], "signal": "buy"})
        return signals

    def need_retrain(self):
        # Aquí una lógica simple de ejemplo: reentrenar cada 100 ciclos
        # Implementar un contador persistente en producción
        return self.model is None

    def retrain(self, dfs):
        # Entrenamiento dummy, reemplaza con lógica real
        self.logger.info("Entrenando modelo RandomForest...")
        X, y = [], []
        for df in dfs:
            if not df.empty:
                # Ejemplo: usar precio de cierre como dummy
                X.extend(df["close"].astype(float).values.reshape(-1,1))
                y.extend([1]*len(df)) # Dummy: siempre '1'
        if X and y:
            model = RandomForestClassifier()
            model.fit(X, y)
            joblib.dump(model, self.model_path)
            self.model = model
            self.logger.info("Modelo entrenado y guardado.")

    def stats(self):
        return {}
