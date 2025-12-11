"""
AppleTrader Pro - ML Feature Engineering
Calculates 30+ technical indicators for machine learning

Features include:
- Trend: EMAs, MACD, ADX
- Momentum: RSI, Stochastic, CCI, Williams %R
- Volatility: ATR, Bollinger Bands
- Volume: OBV, Volume ratios
- Price Action: Candle patterns, support/resistance
- Market Structure: Swing highs/lows, trend strength
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class MLFeatures:
    """Container for ML features"""
    # Trend features
    ema_20: float
    ema_50: float
    ema_200: float
    ema_slope_20: float
    ema_alignment: int  # 1=bullish, -1=bearish, 0=neutral
    macd: float
    macd_signal: float
    macd_histogram: float
    adx: float

    # Momentum features
    rsi_14: float
    rsi_slope: float
    stoch_k: float
    stoch_d: float
    cci: float
    williams_r: float
    momentum_10: float

    # Volatility features
    atr_14: float
    atr_ratio: float  # Current ATR / Average ATR
    bb_upper: float
    bb_lower: float
    bb_width: float
    bb_position: float  # Where price is in BB (0-1)

    # Volume features
    volume_ratio: float  # Current / Average
    volume_trend: float  # Volume slope
    obv: float
    obv_slope: float

    # Price action features
    candle_size: float
    upper_wick_ratio: float
    lower_wick_ratio: float
    body_ratio: float
    is_engulfing: int
    is_pin_bar: int
    is_inside_bar: int

    # Market structure
    distance_to_high_20: float  # % from 20-bar high
    distance_to_low_20: float   # % from 20-bar low
    swing_strength: float
    trend_strength: float

    # Target variable (for training)
    future_return: float = 0.0  # Next N bars return
    is_winner: int = 0  # 1=profitable trade, 0=losing trade


class FeatureEngineer:
    """
    Calculates all technical indicators for ML
    """

    def __init__(self):
        pass

    def calculate_features(self, df: pd.DataFrame, index: int = -1) -> MLFeatures:
        """
        Calculate all features for a single point in time

        Args:
            df: OHLCV DataFrame
            index: Index to calculate features for (-1 = most recent)

        Returns:
            MLFeatures object with all indicators
        """

        if len(df) < 200:
            raise ValueError("Need at least 200 candles for feature calculation")

        # Slice data up to index
        data = df.iloc[:index+1] if index != -1 else df

        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        open_price = data['open'].values
        volume = data['volume'].values if 'volume' in data.columns else data.get('tick_volume', np.ones(len(data))).values

        # === TREND FEATURES ===
        ema_20 = self._ema(close, 20)
        ema_50 = self._ema(close, 50)
        ema_200 = self._ema(close, 200) if len(close) >= 200 else ema_50

        # EMA slope (rate of change)
        ema_slope_20 = (ema_20 - self._ema(close[:-5], 20)) / self._ema(close[:-5], 20) if len(close) > 5 else 0

        # EMA alignment (bullish when 20 > 50 > 200)
        if ema_20 > ema_50 > ema_200:
            ema_alignment = 1
        elif ema_20 < ema_50 < ema_200:
            ema_alignment = -1
        else:
            ema_alignment = 0

        # MACD
        macd, macd_signal, macd_histogram = self._macd(close)

        # ADX (trend strength)
        adx = self._adx(high, low, close, 14)

        # === MOMENTUM FEATURES ===
        rsi_14 = self._rsi(close, 14)
        rsi_slope = rsi_14 - self._rsi(close[:-5], 14) if len(close) > 5 else 0

        stoch_k, stoch_d = self._stochastic(high, low, close, 14, 3)

        cci = self._cci(high, low, close, 20)

        williams_r = self._williams_r(high, low, close, 14)

        momentum_10 = ((close[-1] - close[-10]) / close[-10]) * 100 if len(close) >= 10 else 0

        # === VOLATILITY FEATURES ===
        atr_14 = self._atr(high, low, close, 14)
        atr_avg = np.mean([self._atr(high[-i:], low[-i:], close[-i:], 14) for i in range(50, 60)]) if len(close) >= 60 else atr_14
        atr_ratio = atr_14 / atr_avg if atr_avg > 0 else 1.0

        # Bollinger Bands
        bb_middle = np.mean(close[-20:])
        bb_std = np.std(close[-20:])
        bb_upper = bb_middle + (2 * bb_std)
        bb_lower = bb_middle - (2 * bb_std)
        bb_width = (bb_upper - bb_lower) / bb_middle
        bb_position = (close[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5

        # === VOLUME FEATURES ===
        volume_avg = np.mean(volume[-20:])
        volume_ratio = volume[-1] / volume_avg if volume_avg > 0 else 1.0

        volume_slope = (volume[-1] - np.mean(volume[-10:-1])) / np.mean(volume[-10:-1]) if len(volume) >= 10 else 0

        obv = self._obv(close, volume)
        obv_slope = (obv - self._obv(close[:-5], volume[:-5])) / abs(self._obv(close[:-5], volume[:-5])) if len(close) > 5 else 0

        # === PRICE ACTION FEATURES ===
        current_close = close[-1]
        current_open = open_price[-1]
        current_high = high[-1]
        current_low = low[-1]
        prev_close = close[-2]
        prev_open = open_price[-2]

        candle_size = abs(current_close - current_open)
        candle_range = current_high - current_low
        upper_wick = current_high - max(current_open, current_close)
        lower_wick = min(current_open, current_close) - current_low

        upper_wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
        lower_wick_ratio = lower_wick / candle_range if candle_range > 0 else 0
        body_ratio = candle_size / candle_range if candle_range > 0 else 0

        # Pattern detection
        is_engulfing = 1 if (
            (current_close > current_open and prev_close < prev_open and
             current_close > prev_open and current_open < prev_close) or
            (current_close < current_open and prev_close > prev_open and
             current_close < prev_open and current_open > prev_close)
        ) else 0

        is_pin_bar = 1 if (lower_wick_ratio > 0.6 or upper_wick_ratio > 0.6) and body_ratio < 0.3 else 0

        is_inside_bar = 1 if current_high < high[-2] and current_low > low[-2] else 0

        # === MARKET STRUCTURE ===
        high_20 = np.max(high[-20:])
        low_20 = np.min(low[-20:])
        distance_to_high_20 = ((high_20 - current_close) / current_close) * 100
        distance_to_low_20 = ((current_close - low_20) / current_close) * 100

        # Swing strength (how many bars since last swing high/low)
        swing_strength = self._swing_strength(high, low, 5)

        # Trend strength (combination of EMA alignment and ADX)
        trend_strength = (abs(ema_alignment) * adx) / 100

        return MLFeatures(
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            ema_slope_20=ema_slope_20,
            ema_alignment=ema_alignment,
            macd=macd,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            adx=adx,
            rsi_14=rsi_14,
            rsi_slope=rsi_slope,
            stoch_k=stoch_k,
            stoch_d=stoch_d,
            cci=cci,
            williams_r=williams_r,
            momentum_10=momentum_10,
            atr_14=atr_14,
            atr_ratio=atr_ratio,
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            bb_width=bb_width,
            bb_position=bb_position,
            volume_ratio=volume_ratio,
            volume_trend=volume_slope,
            obv=obv,
            obv_slope=obv_slope,
            candle_size=candle_size,
            upper_wick_ratio=upper_wick_ratio,
            lower_wick_ratio=lower_wick_ratio,
            body_ratio=body_ratio,
            is_engulfing=is_engulfing,
            is_pin_bar=is_pin_bar,
            is_inside_bar=is_inside_bar,
            distance_to_high_20=distance_to_high_20,
            distance_to_low_20=distance_to_low_20,
            swing_strength=swing_strength,
            trend_strength=trend_strength
        )

    # === INDICATOR CALCULATION METHODS ===

    def _ema(self, data: np.ndarray, period: int) -> float:
        """Calculate EMA"""
        return pd.Series(data).ewm(span=period, adjust=False).mean().iloc[-1]

    def _rsi(self, close: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        delta = pd.Series(close).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def _macd(self, close: np.ndarray) -> tuple:
        """Calculate MACD"""
        ema_12 = pd.Series(close).ewm(span=12, adjust=False).mean()
        ema_26 = pd.Series(close).ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd.iloc[-1], signal.iloc[-1], histogram.iloc[-1]

    def _atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate ATR"""
        tr = []
        for i in range(1, len(close)):
            tr_value = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            tr.append(tr_value)
        return np.mean(tr[-period:])

    def _adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate ADX (simplified)"""
        # Simplified ADX calculation
        atr = self._atr(high, low, close, period)

        plus_dm = []
        minus_dm = []
        for i in range(1, len(high)):
            high_diff = high[i] - high[i-1]
            low_diff = low[i-1] - low[i]

            plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
            minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)

        plus_di = (np.mean(plus_dm[-period:]) / atr) * 100 if atr > 0 else 0
        minus_di = (np.mean(minus_dm[-period:]) / atr) * 100 if atr > 0 else 0

        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        return dx

    def _stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> tuple:
        """Calculate Stochastic Oscillator"""
        high_k = np.max(high[-k_period:])
        low_k = np.min(low[-k_period:])
        k = ((close[-1] - low_k) / (high_k - low_k)) * 100 if high_k != low_k else 50

        # D is SMA of K (simplified to just K for now)
        d = k

        return k, d

    def _cci(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> float:
        """Calculate Commodity Channel Index"""
        tp = (high[-period:] + low[-period:] + close[-period:]) / 3
        sma_tp = np.mean(tp)
        mad = np.mean(np.abs(tp - sma_tp))
        cci = (tp[-1] - sma_tp) / (0.015 * mad) if mad > 0 else 0
        return cci

    def _williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Williams %R"""
        high_n = np.max(high[-period:])
        low_n = np.min(low[-period:])
        wr = ((high_n - close[-1]) / (high_n - low_n)) * -100 if high_n != low_n else -50
        return wr

    def _obv(self, close: np.ndarray, volume: np.ndarray) -> float:
        """Calculate On-Balance Volume"""
        obv = 0
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv += volume[i]
            elif close[i] < close[i-1]:
                obv -= volume[i]
        return obv

    def _swing_strength(self, high: np.ndarray, low: np.ndarray, lookback: int = 5) -> float:
        """Calculate swing strength"""
        # Count bars since last swing high or low
        is_swing_high = high[-lookback] == np.max(high[-lookback*2:])
        is_swing_low = low[-lookback] == np.min(low[-lookback*2:])

        return 1.0 if is_swing_high or is_swing_low else 0.0


# Global instance
feature_engineer = FeatureEngineer()
