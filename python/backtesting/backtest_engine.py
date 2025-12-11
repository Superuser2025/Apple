"""
AppleTrader Pro - Backtesting Engine
Tests trading strategies on historical data to validate profitability

This module allows you to:
1. Load historical OHLC data
2. Run your strategy on past data
3. Simulate trades (entry, SL hit, TP hit)
4. Calculate performance metrics
5. Compare different strategies
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np


class TradeOutcome(Enum):
    """Trade exit outcomes"""
    TP_HIT = "TP_HIT"  # Take profit hit (winner)
    SL_HIT = "SL_HIT"  # Stop loss hit (loser)
    TIMEOUT = "TIMEOUT"  # Trade timed out (closed at current price)


@dataclass
class BacktestTrade:
    """
    Individual trade in backtest
    """
    # Entry details
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    entry_time: datetime
    lot_size: float

    # Exit levels
    stop_loss: float
    take_profit: float

    # Exit details (filled when trade closes)
    exit_price: float = 0.0
    exit_time: Optional[datetime] = None
    outcome: Optional[TradeOutcome] = None

    # P&L calculation
    pips_result: float = 0.0  # Pips won/lost
    r_multiple: float = 0.0  # Risk:Reward multiple achieved
    profit_loss: float = 0.0  # Dollar P&L

    # Context (why trade was taken)
    pattern_score: int = 0
    confluence_reasons: List[str] = field(default_factory=list)

    def calculate_pnl(self):
        """Calculate P&L after exit"""
        if self.direction == 'BUY':
            pips_move = (self.exit_price - self.entry_price) * 10000
        else:  # SELL
            pips_move = (self.entry_price - self.exit_price) * 10000

        self.pips_result = pips_move

        # Calculate R-multiple
        risk_pips = abs(self.entry_price - self.stop_loss) * 10000
        if risk_pips > 0:
            self.r_multiple = pips_move / risk_pips

        # Calculate dollar P&L (simplified: $10 per pip per lot)
        pip_value = 10.0  # $10 per pip for 1 standard lot
        self.profit_loss = pips_move * pip_value * self.lot_size


@dataclass
class BacktestResults:
    """
    Complete backtest results with performance metrics
    """
    # Basic stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # P&L stats
    total_pnl: float = 0.0
    total_pips: float = 0.0
    avg_win_pips: float = 0.0
    avg_loss_pips: float = 0.0
    avg_r_multiple: float = 0.0
    profit_factor: float = 0.0

    # Risk metrics
    max_drawdown_pct: float = 0.0
    max_drawdown_dollars: float = 0.0
    max_consecutive_losses: int = 0
    sharpe_ratio: float = 0.0

    # Time analysis
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    days_tested: int = 0
    avg_trades_per_day: float = 0.0

    # Trade list
    trades: List[BacktestTrade] = field(default_factory=list)

    # Equity curve
    equity_curve: List[float] = field(default_factory=list)
    dates: List[datetime] = field(default_factory=list)

    # Strategy info
    strategy_name: str = ""
    symbol: str = ""
    timeframe: str = ""

    def calculate_metrics(self, starting_balance: float = 10000.0):
        """Calculate all performance metrics"""
        if not self.trades:
            return

        # Basic stats
        self.total_trades = len(self.trades)
        self.winning_trades = sum(1 for t in self.trades if t.profit_loss > 0)
        self.losing_trades = sum(1 for t in self.trades if t.profit_loss < 0)
        self.win_rate = (self.winning_trades / self.total_trades) * 100 if self.total_trades > 0 else 0

        # P&L stats
        self.total_pnl = sum(t.profit_loss for t in self.trades)
        self.total_pips = sum(t.pips_result for t in self.trades)

        winners = [t.pips_result for t in self.trades if t.pips_result > 0]
        losers = [t.pips_result for t in self.trades if t.pips_result < 0]

        self.avg_win_pips = np.mean(winners) if winners else 0
        self.avg_loss_pips = np.mean(losers) if losers else 0
        self.avg_r_multiple = np.mean([t.r_multiple for t in self.trades])

        # Profit factor
        total_wins = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        total_losses = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        self.profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Build equity curve
        balance = starting_balance
        self.equity_curve = [balance]
        self.dates = [self.trades[0].entry_time if self.trades else datetime.now()]

        for trade in self.trades:
            balance += trade.profit_loss
            self.equity_curve.append(balance)
            self.dates.append(trade.exit_time or trade.entry_time)

        # Calculate drawdown
        peak = starting_balance
        max_dd = 0
        max_dd_pct = 0

        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = peak - equity
            dd_pct = (dd / peak) * 100 if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

        self.max_drawdown_dollars = max_dd
        self.max_drawdown_pct = max_dd_pct

        # Max consecutive losses
        current_streak = 0
        max_streak = 0
        for trade in self.trades:
            if trade.profit_loss < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        self.max_consecutive_losses = max_streak

        # Sharpe ratio (simplified)
        if len(self.trades) > 1:
            returns = [t.profit_loss for t in self.trades]
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            self.sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0

        # Time analysis
        if self.trades:
            self.start_date = self.trades[0].entry_time
            self.end_date = self.trades[-1].exit_time or self.trades[-1].entry_time
            self.days_tested = (self.end_date - self.start_date).days
            self.avg_trades_per_day = self.total_trades / max(1, self.days_tested)


class BacktestEngine:
    """
    Main backtesting engine

    Runs trading strategies on historical data and returns performance metrics
    """

    def __init__(self):
        self.default_starting_balance = 10000.0
        self.default_risk_per_trade = 0.5  # 0.5% risk per trade

    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        strategy_func,
        starting_balance: float = None,
        risk_percent: float = None,
        max_trades: int = None
    ) -> BacktestResults:
        """
        Run backtest on historical data

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (H1, H4, D1, etc.)
            data: Historical OHLC DataFrame
            strategy_func: Function that evaluates opportunities
                          Must return dict with: direction, entry, sl, tp, score, reasons
            starting_balance: Starting account balance
            risk_percent: Risk per trade (%)
            max_trades: Maximum trades to take (for testing)

        Returns:
            BacktestResults with all metrics
        """

        if starting_balance is None:
            starting_balance = self.default_starting_balance

        if risk_percent is None:
            risk_percent = self.default_risk_per_trade

        results = BacktestResults(
            strategy_name="Pattern Trading",
            symbol=symbol,
            timeframe=timeframe
        )

        trades: List[BacktestTrade] = []
        current_balance = starting_balance

        print(f"\n[Backtest] Starting backtest on {symbol} {timeframe}")
        print(f"[Backtest] Data range: {data.index[0]} to {data.index[-1]}")
        print(f"[Backtest] Total candles: {len(data)}")

        # Iterate through historical data (skip first 200 candles for indicators)
        for i in range(200, len(data)):
            # Stop if max trades reached
            if max_trades and len(trades) >= max_trades:
                break

            # Get data up to current point (simulate real-time)
            current_data = data.iloc[:i+1].copy()

            # Run strategy to get signal
            try:
                signal = strategy_func(current_data)
            except Exception as e:
                print(f"[Backtest] Strategy error at index {i}: {e}")
                continue

            if not signal or signal.get('direction') not in ['BUY', 'SELL']:
                continue  # No signal

            # Create trade
            entry_price = signal['entry']
            stop_loss = signal['sl']
            take_profit = signal['tp']

            # Calculate lot size based on risk
            risk_amount = current_balance * (risk_percent / 100)
            pips_risk = abs(entry_price - stop_loss) * 10000
            pip_value = 10.0  # $10 per pip per standard lot
            lot_size = risk_amount / (pips_risk * pip_value) if pips_risk > 0 else 0.01
            lot_size = round(min(lot_size, 1.0), 2)  # Cap at 1.0 lot

            trade = BacktestTrade(
                symbol=symbol,
                direction=signal['direction'],
                entry_price=entry_price,
                entry_time=current_data.index[-1],
                lot_size=lot_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                pattern_score=signal.get('score', 0),
                confluence_reasons=signal.get('reasons', [])
            )

            # Simulate trade outcome
            outcome = self._simulate_trade(trade, data.iloc[i+1:])

            if outcome:
                trade.calculate_pnl()
                trades.append(trade)
                current_balance += trade.profit_loss

                # Print trade result
                outcome_str = "✓ WIN" if trade.profit_loss > 0 else "✗ LOSS"
                print(f"[Backtest] Trade #{len(trades)}: {trade.direction} {outcome_str} "
                      f"| {trade.pips_result:.1f} pips | R:{trade.r_multiple:.2f} | "
                      f"Balance: ${current_balance:.2f}")

        results.trades = trades
        results.calculate_metrics(starting_balance)

        print(f"\n[Backtest] Completed: {results.total_trades} trades")
        print(f"[Backtest] Win Rate: {results.win_rate:.1f}%")
        print(f"[Backtest] Total P&L: ${results.total_pnl:.2f}")
        print(f"[Backtest] Avg R-multiple: {results.avg_r_multiple:.2f}")

        return results

    def _simulate_trade(
        self,
        trade: BacktestTrade,
        future_data: pd.DataFrame,
        max_bars: int = 100
    ) -> bool:
        """
        Simulate trade on future data

        Returns True if trade was closed, False if no conclusion
        """

        if len(future_data) == 0:
            return False

        # Check each candle to see if SL or TP hit
        for idx, (timestamp, candle) in enumerate(future_data.iterrows()):
            if idx >= max_bars:
                # Timeout - close at current price
                trade.exit_price = candle['close']
                trade.exit_time = timestamp
                trade.outcome = TradeOutcome.TIMEOUT
                return True

            high = candle['high']
            low = candle['low']
            close = candle['close']

            if trade.direction == 'BUY':
                # Check if SL hit first (conservative)
                if low <= trade.stop_loss:
                    trade.exit_price = trade.stop_loss
                    trade.exit_time = timestamp
                    trade.outcome = TradeOutcome.SL_HIT
                    return True

                # Check if TP hit
                if high >= trade.take_profit:
                    trade.exit_price = trade.take_profit
                    trade.exit_time = timestamp
                    trade.outcome = TradeOutcome.TP_HIT
                    return True

            else:  # SELL
                # Check if SL hit first (conservative)
                if high >= trade.stop_loss:
                    trade.exit_price = trade.stop_loss
                    trade.exit_time = timestamp
                    trade.outcome = TradeOutcome.SL_HIT
                    return True

                # Check if TP hit
                if low <= trade.take_profit:
                    trade.exit_price = trade.take_profit
                    trade.exit_time = timestamp
                    trade.outcome = TradeOutcome.TP_HIT
                    return True

        return False

    def compare_strategies(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        strategies: Dict[str, callable]
    ) -> Dict[str, BacktestResults]:
        """
        Compare multiple strategies on same data

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            data: Historical data
            strategies: Dict of {strategy_name: strategy_function}

        Returns:
            Dict of {strategy_name: BacktestResults}
        """

        results = {}

        for name, strategy_func in strategies.items():
            print(f"\n[Backtest] Testing strategy: {name}")
            result = self.run_backtest(symbol, timeframe, data, strategy_func)
            result.strategy_name = name
            results[name] = result

        return results


# Global instance
backtest_engine = BacktestEngine()
