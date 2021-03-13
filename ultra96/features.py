import numpy as np
import pandas as pd
from scipy.stats import entropy, pearsonr


def get_min(data):
    return np.min(data)


def get_max(data):
    return np.max(data)


def get_std(data):
    return np.std(data)


def get_mean(data):
    return np.mean(data)


def get_iqr(data):
    q75, q25 = np.percentile(data, [75, 25], axis=0)
    return q75 - q25


def get_skewness(data):
    return data.skew()


def get_kurtosis(data):
    return data.kurtosis()


# def get_entropy(data):
#     return pd.DataFrame(entropy(data))


def get_sma(data):
    x, y, z = [data[col] for col in data.columns]
    sma = 0
    for xi, yi, zi in zip(x, y, z):
        sma += abs(xi) + abs(yi) + abs(zi)
    return sma


def get_corr(data):
    x, y, z = [data[col] for col in data.columns]
    corrXY, _ = pearsonr(x, y)
    corrXZ, _ = pearsonr(x, z)
    corrYZ, _ = pearsonr(y, z)
    return corrXY, corrXZ, corrYZ


# def get_arr_coeff(data):
#     ar, _, _ = aryule