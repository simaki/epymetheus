import abc
from inspect import cleandoc
from time import time

import numpy as np
import pandas as pd

from epymetheus.exceptions import NoTradeError
from epymetheus.exceptions import NotRunError
from epymetheus.history import History


def create_strategy(logic_func, **params):
    """
    Initialize `Strategy` from function.

    Parameters
    ----------
    - logic_func : callable
        Function that returns iterable from universe and parameters.
    - **params
        Parameter values.

    Examples
    --------
    >>> from epymetheus import trade
    ...
    >>> def logic_func(universe, my_param):
    ...     return [my_param * trade("A")]
    ...
    >>> strategy = create_strategy(logic_func, my_param=2.0)
    >>> universe = None
    >>> strategy(universe)
    [trade(['A'], lot=[2.])]
    """
    return Strategy._create_strategy(logic_func=logic_func, params=params)


class Strategy(abc.ABC):
    """
    Represents a strategy to trade.

    Parameters
    ----------
    - logic : callable
    -

    - name : str, optional
        Name of the strategy.
    - description : str, optional
        Description of the strategy.
        If None, docstring.
    - params : dict
        Parameters of the logic.

    Attributes
    ----------
    - trades : array of Trade, shape (n_trades, )
    - n_trades : int
    - n_orders : int
    - universe : pandas.DataFrame
    - history : History
    - transaction : Transaction

    Examples
    --------
    Define strategy by subclassing:
    >>> from epymetheus import trade
    >>> class MyStrategy(Strategy):
    ...     '''
    ...     This is my favorite strategy.
    ...     '''
    ...     def __init__(self, my_parameter):
    ...         self.my_parameter = my_parameter
    ...
    ...     def logic(self, universe):
    ...         ...
    ...         yield trade(...)

    Initialize:
    >>> my_strategy = MyStrategy(my_parameter=0.1)
    >>> my_strategy.name
    'MyStrategy'
    >>> my_strategy.description
    'This is my favorite strategy.'

    Run:
    >>> from epymetheus.datasets import make_randomwalk
    >>> universe = make_randomwalk()
    >>> _ = my_strategy.run(universe, verbose=False)
    """

    def __init__(self, logic_func=None, name=None, description=None, params=None):
        if logic_func is not None:
            self.logic_func = logic_func
            self.params = params or {}

    @classmethod
    def _create_strategy(cls, logic_func, params):
        """
        Create strategy from logic function.

        Parameters
        ----------
        - logic_func : callable
        - params : dict

        Returns
        -------
        strategy : Strategy
        """
        return cls(logic_func=logic_func, params=params)

    def __call__(self, universe, to_list=True):
        logic = getattr(self, "logic_func", self.logic)
        trades = logic(universe, **getattr(self, "params", {}))
        if to_list:
            trades = list(trades)
        return trades

    def logic(self, universe):
        """
        Logic to generate trades from universe.

        Parameters
        ----------
        - universe : pandas.DataFrame
            Historical price data to apply this strategy.
            The index represents timestamps and the column is the assets.

        Returns
        ------
        trades : iterable of trades
        """

    @property
    def name(self):
        """Return name of the strategy."""
        return self.__class__.__name__

    @property
    def description(self):
        """
        Return detailed description of the strategy.

        Returns
        -------
        description : str or None
            If strategy class has no docstring, return None.
        """
        if self.__class__.__doc__ is None:
            description = None
        else:
            description = cleandoc(self.__class__.__doc__)
        return description

    @property
    def n_trades(self):
        return len(self.trades)

    @property
    def n_orders(self):
        return sum(t.n_orders for t in self.trades)

    @property
    def history(self):
        return History(strategy=self)

    def wealth(self, universe=None):
        """
        Return `pandas.Series` of wealth.

        Returns
        -------
        wealth : pandas.Series
            Series of wealth.
        """
        universe = universe or self.universe

        wealth = np.zeros_like(universe.iloc[:, 0])
        for t in self.trades:
            i_open = universe.index.get_indexer([t.open_bar]).item()
            i_open = i_open if i_open != -1 else 0
            i_close = universe.index.get_loc(t.close_bar)

            value = t.array_value(universe).sum(axis=1)
            pnl = value - value[i_open]
            pnl[:i_open] = 0
            pnl[i_close:] = pnl[i_close]

            wealth += pnl

        return pd.Series(wealth, index=universe.index)

    def run(self, universe, verbose=True):
        """
        Run a backtesting of strategy.

        Parameters
        ----------
        - universe : pandas.DataFrame
            Historical price data to apply this strategy.
            The index represents timestamps and the column is the assets.
        - verbose : bool, default True
            Verbose mode.

        Returns
        -------
        self
        """
        _begin_time = time()

        self.universe = universe

        # Yield trades
        _begin_time_yield = time()
        trades = []
        for i, t in enumerate(self(universe, to_list=False) or []):
            if verbose:
                print(f"\rYield {i + 1} trades: {t} ... ", end="")
            trades.append(t)
        if len(trades) == 0:
            raise NoTradeError("No trade.")
        if verbose:
            _time = time() - _begin_time_yield
            print(f"Done. (Runtume: {_time:.4f} sec)")

        # Execute trades
        _begin_time_execute = time()
        for i, t in enumerate(trades):
            if verbose:
                print(f"\rExecute {i + 1} trades: {t} ... ", end="")
            t.execute(universe)
        if verbose:
            _time = time() - _begin_time_execute
            print(f"Done. (Runtime: {_time:.4f} sec)")

        if verbose:
            _time = time() - _begin_time
            print(f"Done. (Runtime: {_time:.4f} sec)")

        self.trades = trades
        return self

    def get_params(self):
        """
        Set the parameters of this strategy.

        Returns
        -------
        params : dict[str, *]
            Parameters.
        """
        return getattr(self, "params", {})

    def set_params(self, **params):
        """
        Set the parameters of this strategy.

        Parameters
        ----------
        - **params : dict
            Strategy parameters.

        Returns
        -------
        self : Strategy
            Strategy with new parameters.
        """
        valid_keys = self.get_params().keys()

        for key, value in params.items():
            if key not in valid_keys:
                raise ValueError(f"Invalid parameter: {key}")
            else:
                self.params[key] = value

        return self

    def score(self, metric):
        """
        Returns the value of a metric of self.

        Parameters
        ----------
        - metric : Metric or str
            Metric to evaluate.
        """
        if not hasattr(self, "trades"):
            raise NotRunError("Strategy has not been run")

        return metric.result(self)

    def evaluate(self, metric):
        raise DeprecationWarning(
            "Strategy.evaluate(...) is deprecated. Use Strategy.score(...) instead."
        )
