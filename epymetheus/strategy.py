from abc import ABCMeta, abstractmethod
from inspect import cleandoc
from time import time

from epymetheus.history import History
from epymetheus.transaction import Transaction
from epymetheus.wealth import Wealth
from epymetheus import pipe

try:
    from functools import cached_property
except ImportError:
    cached_property = property


class TradeStrategy(metaclass=ABCMeta):
    """
    Represents a strategy to trade.

    Parameters
    ----------
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
    - universe : Universe
    - history : History
    - transaction : Transaction
    - wealth : Wealth

    Examples
    --------
    Define strategy by subclassing:
    >>> class MyTradeStrategy(TradeStrategy):
    ...     '''This is my favorite strategy.'''
    ...
    ...     def logic(universe, my_parameter):
    ...         ...
    ...         yield Trade(...)

    Initialize:
    >>> my_strategy = MyTradeStrategy(my_parameter=0.1)
    >>> my_strategy.name
    'MyTradeStrategy'
    >>> my_strategy.description
    'This is my favorite strategy.'
    >>> my_strategy.params
    {'my_parameter': 0.1}

    Run:
    >>> universe = Universe(...)
    >>> my_strategy.run(universe)
    """
    def __init__(self, **params):
        self.params = params
        self.is_runned = False

    @abstractmethod
    def logic(self, universe, **kwargs):
        """
        Logic to return iterable of ``Trade`` from ``Universe``.

        Parameters
        ----------
        - universe : Universe
            Universe to apply the logic.
        - kwargs
            Parameters of the trade strategy.
        """

    def run(self, universe, verbose=True, save={}):
        """
        Run a backtesting of strategy.
        Set attributes `history`, `transaction` and `wealth`.

        Parameters
        ----------
        - universe : Universe
        - verbose : bool
        - save : dict

        Returns
        -------
        self
        """
        if verbose:
            begin_time = time()
            print('Running ... ')

        self.universe = universe
        self.trades = self.__generate_trades(verbose=verbose)
        self.history = History(strategy=self, verbose=verbose)
        self.transaction = Transaction(strategy=self, verbose=verbose)
        self.wealth = Wealth(strategy=self, verbose=verbose)
        self.is_runned = True

        if verbose:
            print(f'Done. (Runtime : {time() - begin_time:.1f} sec)')

        return self

    @property
    def name(self):
        """Return name of the strategy."""
        return self.__class__.__name__

    @property
    def description(self):
        """Return detailed description of the strategy."""
        return cleandoc(self.__class__.__doc__)

    @cached_property
    def n_trades(self):
        return len(self.trades)

    @cached_property
    def n_orders(self):
        return sum(trade.n_orders for trade in self.trades)

    @cached_property
    def trade_index(self):
        return pipe.trade_index(self)

    @cached_property
    def order_index(self):
        return pipe.order_index(self)

    @cached_property
    def asset_ids(self):
        return pipe.asset_ids(self)

    @property
    def assets(self):
        if self.n_trades == 0:
            return []
        return self.universe.assets[self.asset_ids]

    @cached_property
    def lots(self):
        return pipe.lots(self)

    @cached_property
    def open_bar_ids(self):
        return pipe.open_bar_ids(self)

    @property
    def open_bars(self):
        return self.universe.bars[self.open_bar_ids]

    @cached_property
    def close_bar_ids(self):
        return pipe.close_bar_ids(self)

    @property
    def close_bars(self):
        return self.universe.bars[self.close_bar_ids]

    @cached_property
    def atakes(self):
        return pipe.atakes(self)

    @cached_property
    def durations(self):
        return pipe.durations(self)

    @cached_property
    def open_prices(self):
        return pipe.open_prices(self)

    @cached_property
    def close_prices(self):
        return pipe.close_prices(self)

    @cached_property
    def gains(self):
        return pipe.gains(self)

    @cached_property
    def wealth_(self):
        return pipe.wealth(self)

    @property
    def _lot_matrix(self):
        return pipe._lot_matrix(self)

    @property
    def _value_matrix(self):
        return pipe._value_matrix(self)

    @property
    def _opening_matrix(self):
        return pipe._opening_matrix(self)

    @property
    def _closebar_matrix(self):
        return pipe._closebar_matrix(self)

    @property
    def _acumpnl_matrix(self):
        return pipe._acumpnl_matrix(self)

    @property
    def _transaction_matrix(self):
        return pipe._transaction_matrix(self)

    @property
    def _close_by_signals(self):
        return pipe._close_by_signals(self)

    def __generate_trades(self, verbose=True):
        """
        Parameters
        ----------
        - self
            TradeStrategy; necessary attributes:
            * universe
        - verbose : bool

        Returns
        -------
        - list of Trade
        """
        iter_trades = self.logic(self.universe, **self.params) or []

        def iter_trades_verbose():
            for i, trade in enumerate(iter_trades):
                print(f'\rGenerating {i + 1} trades ... ', end='')
                yield trade
            print('Done.')

        if verbose:
            trades = list(iter_trades_verbose())
            if len(trades) == 0:
                raise RuntimeError('No trade yielded')
            return trades
        else:
            trades = list(iter_trades)
            if len(trades) == 0:
                raise RuntimeError('No trade yielded')
            return trades
