import pytest
from ._utils import make_randomuniverse, generate_trades

import random
import pandas as pd
import numpy as np

from epymetheus import Trade, TradeStrategy, Universe


list_seed = [42, 1, 2, 3]
list_n_bars = [10, 1000]
list_n_assets = [1, 100]
list_lot = [0.0, 1, 1.23, -1.0, 123.4, -123.4]


class OneTradeStrategy(TradeStrategy):
    """
    Yield a single trade.
    """
    def logic(self, universe, asset, lot, open_bar, close_bar):
        yield Trade(asset=asset, lot=lot, open_bar=open_bar, close_bar=close_bar)


# --------------------------------------------------------------------------------


@pytest.mark.parametrize('seed', list_seed)
@pytest.mark.parametrize('n_bars', list_n_bars)
@pytest.mark.parametrize('n_assets', list_n_assets)
@pytest.mark.parametrize('lot', list_lot)
def test_one(seed, n_bars, n_assets, lot):
    np.random.seed(seed); random.seed(seed)

    universe = make_randomuniverse(n_bars, n_assets)

    trade = list(generate_trades(universe, [lot], 1))[0]
    asset, lot, open_bar, close_bar = trade

    strategy = OneTradeStrategy(
        asset=asset, lot=lot, open_bar=open_bar, close_bar=close_bar,
    )
    strategy.run(universe)

    open_price = universe.prices.at[open_bar, asset]
    close_price = universe.prices.at[close_bar, asset]
    gain = lot * (close_price - open_price)

    assert strategy.history.order_index == np.array([0])
    assert strategy.history.trade_index == np.array([0])

    assert strategy.history.assets == np.array([asset])
    assert strategy.history.lots == np.array([lot])
    assert strategy.history.open_bars == np.array([open_bar])
    assert strategy.history.close_bars == np.array([close_bar])
    assert strategy.history.durations == np.array([close_bar - open_bar])
    assert strategy.history.open_prices == np.array([open_price])
    assert strategy.history.close_prices == np.array([close_price])
    assert strategy.history.gains == np.array([gain])

    # TODO test transaction, wealth
