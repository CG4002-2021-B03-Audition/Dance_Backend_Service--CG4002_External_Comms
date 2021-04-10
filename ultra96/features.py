import numpy as np
import pandas as pd
from scipy.stats import pearsonr, skew, kurtosis, iqr
#from numba import njit


#@njit
def get_min(data):
    return [np.min(i) for i in data]

#@njit
def get_max(data):
    return [np.max(i) for i in data]

#@njit
def get_std(data):
    return [np.std(i) for i in data]

#@njit
def get_mean(data):
    return [np.mean(i) for i in data]

# @njit
# def get_trapz(data):
#     return [np.trapz(i) for i in data]


def get_iqr(data):
    return iqr(data, axis=1)


def get_skewness(data):
    return np.array(pd.DataFrame(data).skew(axis=1))


def get_kurtosis(data):
    return np.array(pd.DataFrame(data).kurtosis(axis=1))


# def get_entropy(data):
#     return pd.DataFrame(entropy(data))


def get_sma(data):
    x, y, z = data
    sma = 0
    for xi, yi, zi in zip(x, y, z):
        sma += abs(xi) + abs(yi) + abs(zi)
    return sma


def get_corr(data):
    x, y, z = data
    corrXY, _ = pearsonr(x, y)
    corrXZ, _ = pearsonr(x, z)
    corrYZ, _ = pearsonr(y, z)
    if any([np.isnan(corrXY), np.isnan(corrXZ), np.isnan(corrYZ)]):
        return 0,0,0
    return corrXY, corrXZ, corrYZ