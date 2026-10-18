import math
import re

import pytest

import price_options as po


# --- Black-Scholes --------------------------------------------------------------------------


def test_black_scholes_call_matches_textbook_value():
    # Hull-style reference: S=100, K=100, T=1y, r=5%, sigma=20% -> C = 10.4506
    assert po.black_scholes_call(100, 100, 1.0, 0.05, 0.2) == pytest.approx(
        10.4506, abs=1e-4
    )


def test_black_scholes_put_matches_textbook_value():
    assert po.black_scholes_put(100, 100, 1.0, 0.05, 0.2) == pytest.approx(
        5.5735, abs=1e-4
    )


@pytest.mark.parametrize(
    "S, K, T, r, sigma",
    [
        (100, 100, 1.0, 0.05, 0.2),
        (400, 480, 850 / 365, 0.04, 0.4),
        (566.76, 540, 47 / 365, 0.04, 0.4),
    ],
)
def test_put_call_parity(S, K, T, r, sigma):
    c = po.black_scholes_call(S, K, T, r, sigma)
    p = po.black_scholes_put(S, K, T, r, sigma)
    assert c - p == pytest.approx(S - K * math.exp(-r * T), abs=1e-9)


@pytest.mark.parametrize("T", [0, -0.5])
def test_expired_options_return_intrinsic_value(T):
    assert po.black_scholes_call(110, 100, T, 0.04, 0.4) == 10
    assert po.black_scholes_call(90, 100, T, 0.04, 0.4) == 0
    assert po.black_scholes_put(90, 100, T, 0.04, 0.4) == 10
    assert po.black_scholes_put(110, 100, T, 0.04, 0.4) == 0


def test_prices_respect_no_arbitrage_bounds():
    S, K, T, r, sigma = 100, 95, 0.5, 0.04, 0.3
    c = po.black_scholes_call(S, K, T, r, sigma)
    p = po.black_scholes_put(S, K, T, r, sigma)
    assert max(S - K * math.exp(-r * T), 0) <= c <= S
    assert max(K * math.exp(-r * T) - S, 0) <= p <= K * math.exp(-r * T)


def test_call_price_increases_with_volatility_and_put_decreases_with_spot():
    calls = [
        po.black_scholes_call(100, 100, 1, 0.04, sig) for sig in (0.1, 0.2, 0.4, 0.8)
    ]
    assert calls == sorted(calls)
    puts = [po.black_scholes_put(S, 100, 1, 0.04, 0.2) for S in (80, 90, 100, 110)]
    assert puts == sorted(puts, reverse=True)


def test_deep_in_the_money_call_approaches_forward_intrinsic():
    S, K, T, r = 1000, 100, 1, 0.05
    assert po.black_scholes_call(S, K, T, r, 0.2) == pytest.approx(
        S - K * math.exp(-r * T), rel=1e-9
    )


# --- scenario helpers -----------------------------------------------------------------------


def test_model_option_price_prints_scenario_with_module_parameters(capsys):
    po.model_option_price()

    out = capsys.readouterr().out
    expected = po.black_scholes_call(400, po.K, po.t_minus / 365.0, po.r, po.sigma)
    assert f"Strike: {po.K}" in out
    assert "Scenario: 400" in out
    assert f"Days until exp: {po.t_minus}, modeled price: {expected}" in out


def test_model_option_positions_reports_total_pnl_per_contract(capsys):
    positions = [po.pos(5, 470, 1.245), po.pos(47, 480, 12.27)]
    cur, change = 488.83, 0.99

    po.model_option_positions(positions, cur, change)

    out = capsys.readouterr().out
    scenario = cur * change
    assert f"from current price of {cur} to {scenario}" in out
    expected = (
        sum(
            po.black_scholes_put(scenario, p.k, p.t_minus / 365.0, po.r, po.sigma)
            - p.prev
            for p in positions
        )
        * 100
    )
    assert f"Total projected gain/loss: {expected:.2f}" in out
    for p in positions:
        modeled = po.black_scholes_put(scenario, p.k, p.t_minus / 365.0, po.r, po.sigma)
        assert f"{p.t_minus} \t {p.k} \t {p.prev} \t {modeled}" in out


def test_model_option_positions_with_no_positions_is_flat(capsys):
    po.model_option_positions([], 500.0, 1.0)
    assert "Total projected gain/loss: 0.00" in capsys.readouterr().out


def test_sample_position_lists_are_well_formed():
    for positions in (po.qqq_positions, po.spy_positions):
        assert len(positions) == 9
        assert all(p.t_minus > 0 and p.k > 0 and p.prev > 0 for p in positions)
        assert [p.t_minus for p in positions] == sorted(p.t_minus for p in positions)


# --- model_option_price_chain ---------------------------------------------------------------

CHAIN_HEADER = "Contract,Expiration,T-minus,Bid,Ask,Last Fill,Extrinsic,θ,δ,γ,ρ,v,ts"


def _write_chain(workdir, rows):
    (workdir / "alpaca").mkdir()
    (workdir / "alpaca" / "option_chain.csv").write_text(
        "\n".join([CHAIN_HEADER] + rows) + "\n"
    )


def test_model_option_price_chain_prices_puts_against_one_percent_drop(workdir, capsys):
    rows = [
        "QQQ250509P00470000,2025-05-09,3.3,1.33,1.39,1.44,1.44,-0.59,-0.17,0.01,-0.007,0.11,2025-05-06 15:18:29",
        "QQQ250516P00470000,2025-05-16,10.3,3.76,3.81,3.729,3.729,-0.35,-0.26,0.01,-0.036,0.26,2025-05-06 15:18:30",
    ]
    _write_chain(workdir, rows)
    t_minus, last_fill = [3.3, 10.3], [1.44, 3.729]
    scenario = 482.79 * 0.99
    modeled = [
        po.black_scholes_put(S=scenario, K=po.K, T=t / 365.0, r=po.r, sigma=po.sigma)
        for t in t_minus
    ]

    po.model_option_price_chain()

    out = capsys.readouterr().out
    assert "Running put ceiling price change scenario" in out
    assert f"Previous  position value: {sum(last_fill) * 100:.2f}" in out
    assert f"Projected position value: {sum(modeled) * 100:.2f}" in out
    assert (
        f"Total projected gain/loss: {sum(m - lf for m, lf in zip(modeled, last_fill)) * 100:.2f}"
        in out
    )
    assert "Modeled Multiplier" in out


def test_model_option_price_chain_call_contracts_are_not_modeled_yet(workdir, capsys):
    _write_chain(workdir, ["QQQ250509C00470000,2025-05-09,3.3,1,1,1,1,0,0,0,0,0,ts"])

    po.model_option_price_chain()

    out = capsys.readouterr().out
    assert "tbd" in out
    assert "Projected position value" not in out


def test_model_option_price_chain_ignores_unrecognised_contracts(workdir, capsys):
    _write_chain(workdir, ["XYZ,2025-05-09,3.3,1,1,1,1,0,0,0,0,0,ts"])

    po.model_option_price_chain()

    assert capsys.readouterr().out == ""


# --- solve_spot_price -----------------------------------------------------------------------


def test_solve_spot_price_finds_spot_where_put_doubles(capsys):
    po.solve_spot_price()

    out = capsys.readouterr().out
    m = re.search(r"SPY must fall to approximately \$(\d+\.\d+)", out)
    assert m, out
    spot = float(m.group(1))
    target = 2 * 12.79
    assert po.black_scholes_put(
        spot, po.K, po.t_minus / 365.0, po.r, po.sigma
    ) == pytest.approx(target, abs=0.05)
    assert f"SPY put: K={po.K} (expires in {po.t_minus} days), curr_price 12.79" in out


# --- main -----------------------------------------------------------------------------------


def test_main_runs_only_the_single_strike_scenario(monkeypatch, capsys):
    calls = []
    for name in (
        "model_option_price",
        "model_option_positions",
        "model_option_price_chain",
        "solve_spot_price",
    ):
        monkeypatch.setattr(po, name, lambda *a, _n=name, **k: calls.append(_n))

    po.main()

    assert calls == ["model_option_price"]
