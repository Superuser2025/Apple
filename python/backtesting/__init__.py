"""
AppleTrader Pro - Backtesting Module
"""

from backtesting.backtest_engine import backtest_engine, BacktestEngine, BacktestResults
from backtesting.strategy_adapter import strategy_quality_70, strategy_quality_75, strategy_quality_80

__all__ = [
    'backtest_engine',
    'BacktestEngine',
    'BacktestResults',
    'strategy_quality_70',
    'strategy_quality_75',
    'strategy_quality_80'
]
