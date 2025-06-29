# train_model.py
import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
import pickle

# 1. Cargar datos históricos
conn = sqlite3.connect('binance_1m.db')
df = pd.read_sql('SELECT * FROM _BTCUSDT', conn)
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
with open('rf_btcusdt.pkl', 'wb') as f:
    pickle.dump(clf, f)
