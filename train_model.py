# train_model.py
import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
import pickle
from pathlib import Path
import yaml

# Load configuration
with open(Path(__file__).resolve().parent / 'config.yaml', 'r') as fh:
    CONFIG = yaml.safe_load(fh)

DB_PATH = CONFIG.get('database_path', 'binance_1m.db')
SYMBOL = (CONFIG.get('symbols') or ['BTCUSDT'])[0]

# 1. Cargar datos históricos
conn = sqlite3.connect(DB_PATH)
table = f"_{SYMBOL}"
try:
    df = pd.read_sql(f'SELECT * FROM {table}', conn)
except Exception as exc:
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    existing = ", ".join(t[0] for t in tables)
    raise SystemExit(
        f"Table {table} not found in {DB_PATH}.\n"
        "Run bot.py with this symbol configured first.\n"
        f"Existing tables: {existing if existing else 'none'}"
    ) from exc
finally:
    conn.close()

# 2. Procesar features
df['return_5'] = df['close'].pct_change(5)
df['SMA10'] = df['close'].rolling(10).mean()
# ... añade tus features

# 3. Etiquetado: sube >0.3% en próximos 10 minutos
df['target'] = (df['close'].shift(-10) / df['close'] > 1.003).astype(int)
df = df.dropna()

# 4. Split temporal
train = df.iloc[:int(len(df)*0.7)]
test = df.iloc[int(len(df)*0.7):]

# 5. Entrenar modelo
features = ['return_5', 'SMA10']  # añade todas las que calcules
clf = RandomForestClassifier(n_estimators=100)
clf.fit(train[features], train['target'])

# 6. Evaluar modelo
preds = clf.predict(test[features])
# ... calcula métricas de trading y precisión

# 7. Guardar modelo
model_path = f"rf_{SYMBOL.lower()}.pkl"
with open(model_path, "wb") as f:
    pickle.dump(clf, f)
print(f"Model saved to {model_path}")
