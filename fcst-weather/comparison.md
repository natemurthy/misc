# Aurora 1.5 vs Chronos-2: hourly SSRD forecast comparison

**Date of analysis:** 2026-08-04 ~05:20 UTC · **Site:** San Leandro, CA (37.72, −122.16) · **Metric:** hourly-mean
SSRD in W/m² (`ssrd_w_m2`; Chronos values are the forecast median)

| Run | Init (UTC) | Forecast window (hour-ending, UTC) | Inputs |
|---|---|---|---|
| Aurora 1.5 | Aug 3 18:00 (latest published IFS cycle) | Aug 3 19:00 → Aug 4 18:00 | Real ECMWF open-data atmospheric state (first run with real initial conditions) |
| Chronos-2 | Aug 4 05:00 (current hour) | Aug 4 06:00 → Aug 5 05:00 | 30 days of Open-Meteo SSRD history at the site |

The two windows are offset because Aurora initializes from the newest *published* forecast cycle (~7–8 h behind
wall clock) while Chronos initializes from "now". That offset is what makes part 1 possible: Aurora's first 11
forecast hours have already happened, so they can be scored against recorded values.

## 1. Aurora vs recorded actuals (the only hours verifiable today)

Reference: Open-Meteo's recorded `shortwave_radiation` for Aug 3 19:00 → Aug 4 05:00 UTC.

| Valid (UTC) | Local (PDT) | Actual | Aurora | Error |
|---|---|---:|---:|---:|
| Aug 3 19:00 | 12pm | 900 | 853.3 | −46.7 |
| Aug 3 20:00 | 1pm | 973 | 929.7 | −43.3 |
| Aug 3 21:00 | 2pm | 989 | 944.2 | −44.8 |
| Aug 3 22:00 | 3pm | 944 | 909.4 | −34.6 |
| Aug 3 23:00 | 4pm | 836 | 807.4 | −28.6 |
| Aug 4 00:00 | 5pm | 685 | 658.1 | −26.9 |
| Aug 4 01:00 | 6pm | 488 | 452.8 | −35.2 |
| Aug 4 02:00 | 7pm | 255 | 251.9 | −3.1 |
| Aug 4 03:00 | 8pm | 49 | 67.0 | +18.0 |
| Aug 4 04:00 | 9pm | 0 | 5.5 | +5.5 |
| Aug 4 05:00 | 10pm | 0 | 4.7 | +4.7 |

**MAE 26.5 W/m² · RMSE 30.8 W/m² · daylight bias −27 W/m² (−4.0%) · peak-hour error −4.5%.**

Aurora, on real initial conditions, tracked an entire clear afternoon-to-night cycle at 1–11 h lead: correct peak
timing (21:00 UTC), correct sunset decay, near-zero night values. The errors are small and systematic (a mild ~4%
daytime low bias). Contrast with the mock-input run earlier today, which was off by 4–5× at midday and predicted
150+ W/m² in darkness — the initial conditions were the entire problem.

Chronos-2 cannot be scored on these hours: its current run starts at 06:00 UTC, and verifying any Chronos run
against Open-Meteo data is partly circular anyway — Open-Meteo SSRD *is* its input series (see caveats).

## 2. Head-to-head on the overlapping future hours (Aug 4 06:00–18:00 UTC)

Not yet verifiable — these hours haven't happened. Note the asymmetric handicap: Aurora is at 12–24 h lead here,
Chronos at 1–13 h.

| Valid (UTC) | Local (PDT) | Aurora | Chronos-2 (p10–p90) | Comment |
|---|---|---:|---:|---|
| 06:00–13:00 | 11pm–6am | 0.0–4.7 | 3.1–9.3 (p90 12–20) | Night: truth is 0. Aurora closer; Chronos keeps a small spurious floor |
| 14:00 | 7am | 11.5 | 23.3 (9–41) | First light |
| 15:00 | 8am | 109.5 | 156.7 (66–210) | Aurora below Chronos p10 |
| 16:00 | 9am | 253.8 | 349.1 (192–425) | Marine-layer window |
| 17:00 | 10am | 424.0 | 552.5 (355–638) | " |
| 18:00 | 11am | 602.0 | 735.6 (484–819) | Aurora ~18% lower |

The disagreement is concentrated in the morning ramp, where Aurora sits 45–130 W/m² below the Chronos median
(at/below its p10 at 15:00). Two readings: (a) Aurora sees the real Pacific state and is forecasting morning
marine-layer attenuation that Chronos's univariate history can't resolve; or (b) Aurora's verified ~4% low bias
plus its longer lead is simply muting the ramp. Yesterday's verified hours can't distinguish these — the ramp
hours verify after ~18:00 UTC today.

## 3. Verdict

**On the evidence available right now, Aurora (with real initial conditions) is the demonstrably more accurate
forecast: it is the only one with verifiable hours today, and it verified well — MAE 26.5 W/m², ~4% daytime low
bias, correct diurnal timing.** It is also the better of the two at night (true zeros; Chronos floors at 3–9 W/m²
because nothing constrains it to darkness).

That is not the same as declaring it the more *skillful* system overall: skill needs many verified forecasts, and
in the one window where the two directly disagree (this morning's ramp), Chronos has the lead-time advantage and
its 80% band sensibly widens across exactly the fog-risk hours. If the morning verifies clear and strong, Chronos's
higher ramp wins those hours; if the marine layer shows up, Aurora called a regime signal Chronos couldn't see.

**To settle it:** after ~19:00 UTC today, fetch Open-Meteo's recorded values for Aug 4 06:00–18:00 and score both
columns in part 2 (Aurora at 12–24 h lead, Chronos at 1–13 h lead — report lead-stratified errors, not one pooled
number).

## Caveats

- The "actuals" are Open-Meteo's model analysis for the grid point, not a pyranometer at the site.
- Chronos-2 consumes Open-Meteo SSRD as input, so verification against Open-Meteo data favors Chronos by
  construction (shared systematic errors cancel). Aurora's verification above has no such coupling — its ~4% low
  bias may partly be an Aurora-vs-Open-Meteo reference mismatch rather than true error.
- One day, one site, one run each: indicative, not a skill statistic.
- Aurora values are from the run logged 05:13 UTC (before the night-time clamp was added to the script); its
  13:00 UTC value −0.6 is shown as 0.0, which is what the current script would print.
