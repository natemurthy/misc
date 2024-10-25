create databsae "market-data";
create use "nathan" with encrypted password 'password';
grant all privileges on database "market-data" to "nathan";

create schema timeseries;
create schema portfolio;

create table portfolio.holdings (
  id     SERIAL PRIMARY KEY not null, 
  symbol varchar(8) not null
);

create table timeseries.fcst_analyst_price_target (
  id                  SERIAL        PRIMARY KEY not null,
  created_at          TIMESTAMPTZ   not null DEFAULT now(),
  source              varchar(255)  not null,
  symbol              varchar(8)    not null,
  trading_day         date          not null,
  last_closing_price  decimal       not null,
  forecast_date       date          not null, -- 12-months into future
  upside_potential    decimal       not null,
  low                 decimal       not null,
  high                decimal       not null,
  mean                decimal       not null,
  median              decimal
);

create table timeseries.hist_dividend_yield (
  id                  SERIAL        PRIMARY KEY not null,
  created_at          TIMESTAMPTZ   not null default now(),
  source              varchar(255)  not null,
  symbol              varchar(8)    not null,
  trading_day         date          not null,
  last_closing_price  decimal       not null,
  rate                decimal       not null
);

create table timeseries.hist_momentum_stat (
  id                      SERIAL       PRIMARY KEY not null,
  created_at              TIMESTAMPTZ  not null default now(),
  source                  varchar(255) not null,
  symbol                  varchar(8)   not null,
  trading_day             date         not null,
  last_closing_price      decimal      not null,
  sma_period              varchar(8)   not null,
  last_adj_close          decimal      not null,
  time_frame_low          decimal      not null,
  curr_distance_from_low  decimal      not null,
  last_sma                decimal      not null,
  momentum_factor         decimal      not null
);

create table timeseries.hist_free_cash_flow (
  id               SERIAL PRIMARY KEY not null,
  created_at       TIMESTAMPTZ        not null default now(),
  symbol           varchar(8)         not null,
  release_date     date               not null,
  ycharts_raw_fcf  varchar(16)        not null,
  fcf_usd          bigint             not null
);

alter table timeseries.fcst_analyst_price_target add column ratings_count int;
alter table timeseries.hist_momentum_stat add column rsi decimal;
alter table timeseries.hist_momentum_stat rename column rsi to last_rsi;


truncate table portfolio.holdings RESTART IDENTITY;
truncate table timeseries.fcst_analyst_price_target RESTART IDENTITY;
truncate table timeseries.hist_dividend_yield       RESTART IDENTITY;
truncate table timeseries.hist_momentum_stat        RESTART IDENTITY;
truncate table timeseries.hist_free_cash_flow       RESTART IDENTITY;

drop table portfolio.holdings;
drop table timeseries.fcst_analyst_price_target;
drop table timeseries.hist_dividend_yield;
drop table timeseries.hist_momentum_stat;
drop table timeseries.hist_free_cash_flow;

