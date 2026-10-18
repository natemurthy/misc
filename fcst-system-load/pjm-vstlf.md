# PJM’s Very Short-Term Load Forecast (VSTLF) 

PJM’s Very Short-Term Load Forecast (VSTLF) methodology is a rolling, 5-minute interval forecast covering the next 6
hours. It is primarily implemented to drive PJM's Security Constrained Economic Dispatch (SCED) tool, enabling
real-time grid operators to balance moment-to-moment supply and demand.

See "Load Forecasting Supports Reliability and Efficiency" and "PJM Introduction and Load Forecasting Overview" in
references below.


## Methodology and implementation research

The implementation methodology relies on three main components to continuously predict loads:

1. **Time-Series Models & Machine Learning:** PJM utilizes advanced time-series modeling, incorporating machine
   learning technology for short-term predictions. The models project load profiles across 25 specific PJM areas
   and zones. See "Five Minute Load Forecast - Data Miner 2".

2. **Real-Time Telemetry & Lagged Data:** The VSTLF ingests constant feeds of real-time telemetered load data from
   regional Power Meters to capture immediate system load trends and recent historical deviations. See "PJM Manual 19",
   "XGBoost-Based Very Short-Term Load Forecasting Using Day-Ahead Load Forecasting Results", and "Load Forecasting
   Supports Reliability and Efficiency".

3. **Weather Adjustments:** Real-time variables such as temperature, humidity, and cloud cover are factored into the
   model to adjust for immediate, weather-sensitive spikes (e.g., cooling and heating loads). See "2026 PJM Load
   Forecast Report", "One Step Ahead Energy Load Forecasting: A Multi-model approach utilizing Machine and Deep
   Learning", "PredXGBR: A Machine Learning Framework for Short-Term Electrical Load Prediction", and "Load Forecasting
   Supports Reliability and Efficiency".

Updates are generated and published continuously throughout the operating day. System-to-system access to these 5 
minute predictions is available directly to market participants via the PJM Data Miner 2 API (also see "LMP Supports
Competitive Wholesale Power Markets".


---
## References

### Primary sources from  PJM

"Load Forecasting Supports Reliability and Efficiency"
https://www.pjm.com/-/media/DotCom/about-pjm/newsroom/fact-sheets/load-forecasting-supports-reliability-and-efficiency.ashx

"LMP Supports Competitive Wholesale Power Markets"
https://www.pjm.com/-/media/DotCom/about-pjm/newsroom/fact-sheets/lmp-supports-competitive-wholesale-power-markets.ashx

"2026 PJM Load Forecast Report"
https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report.pdf

"PJM Manual 19"
https://www.pjm.com/-/media/DotCom/documents/manuals/archive/m19/m19v35-load-forecasting-and-analysis-12-31-2021.pdf

"Five Minute Load Forecast - Data Miner 2"
https://dataminer2.pjm.com/feed/very_short_load_frcst/definition

"PJM Introduction and Load Forecasting Overview"
https://icc.illinois.gov/api/web-management/documents/downloads/public/future-of-gas/PJM%20Interconnection%20Presentation_ICC%20Future%20of%20Gas%20Workshop_5-20-2024.pdf


### Research papers

"Enhanced very short-term load forecasting with multi-lag feature engineering and prophet-XGBoost-CatBoost architecture"
https://www.sciencedirect.com/science/article/pii/S0360544225036230
30 Oct 2025

"XGBoost-Based Very Short-Term Load Forecasting Using Day-Ahead Load Forecasting Results"
https://www.mdpi.com/2079-9292/14/18/3747
22 Sept 2025

"PredXGBR: A Machine Learning Framework for Short-Term Electrical Load Prediction"
https://www.mdpi.com/2079-9292/13/22/4521
18 Nov 2024

"One Step Ahead Energy Load Forecasting: A Multi-model approach utilizing Machine and Deep Learning"
https://ieeexplore.ieee.org/document/9917790/
18 Oct 2022


### Related

WattCarbon releases "Local grid forecasts" feature to its GridSolver product. Every substation in the U.S. now has a
7-day load forecast
https://www.linkedin.com/posts/mcgeeyoung_apparently-its-really-hot-on-the-east-coast-activity-7478094582656716801-nkro
1 July 2026

