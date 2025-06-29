import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from pathlib import Path
import yaml
import pickle

# Load configuration
with open(Path(__file__).resolve().parent / 'config.yaml', 'r') as fh:
    CONFIG = yaml.safe_load(fh)

DB_PATH = CONFIG.get('database_path', 'binance_1m.db')
SYMBOL = (CONFIG.get('symbols') or ['BTCUSDT'])[0]


def load_data():
    """Read historical data for the configured symbol."""
    conn = sqlite3.connect(DB_PATH)
    table = f"_{SYMBOL}"
    df = pd.read_sql(f'SELECT * FROM {table}', conn)
    conn.close()
    return df


def optimize_model():
    """Run a simple grid search for a RandomForestClassifier."""
    df = load_data()

    # Basic feature engineering and labeling
    df['return_5'] = df['close'].pct_change(5)
    df['SMA10'] = df['close'].rolling(10).mean()
    df['target'] = (df['close'].shift(-10) / df['close'] > 1.003).astype(int)
    df = df.dropna()

    X = df[['return_5', 'SMA10']]
    y = df['target']

    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [None, 5, 10],
    }
    base_model = RandomForestClassifier(random_state=42)
    search = GridSearchCV(base_model, param_grid=param_grid, cv=3, n_jobs=-1)
    search.fit(X, y)

    print('Best params:', search.best_params_)
    return search.best_estimator_


if __name__ == '__main__':
    best_model = optimize_model()
    with open('rf_best.pkl', 'wb') as f:
        pickle.dump(best_model, f)
    print('Saved best model to rf_best.pkl')
