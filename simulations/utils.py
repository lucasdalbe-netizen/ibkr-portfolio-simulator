import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

def load_historical(ticker):
    """Charge les données historiques d'un ticker depuis data/historical/"""
    path = os.path.join(DATA_DIR, 'historical', f'{ticker}_1y.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Pas de données pour {ticker} — lance d'abord le collector.")
    df = pd.read_csv(path)
    col = 'date' if 'date' in df.columns else 'Date'
    df[col] = pd.to_datetime(df[col])
    df.set_index(col, inplace=True)
    cols_map = {c.lower(): c for c in df.columns}
    df = df[[cols_map.get('open'), cols_map.get('high'), cols_map.get('low'), cols_map.get('close'), cols_map.get('volume')]].copy()    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df['return'] = df['close'].pct_change()  # ← ajout
    return df

def load_snapshot(ticker):
    """Charge le dernier snapshot temps réel d'un ticker depuis data/realtime/"""
    import json
    path = os.path.join(DATA_DIR, 'realtime', f'{ticker}_latest.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Pas de snapshot pour {ticker} — lance d'abord le collector.")
    with open(path, 'r') as f:
        return json.load(f)

def load_multiple_historical(tickers):
    """Charge les closes de plusieurs tickers dans un seul DataFrame"""
    closes = {}
    for ticker in tickers:
        try:
            df = load_historical(ticker)
            closes[ticker] = df['close']
        except FileNotFoundError as e:
            print(f"Warning: {e}")
    return pd.DataFrame(closes).dropna()

def compute_returns(df_close):
    """Calcule les rendements log journaliers"""
    import numpy as np
    return np.log(df_close / df_close.shift(1)).dropna()
