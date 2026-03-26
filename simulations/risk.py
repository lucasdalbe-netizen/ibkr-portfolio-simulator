import numpy as np
import pandas as pd
from simulations.utils import load_historical, load_multiple_historical, compute_returns

def compute_var_es(tickers, confidence=0.95, n_simulations=100000, weights=None):
    """
    Calcule la VaR et l'Expected Shortfall pour un portfolio
    weights : dict {ticker: poids} — si None, poids égaux
    """
    closes = load_multiple_historical(tickers)
    returns = compute_returns(closes)

    # Poids égaux si non spécifiés
    if weights is None:
        w = np.array([1/len(tickers)] * len(tickers))
    else:
        w = np.array([weights[t] for t in tickers])

    # Rendements journaliers du portfolio
    port_returns = returns.values @ w

    mu = port_returns.mean()
    vol = port_returns.std()
    alpha = 1 - confidence

    # VaR Historique
    VaR_historical = -np.quantile(port_returns, alpha).round(4)

    # VaR Monte Carlo
    mc_returns = mu + vol * np.random.normal(0, 1, n_simulations)
    VaR_mc = -np.quantile(mc_returns, alpha).round(4)
    VaR_mc_10d = round(VaR_mc * np.sqrt(10), 4)
    VaR_mc_1y = round(VaR_mc * np.sqrt(252), 4)

    # Expected Shortfall
    ES_historical = -port_returns[port_returns < -VaR_historical].mean().round(4)
    ES_mc = -mc_returns[mc_returns < -VaR_mc].mean().round(4)

    return {
        "confidence": confidence,
        "VaR": {
            "historical_1d": VaR_historical,
            "mc_1d": VaR_mc,
            "mc_10d": VaR_mc_10d,
            "mc_1y": VaR_mc_1y,
        },
        "ES": {
            "historical": ES_historical,
            "mc": ES_mc,
        }
    }

def stress_test(tickers, weights=None):
    """
    Stress tests historiques sur le portfolio
    """
    closes = load_multiple_historical(tickers)
    returns = compute_returns(closes)

    if weights is None:
        w = np.array([1/len(tickers)] * len(tickers))
    else:
        w = np.array([weights[t] for t in tickers])

    port_returns = returns.values @ w

    # Pire jour historique
    worst_day = port_returns.min().round(4)
    worst_day_date = returns.index[port_returns.argmin()].strftime('%Y-%m-%d')

    # 5 pires jours cumulés
    worst_5 = pd.Series(port_returns).nsmallest(5)
    cumulative_loss = round(np.exp(worst_5.sum()) - 1, 4)

    # Drawdown maximum
    cumulative = np.exp(np.cumsum(port_returns))
    rolling_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - rolling_max) / rolling_max
    max_drawdown = round(drawdowns.min(), 4)

    return {
        "worst_day": {
            "return": worst_day,
            "date": worst_day_date,
        },
        "worst_5_days_cumulative": cumulative_loss,
        "max_drawdown": max_drawdown,
    }

def stress_test_shocks(tickers, weights=None, vol_shock=0.2, return_shock=0.15,
                        jump_size=-0.1, jump_prob=0.05,
                        confidence=0.95, n_simulations=100000):
    """
    Stress tests par chocs sur vol, return et jump
    """
    closes = load_multiple_historical(tickers)
    returns = compute_returns(closes)

    if weights is None:
        w = np.array([1/len(tickers)] * len(tickers))
    else:
        w = np.array([weights[t] for t in tickers])

    port_returns = returns.values @ w
    mu = port_returns.mean()
    vol = port_returns.std()
    alpha = 1 - confidence

    # Choc sur la volatilité
    vol_stressed = vol * (1 + vol_shock)
    mc_vol = mu + vol_stressed * np.random.normal(0, 1, n_simulations)
    VaR_vol_shock = -np.quantile(mc_vol, alpha).round(4)

    # Choc sur le rendement
    mu_stressed = mu * (1 + return_shock)
    mc_return = mu_stressed + vol * np.random.normal(0, 1, n_simulations)
    VaR_return_shock = -np.quantile(mc_return, alpha).round(4)

    # Choc jump
    jumps = np.random.binomial(1, jump_prob, n_simulations) * jump_size
    mc_jump = mu + vol * np.random.normal(0, 1, n_simulations) + jumps
    VaR_jump = -np.quantile(mc_jump, alpha).round(4)

    return {
        "vol_shock": {
            "shock_applied": vol_shock,
            "VaR_1d": VaR_vol_shock,
        },
        "return_shock": {
            "shock_applied": return_shock,
            "VaR_1d": VaR_return_shock,
        },
        "jump_shock": {
            "jump_size": jump_size,
            "jump_prob": jump_prob,
            "VaR_1d": VaR_jump,
        }
    }

def analyze(tickers, weights=None, confidence=0.95, n_simulations=100000,
            vol_shock=0.2, return_shock=0.15, jump_size=-0.1, jump_prob=0.05):
    """
    Analyse complète du risque — retourne tout en un seul dict JSON
    """
    var_es = compute_var_es(tickers, confidence, n_simulations, weights)
    stress = stress_test(tickers, weights)
    shocks = stress_test_shocks(tickers, weights, vol_shock, return_shock,
                                 jump_size, jump_prob, confidence, n_simulations)
    return {
        "tickers": tickers,
        "weights": weights,
        "var_es": var_es,
        "stress_test": stress,
        "shocks": shocks,
    }

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
    result = analyze(tickers)
    print("VaR :", result['var_es']['VaR'])
    print("ES :", result['var_es']['ES'])
    print("Stress :", result['stress_test'])
    print("Shocks :", result['shocks'])