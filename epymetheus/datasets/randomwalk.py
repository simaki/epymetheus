import pandas as pd

from epymetheus import Universe
from epymetheus.stochastic import generate_geometric_brownian


def make_randomwalk(
    n_bars=1000,
    n_assets=10,
    volatility=0.01,
    init_value=1.0,
    dt=1.0,
    drift=0.0,
    name="RandomWalk",
    bars=None,
    assets=None,
    seed=None,
):
    """
    Return Universe whose prices are random-walks.
    Daily returns follow log-normal distribution.

    Parameters
    ----------
    - n_bars : int, default 1000
    - n_assets : int, default 10
    - volatility : float, default 0.01
    - name : str, default='RandomWalk'
    - bars
    - assets
    - seed : int

    Returns
    -------
    Universe

    Examples
    --------
    >>> import numpy as np
    >>> np.random.seed(42)
    >>> make_randomwalk(10, 3).prices
              0         1         2
    0  1.000000  1.000000  1.000000
    1  1.004929  0.998568  1.006448
    2  1.020301  0.996183  1.004044
    3  1.036490  1.003807  0.999291
    4  1.042076  0.999116  0.994598
    5  1.044549  0.980133  0.977540
    6  1.038640  0.970208  0.980568
    7  1.029200  0.956554  0.994996
    8  1.026827  0.957152  0.980871
    9  1.021202  0.958167  0.969598
    """
    data = generate_geometric_brownian(
        n_steps=n_bars,
        n_paths=n_assets,
        volatility=volatility,
        init_value=init_value,
        dt=dt,
        drift=drift,
    )

    bars = bars or list(range(n_bars))
    assets = assets or [str(i) for i in range(n_assets)]

    prices = pd.DataFrame(data, index=bars, columns=assets)

    return Universe(prices, name=name)
