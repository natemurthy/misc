import pandas as pd
import yfinance as yf


def get_bench_data() -> pd.DataFrame:
    symbols=['SPY','QQQ','TSLA']
    start='2024-01-01'
    end='2025-01-01'
    df = yf.download(symbols, start=start, end=end)['Close'].resample('D').ffill()
    df.index = df.index.tz_localize(None)

    for s in symbols:
        for i in range(len(df)):
            df.at[df.index[i], f"diff_{s}"] = (df[s].iloc[i] - df[s].iloc[0]) / df[s].iloc[0] * 100
    return df


def get_nate_data() -> pd.DataFrame:
    df = pd.read_csv('/Users/nathan/Downloads/2024_invest_perf_nate.csv')
    df['Total Value'] = df['Total Value'].str.replace(r'[^\d.]', '', regex=True)
    df['Total Value'] = pd.to_numeric(df['Total Value'])
    df['Invested Capital'] = df['Invested Capital'].str.replace(r'[^\d.]', '', regex=True)
    df['Invested Capital'] = pd.to_numeric(df['Invested Capital'])
    df['Invested Capital'] = df['Invested Capital'] - df['Invested Capital'].iloc[0]
    df['Date (EOD)'] = pd.to_datetime(df['Date (EOD)'])
    df = df.set_index('Date (EOD)')
    df_slim = df[['Total Value', 'Invested Capital']].copy()
    df_slim.fillna(0, inplace=True)

    for i in range(len(df_slim)):
        df_slim.at[df_slim.index[i], 'diff'] = (df['Total Value'].iloc[i] - df['Invested Capital'].iloc[i] \
            - df['Total Value'].iloc[0]) / df['Total Value'].iloc[0] * 100

    return df_slim


def export_diffs(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    perf = pd.concat([df1, df2], axis=1)
    perf.drop('SPY', axis=1, inplace=True)
    perf.drop('QQQ', axis=1, inplace=True)
    perf.drop('TSLA', axis=1, inplace=True)
    perf.drop('Total Value', axis=1, inplace=True)
    perf.drop('Invested Capital', axis=1, inplace=True)
    perf = perf.rename(columns={"diff_SPY": "SPY", "diff_QQQ": "QQQ", "diff_TSLA": "TSLA", "diff": "Nate"})
    perf.to_csv('2024_invest_perf.csv', index=True)
    return perf


def main():
    df_bench = get_bench_data()
    df_nate = get_nate_data()
    perf = export_diffs(df_bench, df_nate)
    print(perf.tail())


if __name__ == "__main__":
    main()

