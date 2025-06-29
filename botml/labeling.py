def create_labels(df, horizon=5, threshold=0.002):
    """
    horizon: minutos a futuro para evaluar el target.
    threshold: cambio porcentual mínimo para considerar señal positiva.
    """
    future_price = df['close'].shift(-horizon)
    future_return = (future_price - df['close']) / df['close']
    df['label'] = (future_return > threshold).astype(int)
    df = df.dropna().reset_index(drop=True)
    return df

# Uso típico:
# df = add_features(df)
# df = create_labels(df, horizon=5, threshold=0.002)  # 0.2% en 5 min
