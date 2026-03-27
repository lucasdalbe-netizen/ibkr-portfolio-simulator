import numpy as np
import pandas as pd
from simulations.utils import load_multiple_historical, compute_returns

def build_returns(tickers):
    """Charge les closes et calcule les rendements annualisés + matrice de covariance"""
    closes = load_multiple_historical(tickers)
    returns = compute_returns(closes)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    return returns, mean_returns, cov_matrix

def generate_weights(n_simulations, n_assets):
    """Génère des poids aléatoires dont la somme = 1"""
    w = np.random.random((n_simulations, n_assets))
    w /= w.sum(axis=1, keepdims=True)
    return w

def portfolio_stats(weights, mean_returns, cov_matrix, risk_free_rate=0.02):
    """Calcule return, volatilité et Sharpe pour chaque portfolio simulé"""
    port_returns = weights @ mean_returns.values
    port_vols = np.array([
        np.sqrt(w @ cov_matrix.values @ w) for w in weights
    ])
    sharpe = (port_returns - risk_free_rate) / port_vols
    return port_returns, port_vols, sharpe

def efficient_frontier(port_returns, port_vols, n_bins=30):
    """Calcule la frontière efficiente — meilleur return pour chaque niveau de vol"""
    results = pd.DataFrame({
        'return': port_returns,
        'volatility': port_vols,
    })
    results['vol_bin'] = pd.cut(results['volatility'], bins=n_bins)
    frontier = (
        results.groupby('vol_bin', observed=True)
        .apply(lambda g: g.loc[g['return'].idxmax()])
        .reset_index(drop=True)
        .sort_values('volatility')
    )
    return frontier

def optimize(tickers, n_simulations=500000, risk_free_rate=0.02):
    """
    Lance la simulation complète et retourne tous les résultats
    Retourne un dict prêt à être sérialisé en JSON pour le site
    """
    returns, mean_returns, cov_matrix = build_returns(tickers)
    weights = generate_weights(n_simulations, len(tickers))
    port_returns, port_vols, sharpe = portfolio_stats(weights, mean_returns, cov_matrix, risk_free_rate)

    results_df = pd.DataFrame({
        'return': port_returns,
        'volatility': port_vols,
        'sharpe': sharpe,
        'weights': [np.round(w, 4).tolist() for w in weights]
    })

    # Meilleur Sharpe
    best_sharpe_idx = results_df['sharpe'].idxmax()
    best_sharpe = results_df.loc[best_sharpe_idx]

    # Minimum volatilité
    min_vol_idx = results_df['volatility'].idxmin()
    min_vol = results_df.loc[min_vol_idx]

    # Frontière efficiente
    frontier = efficient_frontier(port_returns, port_vols)

    return {
        "tickers": tickers,
        "n_simulations": n_simulations,
        "portfolios": results_df[['return', 'volatility', 'sharpe']].round(4).to_dict(orient='records'),
        "best_sharpe": {
            "weights": dict(zip(tickers, best_sharpe['weights'])),
            "return": round(best_sharpe['return'], 4),
            "volatility": round(best_sharpe['volatility'], 4),
            "sharpe": round(best_sharpe['sharpe'], 4),
        },
        "min_vol": {
            "weights": dict(zip(tickers, min_vol['weights'])),
            "return": round(min_vol['return'], 4),
            "volatility": round(min_vol['volatility'], 4),
            "sharpe": round(min_vol['sharpe'], 4),
        },
        "frontier": frontier[['return', 'volatility']].round(4).to_dict(orient='records'),
        "individual_returns": mean_returns.round(4).to_dict(),
        "correlation_matrix": returns.corr().round(4).to_dict(),
    }

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
    result = optimize(tickers)
    print("Meilleur Sharpe :")
    print(result['best_sharpe'])
    print("\nMin Volatilité :")
    print(result['min_vol'])
