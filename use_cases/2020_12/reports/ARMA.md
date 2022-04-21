# ARMA

An AutoRegressiveMovingAverage (ARMA) model was used to train the synthetic power histories

\begin{align}
x_t = \Sigma_{i=1}^{p} \phi_{i}x_{t-i} + \alpha_{t} + \Sigma_{j=1}^{q} \theta_{j}\alpha_{t-j},
\end{align}

where x is a vector of dimension $n$, and $\phi_{i}$ and $\theta_{j}$ are both $n$
by $n$ matrices. When $q=0$, the above is an autoregressive (AR) model of order
$p$; when $p=0$, the above is a moving average model of order $q$.

Before training the ARMA, a Fourier series is used to detrend the time series.

\begin{align}
x_t = y_t - \Sigma_{m} \left{a_{m}\sin\left(2 \pi f_{m} t\right) + b_{m}\cos\left(2\pi f_{m} t\right)\right},
\end{align}

where $1/f_{m}$ is defined as the basis points to detrend on.

## Default

## Default LNHR

## Carbon-Tax

## Carbon-Tax LNHR

## RPS

## RPS LNHR
