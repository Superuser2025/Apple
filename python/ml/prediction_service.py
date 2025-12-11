"""
AppleTrader Pro - ML Prediction Service
Uses trained ML model to score trade opportunities in real-time
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass

from ml.feature_engineering import feature_engineer
from ml.model_trainer import ml_trainer


@dataclass
class MLPrediction:
    """ML prediction result"""
    probability_win: float  # 0.0-1.0 probability of winning trade
    probability_loss: float  # 0.0-1.0 probability of losing trade
    confidence: float  # Max probability (measure of certainty)
    prediction: int  # 1=win, 0=loss
    signal: str  # 'STRONG_BUY', 'BUY', 'NEUTRAL', 'AVOID'


class MLPredictionService:
    """
    Real-time ML prediction service

    Calculates features for new opportunities and predicts profitability
    """

    def __init__(self):
        self.model_loaded = False
        self.prediction_count = 0

    def load_model(self, model_path: str) -> bool:
        """Load trained ML model"""
        try:
            ml_trainer.load_model(model_path)
            self.model_loaded = True
            print(f"[ML Service] ✓ Model loaded and ready")
            return True
        except Exception as e:
            print(f"[ML Service] ❌ Failed to load model: {e}")
            return False

    def predict_trade(self, df: pd.DataFrame) -> Optional[MLPrediction]:
        """
        Predict profitability of trade opportunity

        Args:
            df: Historical OHLCV data leading up to trade

        Returns:
            MLPrediction or None if model not loaded
        """

        if not self.model_loaded:
            return None

        try:
            # Calculate features
            features = feature_engineer.calculate_features(df, index=-1)

            # Convert to DataFrame
            feature_dict = {
                'ema_20': [features.ema_20],
                'ema_50': [features.ema_50],
                'ema_200': [features.ema_200],
                'ema_slope_20': [features.ema_slope_20],
                'ema_alignment': [features.ema_alignment],
                'macd': [features.macd],
                'macd_signal': [features.macd_signal],
                'macd_histogram': [features.macd_histogram],
                'adx': [features.adx],
                'rsi_14': [features.rsi_14],
                'rsi_slope': [features.rsi_slope],
                'stoch_k': [features.stoch_k],
                'stoch_d': [features.stoch_d],
                'cci': [features.cci],
                'williams_r': [features.williams_r],
                'momentum_10': [features.momentum_10],
                'atr_14': [features.atr_14],
                'atr_ratio': [features.atr_ratio],
                'bb_width': [features.bb_width],
                'bb_position': [features.bb_position],
                'volume_ratio': [features.volume_ratio],
                'volume_trend': [features.volume_trend],
                'obv_slope': [features.obv_slope],
                'candle_size': [features.candle_size],
                'upper_wick_ratio': [features.upper_wick_ratio],
                'lower_wick_ratio': [features.lower_wick_ratio],
                'body_ratio': [features.body_ratio],
                'is_engulfing': [features.is_engulfing],
                'is_pin_bar': [features.is_pin_bar],
                'is_inside_bar': [features.is_inside_bar],
                'distance_to_high_20': [features.distance_to_high_20],
                'distance_to_low_20': [features.distance_to_low_20],
                'swing_strength': [features.swing_strength],
                'trend_strength': [features.trend_strength],
            }

            X = pd.DataFrame(feature_dict)

            # Get prediction
            predictions, probabilities = ml_trainer.predict(X)

            prob_loss = probabilities[0][0]
            prob_win = probabilities[0][1]
            prediction = predictions[0]
            confidence = max(prob_win, prob_loss)

            # Determine signal strength
            if prob_win >= 0.75:
                signal = 'STRONG_BUY'
            elif prob_win >= 0.60:
                signal = 'BUY'
            elif prob_win >= 0.45:
                signal = 'NEUTRAL'
            else:
                signal = 'AVOID'

            self.prediction_count += 1

            return MLPrediction(
                probability_win=prob_win,
                probability_loss=prob_loss,
                confidence=confidence,
                prediction=prediction,
                signal=signal
            )

        except Exception as e:
            print(f"[ML Service] Error predicting trade: {e}")
            return None

    def batch_predict(self, opportunities: list, mt5_connector) -> Dict[str, MLPrediction]:
        """
        Predict multiple opportunities

        Args:
            opportunities: List of opportunity dicts
            mt5_connector: MT5 connector to fetch data

        Returns:
            Dict of {symbol: MLPrediction}
        """

        predictions = {}

        for opp in opportunities:
            symbol = opp['symbol']
            timeframe = opp['timeframe']

            # Get historical data
            df = mt5_connector.get_candles(symbol, timeframe, 200)

            if df is None or len(df) < 200:
                continue

            # Predict
            prediction = self.predict_trade(df)

            if prediction:
                predictions[symbol] = prediction

        return predictions

    def get_stats(self) -> Dict:
        """Get prediction service stats"""
        return {
            'model_loaded': self.model_loaded,
            'predictions_made': self.prediction_count,
            'feature_count': len(ml_trainer.feature_names) if self.model_loaded else 0
        }


# Global instance
ml_prediction_service = MLPredictionService()
