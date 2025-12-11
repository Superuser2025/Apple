"""
AppleTrader Pro - Strategy Adapter
Adapts opportunity scanner logic for backtesting

This allows you to backtest the SAME logic that the live scanner uses
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np


class StrategyAdapter:
    """
    Adapts live trading strategy for backtesting
    """

    def __init__(self, min_quality_score: int = 70):
        self.min_quality_score = min_quality_score

    def evaluate(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Evaluate trading opportunity on historical data

        This is the SAME logic as opportunity_scanner.analyze_opportunity()
        adapted for backtesting

        Args:
            df: Historical OHLC data up to current point

        Returns:
            Signal dict or None
        """

        try:
            if len(df) < 100:
                return None

            # === CALCULATE INDICATORS ===
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            open_price = df['open'].values

            current_close = close[-1]
            current_high = high[-1]
            current_low = low[-1]
            current_open = open_price[-1]
            prev_close = close[-2]
            prev_open = open_price[-2]
            prev_high = high[-2]
            prev_low = low[-2]

            # Calculate EMAs
            ema_20 = pd.Series(close).ewm(span=20, adjust=False).mean().iloc[-1]
            ema_50 = pd.Series(close).ewm(span=50, adjust=False).mean().iloc[-1]
            ema_200 = pd.Series(close).ewm(span=200, adjust=False).mean().iloc[-1] if len(close) >= 200 else ema_50

            # Calculate ATR
            tr = []
            for i in range(1, len(df)):
                tr_value = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr.append(tr_value)
            atr = np.mean(tr[-14:]) if len(tr) >= 14 else (high[-1] - low[-1])

            # Calculate RSI
            delta = pd.Series(close).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50

            # === DETECT PATTERNS ===
            pattern_detected = None
            pattern_direction = None
            quality_score = 50
            reasons = []

            # Bullish Engulfing
            if (current_close > current_open and
                prev_close < prev_open and
                current_close > prev_open and
                current_open < prev_close):
                pattern_detected = "Bullish Engulfing"
                pattern_direction = "BUY"
                quality_score += 15
                reasons.append("Bullish Engulfing")

            # Bearish Engulfing
            elif (current_close < current_open and
                  prev_close > prev_open and
                  current_close < prev_open and
                  current_open > prev_close):
                pattern_detected = "Bearish Engulfing"
                pattern_direction = "SELL"
                quality_score += 15
                reasons.append("Bearish Engulfing")

            # Bullish Pin Bar
            elif (current_close > current_open and
                  (current_low - min(current_open, current_close)) > 2 * abs(current_close - current_open) and
                  (current_high - max(current_open, current_close)) < 0.5 * abs(current_close - current_open)):
                pattern_detected = "Bullish Pin Bar"
                pattern_direction = "BUY"
                quality_score += 12
                reasons.append("Bullish Pin Bar")

            # Bearish Pin Bar
            elif (current_close < current_open and
                  (max(current_open, current_close) - current_high) < 0.5 * abs(current_close - current_open) and
                  (min(current_open, current_close) - current_low) > 2 * abs(current_close - current_open)):
                pattern_detected = "Bearish Pin Bar"
                pattern_direction = "SELL"
                quality_score += 12
                reasons.append("Bearish Pin Bar")

            # Trend continuation
            else:
                if current_close > ema_20 and ema_20 > ema_50:
                    pattern_direction = "BUY"
                    pattern_detected = "Trend Continuation"
                    quality_score += 5
                elif current_close < ema_20 and ema_20 < ema_50:
                    pattern_direction = "SELL"
                    pattern_detected = "Trend Continuation"
                    quality_score += 5
                else:
                    return None

            # === VALIDATE TREND ALIGNMENT ===
            if pattern_direction == "BUY":
                if current_close > ema_20 > ema_50 > ema_200:
                    quality_score += 20
                    reasons.append("Strong Uptrend")
                elif current_close > ema_20 > ema_50:
                    quality_score += 12
                    reasons.append("Uptrend Aligned")
                else:
                    quality_score -= 10

            elif pattern_direction == "SELL":
                if current_close < ema_20 < ema_50 < ema_200:
                    quality_score += 20
                    reasons.append("Strong Downtrend")
                elif current_close < ema_20 < ema_50:
                    quality_score += 12
                    reasons.append("Downtrend Aligned")
                else:
                    quality_score -= 10

            # === VALIDATE RSI ===
            if pattern_direction == "BUY" and 30 < current_rsi < 70:
                quality_score += 10
                reasons.append("RSI Favorable")
            elif pattern_direction == "SELL" and 30 < current_rsi < 70:
                quality_score += 10
                reasons.append("RSI Favorable")

            # === CHECK VOLUME ===
            if 'volume' in df.columns or 'tick_volume' in df.columns:
                vol_col = 'volume' if 'volume' in df.columns else 'tick_volume'
                avg_volume = df[vol_col].tail(20).mean()
                current_volume = df[vol_col].iloc[-1]

                if current_volume > avg_volume * 1.8:
                    quality_score += 15
                    reasons.append("High Volume")
                elif current_volume > avg_volume * 1.3:
                    quality_score += 8
                    reasons.append("Above Avg Volume")

            # === QUALITY THRESHOLD ===
            if quality_score < self.min_quality_score:
                return None

            # === CALCULATE ENTRY, SL, TP ===
            if pattern_direction == "BUY":
                entry = current_close
                stop_loss = current_low - (atr * 0.5)
                take_profit = entry + (atr * 2.5)
            else:
                entry = current_close
                stop_loss = current_high + (atr * 0.5)
                take_profit = entry - (atr * 2.5)

            return {
                'direction': pattern_direction,
                'entry': float(entry),
                'sl': float(stop_loss),
                'tp': float(take_profit),
                'score': quality_score,
                'reasons': reasons
            }

        except Exception as e:
            return None


# Create instances with different quality thresholds for testing
strategy_quality_70 = StrategyAdapter(min_quality_score=70)
strategy_quality_75 = StrategyAdapter(min_quality_score=75)
strategy_quality_80 = StrategyAdapter(min_quality_score=80)
