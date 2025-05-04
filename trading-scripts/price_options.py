import numpy as np
import scipy.stats as si

from scipy.optimize import fsolve

"""
These Black-Scholes functions are for European options. Note that American options
may be exercised before expiration and may require PDE and ODE solvers.
"""

def black_scholes_call(S, K, T, r, sigma):
    """Calculate the Black-Scholes price for a European call option.

    Args:
        S (float): Current price of the underlying asset.
        K (float): Strike price of the option.
        T (float): Time to expiration in years (e.g., 30 days = 30/365).
        r (float): Annual risk-free interest rate (as a decimal, e.g., 0.04 for 4%).
        sigma (float): Implied volatility of the underlying asset (as a decimal).

    Returns:
        float: Theoretical price of the European call option.
    """
    if T <= 0:
        return max(S - K, 0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    call_price = (S * si.norm.cdf(d1)) - (K * np.exp(-r * T) * si.norm.cdf(d2))
    return call_price


def black_scholes_put(S, K, T, r, sigma):
    """Calculate the Black-Scholes price for a European put option.

    Args:
        S (float): Current price of the underlying asset.
        K (float): Strike price of the option.
        T (float): Time to expiration in years (e.g., 30 days = 30/365).
        r (float): Annual risk-free interest rate (as a decimal, e.g., 0.04 for 4%).
        sigma (float): Implied volatility of the underlying asset (as a decimal).

    Returns:
        float: Theoretical price of the European put option.
    """
    if T <= 0:
        return max(K - S, 0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    put_price = (K * np.exp(-r * T) * si.norm.cdf(-d2)) - (S * si.norm.cdf(-d1))
    return put_price


# Given values
K = 500
t_minus = 33
T = t_minus/365.0  # fraction of days over a year remaining until expiration
r = 0.04           # updated risk-free rate (4%)
sigma = 0.2312     # 0.2312 (for SPY) as of 2 May 2025


# Calculate future options price
def model_option_price():
    scenario_underlying_price = 510
    p = black_scholes_put(scenario_underlying_price, K, T, r, sigma)
    print(f"Strike: {K}")
    print(f"Scenario: {scenario_underlying_price}")
    print(f"Days until exp: {t_minus}, modeled price: {p}")


# Solve by how much SPY would need to drop to each gain of multiplier `m`
def solve_spot_price():
    m = 2
    curr_price = 12.79
    target_price = m * curr_price

    # Function to solve for SPY spot price
    def equation(S):
        return black_scholes_put(S, K, T, r, sigma) - target_price

    # Initial guess for underlyig target price
    initial_guess = 500
    solution = fsolve(equation, initial_guess)

    print(f"SPY put: K={K} (expires in {round(T*365)} days), curr_price {curr_price}")
    print(f"{m}x price target: SPY must fall to approximately ${solution[0]:.2f}")


def main():
    model_option_price()
    #solve_spot_price()

if __name__ == "__main__":
    main()

