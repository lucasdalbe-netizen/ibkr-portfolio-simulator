from ib_insync import IB, Stock, util
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", 4002))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", 1))

def connect_gateway():
    ib = IB()
    ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
    ib.reqMarketDataType(3)  # 3 = données différées (paper trading)
    print(f"Connecté à IB Gateway ({IB_HOST}:{IB_PORT})")
    return ib

def get_snapshot(ib, ticker, exchange="SMART", currency="USD"):
    contract = Stock(ticker, exchange, currency)
    ib.qualifyContracts(contract)
    ticker_data = ib.reqMktData(contract, "", True, False)
    ib.sleep(2)  # attendre la réponse

    snapshot = {
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
        "last": ticker_data.last,
        "bid": ticker_data.bid,
        "ask": ticker_data.ask,
        "high": ticker_data.high,
        "low": ticker_data.low,
        "volume": ticker_data.volume,
        "close": ticker_data.close,
    }
    return snapshot

def get_historical(ib, ticker, duration="1 Y", bar_size="1 day", exchange="SMART", currency="USD"):
    contract = Stock(ticker, exchange, currency)
    ib.qualifyContracts(contract)
    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow="MIDPOINT",
        useRTH=True
    )
    df = util.df(bars)
    return df

def save_snapshot_locally(snapshot, output_dir="data/realtime"):
    os.makedirs(output_dir, exist_ok=True)
    ticker = snapshot["ticker"]
    path = os.path.join(output_dir, f"{ticker}_latest.json")
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Snapshot sauvegardé : {path}")

def save_historical_locally(df, ticker, output_dir="data/historical"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{ticker}_1y.csv")
    df.to_csv(path, index=False)
    print(f"Historique sauvegardé : {path}")

if __name__ == "__main__":
    TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA", "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "NFLX", "ADBE", "CRM"]

    ib = connect_gateway()

    for ticker in TICKERS:
        print(f"Collecte {ticker}...")

        # Snapshot temps réel
        snapshot = get_snapshot(ib, ticker)
        save_snapshot_locally(snapshot)

        # Données historiques
        df = get_historical(ib, ticker)
        save_historical_locally(df, ticker)

    ib.disconnect()
    print("Déconnecté. Collecte terminée.")
