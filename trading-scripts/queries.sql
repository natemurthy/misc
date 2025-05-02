-- estimate of table size by row count
-- see https://stackoverflow.com/a/2611745
SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC;


-- get analyst price target history for a given symbol sorted by created_at (tipranks)
select trading_day, upside_potential, last_closing_price, mean, low, high, ratings_count
from timeseries.fcst_analyst_price_target
where symbol = upper('spy') and source = 'tipranks'
order by created_at desc


-- get analyst price target history for a given symbol sorted by created_at (yfinance)
select trading_day, upside_potential, last_closing_price, median, mean, low, high, pe_ttm, pe_fwd
from timeseries.fcst_analyst_price_target
where symbol = upper('nvda') and source = 'yfinance'
order by created_at desc


-- P/E ratio comarison
select symbol, pe_ttm, pe_fwd, upside_potential, last_closing_price, median
from timeseries.fcst_analyst_price_target
where
  source = 'yfinance'
  and trading_day = '2025-02-14'
  and symbol in ('NVDA', 'GOOGL')
order by pe_fwd asc


-- buy-side symbol screener (by upside_potential)
select t.source, t.symbol, t.upside_potential, m.last_sma, m.last_closing_price
from timeseries.hist_momentum_stat m
inner join timeseries.fcst_analyst_price_target t on t.trading_day = m.trading_day and t.symbol = m.symbol
where
  m.sma_period = '100d'
  and m.trading_day = '2024-10-15'
  and m.last_closing_price < m.last_sma
  and t.upside_potential > 1.3
order by t.upside_potential desc


-- symbol screener (by momentum_factor)
select t.source, t.symbol, m.momentum_factor, t.upside_potential, m.last_sma, m.last_closing_price
from timeseries.hist_momentum_stat m
inner join timeseries.fcst_analyst_price_target t on t.trading_day = m.trading_day and t.symbol = m.symbol
where
  m.sma_period = '200d'
  and m.trading_day = '2024-10-15'
  and m.last_closing_price < m.last_sma
  and t.upside_potential > 1.3
order by m.momentum_factor desc


-- sell-side symbol screener (by upside_potential)
select t.symbol, upside_potential, last_closing_price, median, mean
from timeseries.fcst_analyst_price_target t
inner join portfolio.holdings p on p.symbol = t.symbol
where
  t.trading_day = '2024-11-07'
  and source = 'tipranks'
  and upside_potential < 1.10
order by upside_potential asc


-- get analyst price targets
select symbol, upside_potential, median, mean, low, high
from timeseries.fcst_analyst_price_target
where trading_day = '2024-10-11'
order by upside_potential desc


-- get dividend yields
select symbol, rate, source
from timeseries.hist_dividend_yield
where trading_day = '2024-10-11'
order by rate desc


-- get moving averages
select symbol, momentum_factor, last_closing_price, last_sma
from timeseries.hist_momentum_stat
where trading_day = '2024-10-11' and sma_period = '200w'
order by momentum_factor desc


/* symbol groups */

-- Magnificent 7
symbol in ('AAPL','NVDA','MSFT','GOOGL','AMZN','META','TSLA')

-- Rotations in 6750 (NVO, TFX, XRAY are questionable hedges), still need to find Stoxx 600 ETF (DEBF, EWG, HEDJ?)
AFK, INDA, UTWO, FLOT, ILF, VGK, DBEF, EWG, EWJ, HEDJ, MCHI, GLD, EIX, CCI, NEE, MOH, NVO, DXCM, TFX, XRAY, VICI, O, PLD, MRK, ELV, OGN, ABBV, A, PPL, WELL, VST, CEG, WCC, PWR

-- Finance
symbol in ('BAC','BANC','BLK','C','CMA','DB','FHN','GS','JPM','KEY','KRE','MA','MS','UBS','V','WAL','WFC')

-- China stocks
symbol in ('BABA','BYDDY','BIDU','JD','LI','MCHI', 'NIO', 'NTES', 'PDD', 'XPEV')

-- Real Estate
symbol in ('MAA','O','PLD')

-- EVs, detroit car companies, and autonomous driving)
symbol in ('AUR','BYDDY','F','GM','GOEV','LAZR','LCID','LI','NIO','PSNY','RIVN','STLA','TSLA','VFS','XPEV')

-- Renewables and new energy technologies
symbol in ('BEP','ENPH','FAN','SEDG','TAN','NEE')

-- Energy storage
symbol in ('FLNC','STEM')

-- Electric power infra
symbol in ('CEG','EIX','NEE','PCG','PWR','SRE','VST','WCC','WEC')

-- Shipping
symbol in ('DAC','GSL')

-- Consumer goods
symbol in ('CHWY','CVNA','JMIA','NKE','MMM','WBA')

-- Chip hardware and software stocks
symbol in ('AMD','ASML','AVGO','INTC','NVDA','MU','SNPS','TSM','TXN')

-- Biotech and healthcare
symbol in ('A','ABBV','BIIB','DXCM','UNH')

-- Fintech
symbol in ('AFRM','ADYEY','GPN','LMND','PYPL','SQ','UPST')

-- Telecom
symbold in ('CMCSA','T','TMUS','VOD','VZ')

-- Other tech (big, medium, small cap)
symbol in ('ADBE','APLD','CORZ','CRWD','CRM','DASH','DOCU','IBM','LYFT','NFLX','PL','OKTA','ORCL','PTON','RKLB',
  'SHOP','SPOT','TWLO','UBER','ZM','ZS'
)

-- Mining
symbol in ('MP','PLL')

-- ETFs
symbol in ('AFK','AGGH','ARKK','ARKX','BITO','BUCK','CDX','CONY','COWZ','CTA','DIA','EQLS','ESGU','EWJ','FAN',
  'FFND','FLOT','GK','GLD','GOVT','HEQT','HIGH','ILF','INDA','IWM','JEPI','JETS','KOMP','KRE','MCHI','MJ',
  'PFF', 'QQQ','SPY','SVOL','TAN','TLT','VOO'
)

