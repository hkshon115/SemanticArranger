"""
This module implements the factory pattern for creating extraction strategies.

The `StrategyFactory` is responsible for instantiating and providing the
correct strategy object based on a given strategy name. This decouples the
`AsyncExtractor` from the concrete strategy implementations, making the system
more modular and extensible.
"""
from typing import Dict, Type
from backend.models.extraction import ExtractionStrategy
from backend.strategies.base import IExtractionStrategy

# This will be populated by the individual strategy modules
_strategy_map: Dict[str, Type[IExtractionStrategy]] = {}

def register_strategy(name: str, strategy_class: Type[IExtractionStrategy]):
    """
    Registers an extraction strategy class with the factory.
    """
    _strategy_map[name] = strategy_class

def get_strategy(strategy_name: str, **kwargs) -> IExtractionStrategy:
    """
    Retrieves an instance of the specified extraction strategy.

    :param strategy_name: The name of the strategy to retrieve.
    :param kwargs: Additional arguments to pass to the strategy's constructor.
    :return: An instance of the requested extraction strategy.
    :raises ValueError: If the requested strategy is not registered.
    """
    strategy_class = _strategy_map.get(strategy_name)
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    return strategy_class(**kwargs)
