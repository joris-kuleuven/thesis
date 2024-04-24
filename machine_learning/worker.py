from statsmodels.stats.outliers_influence import variance_inflation_factor
# This is in a separate file because of the way Jupyter notebooks handle multiprocessing
def worker(args):
    X, i = args
    return variance_inflation_factor(X.values, i)