"""
Data Processors Package

This package provides multiple data processing strategies that conform to the
AbstractDataProcessor contract.

Available Strategies:
- AIDataProcessor: An advanced processor that uses an LLM for structuring and categorization.
- RuleBasedDataProcessor: A simpler processor that uses hard-coded rules.
"""

from .abstract_processor import AbstractDataProcessor
from .ai_data_processor import AIDataProcessor
from .rule_based_data_processor import RuleBasedDataProcessor

__all__ = [
    'AbstractDataProcessor',
    'AIDataProcessor',
    'RuleBasedDataProcessor'
]
