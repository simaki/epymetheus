import abc
from inspect import cleandoc
from time import time

from epymetheus.exceptions import NoTradeError
from epymetheus.exceptions import NotRunError
from epymetheus.history import History
from epymetheus.wealth import Wealth


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
    - universe : Universe
    - history : History
    - transaction : Transaction
    - wealth : Wealth

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

    Todo
    ----
    - dump trades in a light data structure
    """

    def __init__(self, logic_func=None, name=None, description=None, params=None):
        """
        Initialize self.
        """
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

    def __call__(self, universe):
        logic = getattr(self, "logic_func", self.logic)
        return list(logic(universe, **getattr(self, "params", {})))

    def logic(self, universe):
        """
        Logic to generate `Trade` from `Universe`.

        Parameters
        ----------
        - universe : Universe
            Universe to apply the logic.

        Yields
        ------
        trade : Trade
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
    def is_run(self):
        # Don't use "__is_run"; it cannot be accessed by getattr.
        return getattr(self, "_is_run", False)

    @property
    def n_trades(self):
        return len(self.trades)

    @property
    def n_orders(self):
        return sum(t.n_orders for t in self.trades)

    @property
    def history(self):
        return History(strategy=self)

    @property
    def wealth(self):
        return Wealth(strategy=self)

    def run(self, universe, metrics=[], budget=0.0, verbose=True):
        """
        Run a backtesting of strategy.

        Parameters
        ----------
        - universe : Universe
            Universe with which self is run.
        - metrics : List[metrics]
            List of metrics to be evaluated for the strategy during running.
            See epymetheus.metrics.
        - budget : float, default 0.0
            Initial budget.
        - verbose : bool, default True
            Verbose mode.

        Returns
        -------
        self
        """
        self.__compile(metrics=metrics, budget=budget)

        if verbose:
            begin_time = time()
            print("Running ... ")

        self.universe = universe
        self.__generate_trades(universe=universe, verbose=verbose)
        self.__execute_trades(universe=universe, verbose=verbose)

        self._is_run = True

        if verbose:
            print(f"Done. (Runtime : {time() - begin_time:.2f} sec)")

        return self

    def get_params(self):
        return getattr(self, "params")

    def set_params(self, params):
        if hasattr(self, "params"):
            self.params = params
        else:
            raise AttributeError

    def __compile(self, metrics, budget):
        self.metrics = metrics
        self.budget = budget

    def __generate_trades(self, universe, verbose=True):
        """
        Generate trades according to `self.logic`.
        It sets `self.trades`.

        Parameters
        ----------
        - verbose : bool

        Returns
        -------
        self : Strategy
        """

        def iter_trades(verbose):
            if verbose:
                begin_time = time()
                for i, t in enumerate(self.logic(universe) or []):
                    print(
                        f"\rGenerating {i + 1} trades " f"({t.open_bar}) ... ",
                        end="",
                    )
                    yield t
                print(f"Done. (Runtime : {time() - begin_time:.2f} sec)")
            else:
                for t in self.logic(universe) or []:
                    yield t

        self.trades = list(iter_trades(verbose))

        if len(self.trades) == 0:
            raise NoTradeError("No trades")

        return self

    def __execute_trades(self, universe, verbose=True):
        """
        Execute trades.

        Returns
        -------
        self : Strategy
        """
        if verbose:
            begin_time = time()
            for i, t in enumerate(self.trades):
                print(f"\rExecuting {i + 1} trades ... ", end="")
                t.execute(universe)
            print(f"Done. (Runtime : {time() - begin_time:.2f} sec)")
        else:
            for t in self.trades:
                t.execute(universe)

        return self

    def score(self, metric):
        """
        Returns the value of a metric of self.

        Parameters
        ----------
        - metric : Metric or str
            Metric to evaluate.
        """
        if not self.is_run:
            raise NotRunError("Strategy has not been run")

        return metric.result(self)

    def evaluate(self, metric):
        raise DeprecationWarning(
            "Strategy.evaluate(...) is deprecated. Use Strategy.score(...) instead."
        )
