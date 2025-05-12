import numpy as np
import pandas as pd
import scipy.stats as si

from dataclasses import dataclass
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
K = 490
t_minus = 5        # 956 days til 17 Dec 2017 (as of 4 May 2024)
r = 0.04           # updated risk-free rate (4%)
sigma = 0.2780     # QQQ as of 6 May 2025


# Calculate future options price
def model_option_price():
    scenario_underlying_price = 700
    T = t_minus/365.0  # fraction of days over a year remaining until expiration
    p = black_scholes_put(scenario_underlying_price, K, T, r, sigma)
    print(f"Strike: {K}")
    print(f"Scenario: {scenario_underlying_price}")
    print(f"Days until exp: {t_minus}, modeled price: {p}")


@dataclass
class pos:
    t_minus: float  # days left to expiration
    k: float        # strike price
    prev: float     # last filled price


qqq_positions = [
    pos( 5, 470, 1.245),
    pos(12, 470, 3.155),
    pos(19, 460, 3.105),
    pos(26, 475, 7.18),
    pos(33, 460, 5.395),
    pos(40, 420, 2.065),
    pos(47, 420, 2.53),
    pos(47, 460, 7.30),
    pos(47, 480, 12.27),
]

spy_positions = [
    pos( 5, 550, 1.605),
    pos(12, 552, 3.87),
    pos(19, 540, 3.44),
    pos(26, 554, 7.235),
    pos(33, 540, 5.68),
    pos(40, 500, 2.275),
    pos(47, 500, 2.87),
    pos(47, 540, 7.895),
    pos(47, 560, 12.79),
]

def model_option_positions(positions, underlyig_cur_price, change):
    print("\nRunning put ceiling price change scenario")
    cur_price = underlyig_cur_price
    scenario_underlying_price = cur_price * change
    print(f"Scenario: underlying asset moves from current price of {cur_price} to {scenario_underlying_price}\n")
    results = []
    for p in positions:
        modeled_price = black_scholes_put(scenario_underlying_price, p.k, p.t_minus/365.0, r, sigma)
        results.append(modeled_price-p.prev)
        print(f"{p.t_minus} \t {p.k} \t {p.prev} \t {modeled_price}")
    gain_loss = sum(results)*100
    print(f"\nTotal projected gain/loss: {gain_loss:.2f}")


def model_option_price_chain():
    df = pd.read_csv("alpaca/option_chain.csv")

    result = df[["Contract", "Expiration", "T-minus", "Last Fill"]]
    is_call = "C0" in str(result["Contract"].iloc[0])  # type: ignore
    is_put = "P0" in str(result["Contract"].iloc[0])  # type: ignore

    if is_call:
        print("\nRunning put ceiling price change scenario")
        print("tbd")
        
    if is_put:
        print("\nRunning put ceiling price change scenario")
        cur_price = 482.79
        scenario_underlying_price = cur_price * 0.99
        print(f"Scenario: underlying asset moves from current price of {cur_price} to {scenario_underlying_price}\n")

        result = result.copy()
        result.loc[:, "Modeled Price"] = result["T-minus"].apply(  # type: ignore
            lambda t_minus: black_scholes_put(S=scenario_underlying_price, K=K, T=t_minus/365.0, r=r, sigma=sigma),
        )
        result.loc[:, "Modeled Multiplier"] = result["Modeled Price"] / result["Last Fill"]
        result.loc[:, "Modeled Gain/Loss"] = (result["Modeled Price"] - result["Last Fill"])*100
        print(result)
        prev = result["Last Fill"].sum()*100
        next = result["Modeled Price"].sum()*100
        gain_loss = result["Modeled Gain/Loss"].sum()
        print()
        print(f"Previous  position value: {prev:.2f}")
        print(f"Projected position value: {next:.2f}")
        print(f"Total projected gain/loss: {gain_loss:.2f}")
    

# Solve by how much SPY would need to drop to each gain of multiplier `m`
def solve_spot_price():
    m = 2
    curr_price = 12.79
    target_price = m * curr_price
    T = t_minus/365.0

    # Function to solve for SPY spot price
    def equation(S):
        return black_scholes_put(S, K, T, r, sigma) - target_price

    # Initial guess for underlyig target price
    initial_guess = 500
    solution = fsolve(equation, initial_guess)

    print(f"SPY put: K={K} (expires in {round(T*365)} days), curr_price {curr_price}")
    print(f"{m}x price target: SPY must fall to approximately ${solution[0]:.2f}")


def main():
    #model_option_price()
    #model_option_positions(spy_positions, 566.76, 0.99)
    #model_option_positions(qqq_positions, 488.83, 0.99)
    model_option_price_chain()
    #solve_spot_price()

if __name__ == "__main__":
    main()

