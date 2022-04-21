#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn.linear_model
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.api import qqplot
from scipy import stats
import collections

BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath('train')
TRAIN_DATA = TRAIN_DIR.joinpath('carbontax', 'IL').glob('Data_*.csv')


def detrend(df: pd.DataFrame) -> pd.Series:
    """
    Return a time-series signal detrending using Fourier analysis.

    @In: df, pd.DataFrame, a dataframe containing signal information.
    @Out: pd.Series, a detrended time-series vector
    """
    values = df.TOTALLOAD
    pivots = df.HOUR
    periods = [8760, 4380, 2190, 438, 168, 24, 12, 6]
    fourier = np.zeros((pivots.size, 2*len(periods)))
    for p, period in enumerate(periods):
        hist = 2.0 * (np.pi / period) * pivots
        fourier[:, 2 * p] = np.sin(hist)
        fourier[:, 2 * p + 1] = np.cos(hist)

    maskds = np.ones(len(values), dtype=bool)
    fe = sklearn.linear_model.LinearRegression(normalize=False)
    fs = fourier[masks, :]
    values = values[masks]
    cn = np.linalg.cond(fs)
    fe.fit(fs, values)
    intercept = fe.intercept_
    coeffs = fe.coef_
    wave_coef_map = collections.defaultdict(dict)
    for c, coef in enumerate(coeffs):
      period = periods[c//2]
      waveform = 'sin' if c % 2 == 0 else 'cos'
      wave_coef_map[period][waveform] = coef
    # convert to C*sin(ft + s)
    ## since we use fitting to ge..t A and B, the magnitudes can be deceiving.
    ## this conversion makes "C" a useful value to know the contribution from a period
    coef_map = {}
    signal=np.ones(len(pivots)) * intercept
    for period, coefs in wave_coef_map.items():
      A = coefs['sin']
      B = coefs['cos']
      s, C = (np.arctan2(B, A), A / np.cos(p))
      coef_map[period] = {'amplitude': C, 'phase': s}
      signal += C * np.sin(2.0 * np.pi * pivots / period + s)
    return signal


def mean_forecast_err(y, yhat):
    return y.sub(yhat).mean()


def main():
    df = pd.read_csv(next(TRAIN_DATA))
    df = df.assign(
        TIMESTAMP = pd.Timestamp(f'{pd.unique(df.YEAR)[0]}-01-01') + pd.to_timedelta(df.HOUR, unit="H")
    ).set_index('TIMESTAMP')
    # df = df.resample('W').sum()
    # df['TOTALLOAD'] = df.TOTALLOAD.apply(lambda x: np.log(x))
    df = df.assign(FTL=lambda x: detrend(x))[:-1]
    print(df)

    plt.plot(df.TOTALLOAD)
    plt.plot(df.TOTALLOAD - df.FTL)
    plt.show()

    # fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12,8))
    # sm.graphics.tsa.plot_acf(df.FTL.values.squeeze(), lags=40, ax=axes[0])
    # sm.graphics.tsa.plot_pacf(df.FTL, lags=40, ax=axes[1])

    model = ARIMA(df.FTL, order=(2, 0, 0))
    model_fit = model.fit()
    print(model_fit.params)

    # print(sm.stats.durbin_watson(model_fit.resid.values))
    # fig = plt.figure(figsize=(12,8))
    # ax = fig.add_subplot(111)
    # ax = model_fit.resid.plot(ax=ax)
    # plt.show()
    #
    # resid = model_fit.resid
    # print(stats.normaltest(resid))
    #
    # fig = plt.figure(figsize=(12,8))
    # ax = fig.add_subplot(111)
    # ax = qqplot(resid, line='q', ax=ax, fit=True)
    # plt.show()
    #
    # fig = plt.figure(figsize=(12,8))
    # ax1 = fig.add_subplot(211)
    # fig = sm.graphics.tsa.plot_acf(resid.values.squeeze(), lags=20, ax=ax1)
    # ax2 = fig.add_subplot(212)
    # fig = sm.graphics.tsa.plot_pacf(resid, lags=20, ax=ax2)
    # plt.show()
    #
    # r,q,p = sm.tsa.acf(resid.values.squeeze(), fft=True, qstat=True, nlags=20)
    # data = np.c_[range(1,21), r[1:], q, p]
    # table = pd.DataFrame(data, columns=['lag', "AC", "Q", "Prob(>Q)"])
    # print(table.set_index('lag'))

    predict_load = model_fit.predict(dynamic=True)
    print(predict_load)
    # df['PREDICT'] = predict_load
    #
    # fig = plt.figure(figsize=(12,8))
    # ax = fig.add_subplot(111)
    # ax.plot(df.FTL)
    # ax.plot(df.PREDICT)
    # plt.show()
    # print(mean_forecast_err(df.FTL, predict_load))


if __name__ == '__main__':
    main()
