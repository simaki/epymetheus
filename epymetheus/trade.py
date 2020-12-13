from copy import deepcopy

import numpy as np

from epymetheus.utils.array import catch_first_index


def trade(
    asset,
    lot=1.0,
    open_bar=None,
    shut_bar=None,
    take=None,
    stop=None,
):
    """
    Initialize `Trade`.

    Returns
    -------
    trade : Trade

    Examples
    --------
    >>> t = trade("AAPL")
    >>> t
    trade(['AAPL'], lot=[1.])

    >>> t = trade(["AAPL", "AMZN"])
    >>> t
    trade(['AAPL' 'AMZN'], lot=[1. 1.])

    >>> t = trade(["AAPL", "AMZN"], lot=[1.0, 2.0])
    >>> t
    trade(['AAPL' 'AMZN'], lot=[1. 2.])
    """
    return Trade.trade(
        asset=asset,
        lot=lot,
        open_bar=open_bar,
        shut_bar=shut_bar,
        take=take,
        stop=stop,
    )


class Trade:
    """
    Represent a single trade.

    Parameters
    ----------
    - asset : str or array of str
        Name of assets.
    - open_bar : object or None, default None
        Bar to open the trade.
    - shut_bar : object or None, default None
        Bar to enforce the trade to close.
    - lot : float, default 1.0
        Lot to trade in unit of share.
    - take : float > 0 or None, default None
        Threshold of profit-take.
    - stop : float < 0 or None, default None
        Threshold of stop-loss.

    Attributes
    ----------
    - close_bar : object
        Bar to close the trade.
        It is set by the method `self.execute`.

    Examples
    --------
    A long position:
    >>> import datetime
    >>> od = datetime.date(2018, 1, 1)
    >>> cd = datetime.date(2018, 2, 1)
    >>> t = trade(
    ...     asset='AAPL',
    ...     lot=2,
    ...     open_bar=datetime.date(2020, 1, 1),
    ...     shut_bar=datetime.date(2020, 2, 1),
    ... )

    A short position:
    >>> import datetime
    >>> t = -2 * Trade(
    ...     asset='AAPL',
    ...     open_bar=datetime.date(2020, 1, 1),
    ...     shut_bar=datetime.date(2020, 2, 1),
    ... )

    A long-short position:
    >>> import datetime
    >>> t = Trade(
    ...     asset=['AAPL', 'MSFT'],
    ...     lot=[1, -2],
    ...     open_bar=datetime.date(2020, 1, 1),
    ...     shut_bar=datetime.date(2020, 2, 1),
    ... )
    """

    def __init__(
        self,
        asset,
        lot=1.0,
        open_bar=None,
        shut_bar=None,
        take=None,
        stop=None,
    ):
        self.asset = asset
        self.lot = lot
        self.open_bar = open_bar
        self.shut_bar = shut_bar
        self.take = take
        self.stop = stop

    @classmethod
    def trade(
        cls,
        asset,
        lot=1.0,
        open_bar=None,
        shut_bar=None,
        take=None,
        stop=None,
    ):
        """
        Initialize `Trade`.

        Returns
        -------
        trade : Trade

        Examples
        --------
        >>> t = Trade.trade("AAPL")
        >>> t
        trade(['AAPL'], lot=[1.])

        >>> t = Trade.trade(["AAPL", "AMZN"])
        >>> t
        trade(['AAPL' 'AMZN'], lot=[1. 1.])

        >>> t = Trade.trade(["AAPL", "AMZN"], lot=[1.0, 2.0])
        >>> t
        trade(['AAPL' 'AMZN'], lot=[1. 2.])
        """
        asset = np.asarray(asset).reshape(-1)
        lot = np.broadcast_to(np.asarray(lot), asset.shape)

        return cls(
            asset=asset,
            lot=lot,
            open_bar=open_bar,
            shut_bar=shut_bar,
            take=take,
            stop=stop,
        )

    @property
    def is_executed(self):
        # Don't use "__is_executed"; it cannot be accessed by getattr.
        return getattr(self, "_is_executed", False)

    @property
    def array_asset(self):
        """
        Return asset as `numpy.array`.

        Returns
        -------
        array_asset : numpy.array, shape (n_orders, )

        Examples
        --------
        >>> trade = Trade(asset='AAPL')
        >>> trade.array_asset
        array(['AAPL'], dtype='<U4')

        >>> trade = Trade(asset=['AAPL', 'MSFT'])
        >>> trade.array_asset
        array(['AAPL', 'MSFT'], dtype='<U4')
        """
        return np.asarray(self.asset).reshape(-1)

    @property
    def array_lot(self):
        """
        Return lot as `numpy.array`.

        Returns
        -------
        array_lot : numpy.array, shape (n_orders, )

        Examples
        --------
        >>> trade = Trade(asset='AAPL', lot=0.2)
        >>> trade.array_lot
        array([0.2])
        >>> trade = Trade(asset=['AAPL', 'MSFT'], lot=[0.2, 0.4])
        >>> trade.array_lot
        array([0.2, 0.4])
        """
        return np.asarray(self.lot).reshape(-1)

    @property
    def n_orders(self):
        """
        Return number of assets in self.

        Returns
        -------
        n_orders : int
            Number of orders.

        Examples
        --------
        >>> trade = Trade(asset='AAPL')
        >>> trade.n_orders
        1
        >>> trade = Trade(asset=['AAPL', 'MSFT'])
        >>> trade.n_orders
        2
        """
        return self.array_asset.size

    def execute(self, universe):
        """
        Execute trade and set `self.close_bar`.

        Parameters
        ----------
        universe : Universe

        Returns
        -------
        self : Trade

        Examples
        --------
        >>> from pandas import DataFrame
        >>> from epymetheus import Universe
        >>> universe = Universe(DataFrame({
        ...     "A0": [1, 2, 3, 4, 5, 6, 7],
        ...     "A1": [2, 3, 4, 5, 6, 7, 8],
        ...     "A2": [3, 4, 5, 6, 7, 8, 9],
        ... }, dtype=float))
        >>> trade0 = Trade(asset="A0", lot=1.0, open_bar=1, shut_bar=6)
        >>> trade0 = trade0.execute(universe)
        >>> trade0.close_bar
        6
        >>> trade1 = Trade(asset="A0", lot=1.0, open_bar=1, shut_bar=6, take=2)
        >>> trade1 = trade1.execute(universe)
        >>> trade1.close_bar
        3
        >>> trade2 = Trade(asset="A0", lot=-1.0, open_bar=1, shut_bar=6, stop=-2)
        >>> trade2 = trade2.execute(universe)
        >>> trade2.close_bar
        3
        """
        self.close_bar = self.__get_close_bar(universe)
        self._is_executed = True

        return self

    def _array_value(self, universe):
        """
        Return value of self for each asset.

        Returns
        -------
        array_value : numpy.array, shape (n_bars, n_orders)

        Examples
        --------
        >>> from pandas import DataFrame
        >>> from epymetheus import Universe
        >>> universe = Universe(DataFrame({
        ...     "A0": [1, 2, 3, 4, 5],
        ...     "A1": [2, 3, 4, 5, 6],
        ...     "A2": [3, 4, 5, 6, 7],
        ... }, dtype=float))
        >>> trade = Trade(asset=["A0", "A2"], lot=[2, -3], open_bar=1, shut_bar=3)
        >>> trade._array_value(universe)
        array([[  2.,  -9.],
               [  4., -12.],
               [  6., -15.],
               [  8., -18.],
               [ 10., -21.]])
        """
        asset_index = universe.get_asset_indexer(self.asset)
        array_prices = universe.prices.iloc[:, asset_index].values
        # (n_orders, ) * (n_bars, n_orders) -> (n_bars, n_orders)
        array_value = self.lot * array_prices
        return array_value

    def array_exposure(self, universe):
        """
        Return exposure of self for each order.

        Returns
        -------
        array_exposure : numpy.array, shape (n_bars, n_orders)

        Examples
        --------
        >>> from pandas import DataFrame
        >>> from epymetheus import Universe
        >>> universe = Universe(DataFrame({
        ...     "A0": [1, 2, 3, 4, 5],
        ...     "A1": [2, 3, 4, 5, 6],
        ...     "A2": [3, 4, 5, 6, 7],
        ... }, dtype=float))
        >>> trade = Trade(asset=["A0", "A2"], lot=[2, -3], open_bar=1, shut_bar=3)
        >>> trade.array_exposure(universe)
        array([[  0.,   0.],
               [  4., -12.],
               [  6., -15.],
               [  8., -18.],
               [  0.,   0.]])
        """
        array_value = self._array_value(universe)

        stop_bar = self.__stop_bar(universe)

        open_bar_index = universe.get_bar_indexer(self.open_bar)[0]
        stop_bar_index = universe.get_bar_indexer(stop_bar)[0]

        array_exposure = array_value
        array_exposure[:open_bar_index] = 0
        array_exposure[stop_bar_index + 1 :] = 0

        return array_exposure

    def series_exposure(self, universe, net=True):
        """
        Return time-series of value of the position.

        Parameters
        ----------
        - universe : Universe
        - net : bool, default True
            If True, return net exposure.
            If False, return absolute exposure.

        Returns
        -------
        series_exposure : numpy.array, shape (n_bars, )

        Examples
        --------
        >>> from pandas import DataFrame
        >>> from epymetheus import Universe
        >>> universe = Universe(DataFrame({
        ...     "A0": [1, 2, 3, 4, 5],
        ...     "A1": [2, 3, 4, 5, 6],
        ...     "A2": [3, 4, 5, 6, 7],
        ... }, dtype=float))
        >>> trade = Trade(asset=["A0", "A2"], lot=[2, -3], open_bar=1, shut_bar=3)
        >>> trade.series_exposure(universe, net=True)
        array([  0.,  -8.,  -9., -10.,   0.])
        >>> trade.series_exposure(universe, net=False)
        array([ 0., 16., 21., 26.,  0.])
        """
        array_exposure = self.array_exposure(universe)
        if net:
            series_exposure = array_exposure.sum(axis=1)
        else:
            series_exposure = np.abs(array_exposure).sum(axis=1)

        return series_exposure

    def array_pnl(self, universe):
        """
        Return profit-loss of self for each order.

        Returns
        -------
        array_exposure : numpy.array, shape (n_bars, n_orders)

        Examples
        --------
        >>> from pandas import DataFrame
        >>> from epymetheus import Universe
        >>> universe = Universe(DataFrame({
        ...     "A0": [1, 2, 3, 4, 5],
        ...     "A1": [2, 3, 4, 5, 6],
        ...     "A2": [3, 4, 5, 6, 7],
        ... }, dtype=float))
        >>> trade = Trade(asset=["A0", "A2"], lot=[2, -3], open_bar=1, shut_bar=3)
        >>> trade.array_pnl(universe)
        array([[ 0.,  0.],
               [ 0.,  0.],
               [ 2., -3.],
               [ 4., -6.],
               [ 4., -6.]])
        """
        array_value = self._array_value(universe)

        stop_bar = self.__stop_bar(universe)

        open_bar_index = universe.get_bar_indexer(self.open_bar)[0]
        stop_bar_index = universe.get_bar_indexer(stop_bar)[0]

        array_pnl = array_value
        array_pnl -= array_pnl[open_bar_index]
        array_pnl[:open_bar_index] = 0
        array_pnl[stop_bar_index:] = array_pnl[stop_bar_index]

        return array_pnl

    def series_pnl(self, universe):
        """
        Return profit-loss of self.

        Returns
        -------
        net_exposure : numpy.array, shape (n_bars, )

        Examples
        --------
        >>> from pandas import DataFrame
        >>> from epymetheus import Universe
        >>> universe = Universe(DataFrame({
        ...     "A0": [1, 2, 3, 4, 5],
        ...     "A1": [2, 3, 4, 5, 6],
        ...     "A2": [3, 4, 5, 6, 7],
        ... }, dtype=float))
        >>> trade = Trade(asset="A0", lot=1, open_bar=1, shut_bar=3)
        >>> trade = trade.execute(universe)
        >>> trade.series_pnl(universe)
        array([0., 0., 1., 2., 2.])
        """
        return self.array_pnl(universe).sum(axis=1)

    def final_pnl(self, universe):
        """
        Return final profit-loss of self.

        Returns
        -------
        pnl : numpy.array, shapr (n_orders, )

        Raises
        ------
        ValueError
            If self has not been `run`.

        Examples
        --------
        >>> from pandas import DataFrame
        >>> from epymetheus import Universe
        >>> universe = Universe(DataFrame({
        ...     "A0": [1, 2, 3, 4, 5],
        ...     "A1": [2, 3, 4, 5, 6],
        ...     "A2": [3, 4, 5, 6, 7],
        ... }, dtype=float))
        >>> trade = Trade(asset=["A0", "A2"], lot=1, open_bar=1, shut_bar=3)
        >>> trade = trade.execute(universe)
        >>> trade.final_pnl(universe)
        array([2., 2.])
        """
        # TODO: make it more efficient
        open_bar_index = universe.get_bar_indexer(self.open_bar)[0]
        close_bar_index = universe.get_bar_indexer(self.close_bar)[0]
        array_exposure = self.array_exposure(universe)
        final_pnl = (
            array_exposure[close_bar_index, :] - array_exposure[open_bar_index, :]
        )

        return final_pnl

    def __get_close_bar(self, universe):
        """
        Used in self.execute.

        Returns
        -------
        close_bar
        """
        stop_bar = self.__stop_bar(universe)

        if self.take is None and self.stop is None:
            close_bar = stop_bar
        else:
            series_pnl = self.series_pnl(universe)

            signal_take = series_pnl >= (self.take or np.inf)
            signal_stop = series_pnl <= (self.stop or -np.inf)

            close_bar_index = catch_first_index(np.logical_or(signal_take, signal_stop))
            stop_bar_index = universe.get_bar_indexer(stop_bar)

            if close_bar_index == -1 or close_bar_index > stop_bar_index:
                close_bar = stop_bar
            else:
                close_bar = universe.bars[close_bar_index]

        return close_bar

    def __stop_bar(self, universe):
        if self.is_executed:
            stop_bar = self.close_bar
        elif self.shut_bar is not None:
            stop_bar = self.shut_bar
        else:
            stop_bar = universe.bars[-1]
        return stop_bar

    def __mul__(self, num):
        return self.__rmul__(num)

    def __rmul__(self, num):
        """
        Multiply lot of self.

        Examples
        --------
        >>> trade("AMZN")
        trade(['AMZN'], lot=[1.])
        >>> (-2.0) * trade("AMZN")
        trade(['AMZN'], lot=[-2.])

        >>> trade(["AMZN", "AAPL"])
        trade(['AMZN' 'AAPL'], lot=[1. 1.])
        >>> (-2.0) * trade(["AMZN", "AAPL"])
        trade(['AMZN' 'AAPL'], lot=[-2. -2.])
        >>> [2.0, 3.0] * trade(["AMZN", "AAPL"])
        trade(['AMZN' 'AAPL'], lot=[2. 3.])
        """
        t = deepcopy(self)
        t.lot = t.lot * np.asarray(num)
        return t

    def __neg__(self):
        """
        Invert the lot of self.

        Examples
        --------
        >>> -trade("AMZN")
        trade(['AMZN'], lot=[-1.])
        """
        return (-1.0) * self

    def __truediv__(self, num):
        """
        Divide the lot of self.

        Examples
        --------
        >>> trade("AMZN", lot=2.0) / 2.0
        trade(['AMZN'], lot=[1.])

        >>> trade(["AMZN", "AAPL"], lot=[2.0, 4.0]) / 2.0
        trade(['AMZN' 'AAPL'], lot=[1. 2.])
        """
        return self.__mul__(1.0 / num)

    def __repr__(self):
        """
        >>> t = trade("AMZN", open_bar=1)
        >>> t
        trade(['AMZN'], lot=[1.], open_bar=1)

        >>> t = trade("AMZN", take=100.0)
        >>> t
        trade(['AMZN'], lot=[1.], take=100.0)
        """
        params = [f"{self.asset}", f"lot={self.lot}"]

        for attr in ("open_bar", "shut_bar", "take", "stop"):
            value = getattr(self, attr)
            if value is not None:
                params.append(f"{attr}={value}")

        return f"trade({', '.join(params)})"